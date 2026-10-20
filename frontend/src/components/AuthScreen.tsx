import { useState, type FormEvent } from 'react';
import AlertBox from './AlertBox';
import PersonalFormFields from './PersonalFormFields';
import { ApiError, login, register, saveProfile } from '../services/api';
import type { Notice, PersonalFormValues, Session } from '../types/medinteract';
import { emptyPersonalForm, validatePersonalForm } from '../utils/profileForm';

interface AuthScreenProps {
  notice: Notice | null;
  onAuthenticated: (session: Session, notice?: Notice) => void;
}

// Verifica se o email possui '@' e '.com' após o '@'
function emailValido(email: string): boolean {
  const texto = email.trim().toLowerCase();
  const posArroba = texto.indexOf('@');
  const posCom = texto.indexOf('.com');
  return posArroba > 0 && posCom > posArroba + 1;
}

export default function AuthScreen({ notice, onAuthenticated }: AuthScreenProps) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [form, setForm] = useState<PersonalFormValues>(emptyPersonalForm);
  const [error, setError] = useState<Notice | null>(null);
  const [loading, setLoading] = useState(false);

  const updateForm = (campo: Partial<PersonalFormValues>) => {
    setForm((atual) => ({ ...atual, ...campo }));
  };

  const validarCampos = (): string | null => {
    if (!emailValido(email)) {
      return "Informe um e-mail válido contendo '@' e '.com'.";
    }
    if (password.length < 8) {
      return 'A senha deve ter no mínimo 8 caracteres.';
    }
    if (mode === 'register') {
      return validatePersonalForm(form);
    }
    return null;
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const erroValidacao = validarCampos();
    if (erroValidacao) {
      setError({ message: erroValidacao, alertType: 'warning' });
      return;
    }

    setLoading(true);
    setError(null);
    try {
      if (mode === 'login') {
        const res = await login(email.trim(), password);
        onAuthenticated({ idUsuario: res.idUsuario, token: res.token });
        return;
      }

      const res = await register({ apelido: form.apelido.trim(), email: email.trim(), password });
      const novaSessao: Session = { idUsuario: res.idUsuario, token: res.token };
      try {
        await saveProfile(novaSessao, form);
        onAuthenticated(novaSessao);
      } catch {
        onAuthenticated(novaSessao, {
          message: 'Conta criada. Complete seus dados no botão "Informações pessoais".',
          alertType: 'warning',
        });
      }
    } catch (err) {
      const apiErr = err instanceof ApiError ? err : null;
      setError({
        message: apiErr?.message ?? 'Erro ao autenticar usuário.',
        alertType: apiErr?.alertType ?? 'danger',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="auth-brand">
          <h1>MedInteract</h1>
        </div>
        <p className="auth-subtitle">Consulta de bulas e interações medicamentosas.</p>

        <div className="auth-tabs">
          <button
            type="button"
            className={`auth-tab ${mode === 'login' ? 'active' : ''}`}
            onClick={() => {
              setMode('login');
              setError(null);
            }}
          >
            Entrar
          </button>
          <button
            type="button"
            className={`auth-tab ${mode === 'register' ? 'active' : ''}`}
            onClick={() => {
              setMode('register');
              setError(null);
            }}
          >
            Criar conta
          </button>
        </div>

        {(error || notice) && (
          <AlertBox type={(error ?? notice)!.alertType} message={(error ?? notice)!.message} />
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-section">
            {mode === 'register' && (
              <div className="field">
                <label htmlFor="auth-apelido">Nome ou apelido</label>
                <input
                  id="auth-apelido"
                  className="input"
                  maxLength={50}
                  value={form.apelido}
                  disabled={loading}
                  onChange={(e) => updateForm({ apelido: e.target.value })}
                />
              </div>
            )}
            <div className="field">
              <label htmlFor="auth-email">E-mail</label>
              <input
                id="auth-email"
                type="email"
                className="input"
                placeholder="usuario@exemplo.com"
                value={email}
                disabled={loading}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="auth-password">Senha</label>
              <input
                id="auth-password"
                type="password"
                className="input"
                minLength={8}
                value={password}
                disabled={loading}
                onChange={(e) => setPassword(e.target.value)}
              />
              <span className="field-hint">Obrigatório no mínimo 8 caracteres.</span>
            </div>
          </div>

          {mode === 'register' && (
            <div className="form-section">
              <h3>Informações pessoais</h3>
              <PersonalFormFields values={form} onChange={updateForm} disabled={loading} />
            </div>
          )}

          <div className="auth-actions">
            <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
              {loading ? 'Carregando...' : mode === 'login' ? 'Entrar' : 'Cadastrar'}
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}

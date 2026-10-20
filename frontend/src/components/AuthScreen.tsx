import { useState, type FormEvent } from 'react';
import AlertBox from './AlertBox';
import PersonalFormFields from './PersonalFormFields';
import ThemeToggle from './ThemeToggle';
import { ApiError, login, register, saveProfile } from '../services/api';
import type { Notice, PersonalFormValues, Session, Theme } from '../types/medinteract';
import { emptyPersonalForm, validatePersonalForm } from '../utils/profileForm';

interface AuthScreenProps {
  theme: Theme;
  onToggleTheme: () => void;
  notice: Notice | null;
  onAuthenticated: (session: Session, notice?: Notice) => void;
}

type Mode = 'login' | 'register';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// tela (deslogada): login e cadastro com informações pessoais
export default function AuthScreen({ theme, onToggleTheme, notice, onAuthenticated }: AuthScreenProps) {
  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [form, setForm] = useState<PersonalFormValues>(emptyPersonalForm);
  const [error, setError] = useState<Notice | null>(null);
  const [loading, setLoading] = useState(false);

  const patchForm = (patch: Partial<PersonalFormValues>) => setForm((prev) => ({ ...prev, ...patch }));

  const switchMode = (next: Mode) => {
    setMode(next);
    setError(null);
  };

  const validate = (): string | null => {
    if (!EMAIL_PATTERN.test(email.trim())) return 'Informe um e-mail válido.';
    if (mode === 'login') return password ? null : 'Informe sua senha.';
    if (password.length < 6) return 'A senha deve ter pelo menos 6 caracteres.';
    return validatePersonalForm(form);
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const problem = validate();
    if (problem) {
      setError({ message: problem, alertType: 'warning' });
      return;
    }

    setLoading(true);
    setError(null);
    try {
      if (mode === 'login') {
        const result = await login(email.trim(), password);
        onAuthenticated({ idUsuario: result.idUsuario, token: result.token });
        return;
      }

      const result = await register({ apelido: form.apelido.trim(), email: email.trim(), password });
      const session: Session = { idUsuario: result.idUsuario, token: result.token };
      try {
        await saveProfile(session, form);
        onAuthenticated(session);
      } catch {
        onAuthenticated(session, {
          message: 'Conta criada, mas não foi possível salvar suas informações pessoais. Preencha-as em "Informações pessoais".',
          alertType: 'warning',
        });
      }
    } catch (err) {
      const apiError = err instanceof ApiError ? err : null;
      setError({
        message: apiError?.message ?? 'Erro inesperado. Tente novamente.',
        alertType: apiError?.alertType ?? 'danger',
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
          <ThemeToggle theme={theme} onToggle={onToggleTheme} />
        </div>
        <p className="auth-subtitle">Consultas sobre medicamentos e interações, baseadas em bulas oficiais.</p>

        <div className="auth-tabs" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'login'}
            className={`auth-tab ${mode === 'login' ? 'active' : ''}`}
            onClick={() => switchMode('login')}
          >
            Entrar
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'register'}
            className={`auth-tab ${mode === 'register' ? 'active' : ''}`}
            onClick={() => switchMode('register')}
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
                <label htmlFor="auth-apelido">Apelido</label>
                <input
                  id="auth-apelido"
                  className="input"
                  autoComplete="nickname"
                  maxLength={50}
                  value={form.apelido}
                  disabled={loading}
                  onChange={(e) => patchForm({ apelido: e.target.value })}
                />
              </div>
            )}
            <div className="field">
              <label htmlFor="auth-email">E-mail</label>
              <input
                id="auth-email"
                type="email"
                className="input"
                autoComplete="email"
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
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                value={password}
                disabled={loading}
                onChange={(e) => setPassword(e.target.value)}
              />
              {mode === 'register' && <span className="field-hint">Mínimo de 6 caracteres.</span>}
            </div>
          </div>

          {mode === 'register' && (
            <div className="form-section">
              <h3>Informações pessoais</h3>
              <span className="field-hint">Opcionais. Ajudam a IA a personalizar as respostas e ficam guardadas no servidor.</span>
              <PersonalFormFields values={form} onChange={patchForm} disabled={loading} />
            </div>
          )}

          <div className="auth-actions">
            <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
              {loading ? 'Aguarde...' : mode === 'login' ? 'Entrar' : 'Criar conta'}
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}

import { useState } from 'react';
import AlertBox from './AlertBox';
import PersonalFormFields from './PersonalFormFields';
import { ApiError, saveProfile } from '../services/api';
import type { Notice, PersonalProfile, ProfileResponse, Session, UserAccount } from '../types/medinteract';
import { formFromProfile, validatePersonalForm } from '../utils/profileForm';
import type { PersonalFormValues } from '../types/medinteract';

interface PersonalInfoModalProps {
  session: Session;
  account: UserAccount | null;
  perfil: PersonalProfile | null;
  imc: number | null;
  onClose: () => void;
  onSaved: (data: ProfileResponse) => void;
}

// Modal para visualizar e editar as informações pessoais salvas no backend
export default function PersonalInfoModal({ session, account, perfil, imc, onClose, onSaved }: PersonalInfoModalProps) {
  const [form, setForm] = useState<PersonalFormValues>(() => formFromProfile(account?.apelido ?? '', perfil));
  const [currentImc, setCurrentImc] = useState<number | null>(imc);
  const [feedback, setFeedback] = useState<Notice | null>(null);
  const [saving, setSaving] = useState(false);

  const patchForm = (patch: Partial<PersonalFormValues>) => setForm((prev) => ({ ...prev, ...patch }));

  const handleSave = async () => {
    const problem = validatePersonalForm(form);
    if (problem) {
      setFeedback({ message: problem, alertType: 'warning' });
      return;
    }

    setSaving(true);
    setFeedback(null);
    try {
      const data = await saveProfile(session, form);
      setCurrentImc(data.imcCalculado);
      onSaved(data);
      setFeedback({ message: 'Informações pessoais salvas com sucesso.', alertType: 'info' });
    } catch (err) {
      const apiError = err instanceof ApiError ? err : null;
      setFeedback({
        message: apiError?.message ?? 'Não foi possível salvar as informações.',
        alertType: apiError?.alertType ?? 'danger',
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="personal-info-title">
        <div className="modal-header">
          <h2 id="personal-info-title">Informações pessoais</h2>
          <button type="button" className="btn" onClick={onClose} aria-label="Fechar">
            ×
          </button>
        </div>

        <div className="stack">
          {feedback && <AlertBox type={feedback.alertType} message={feedback.message} onClose={() => setFeedback(null)} />}

          <div className="field">
            <label htmlFor="pi-apelido">Apelido</label>
            <input
              id="pi-apelido"
              className="input"
              maxLength={50}
              value={form.apelido}
              disabled={saving}
              onChange={(e) => patchForm({ apelido: e.target.value })}
            />
          </div>
          <div className="field">
            <span className="field-label">E-mail</span>
            <div className="readonly-box">{account?.email ?? '—'}</div>
          </div>

          <PersonalFormFields values={form} onChange={patchForm} disabled={saving} />

          <div className="field">
            <span className="field-label">IMC (calculado pelo servidor)</span>
            <div className="readonly-box">{currentImc !== null ? currentImc.toFixed(1) : 'Informe peso e altura e salve'}</div>
          </div>
        </div>

        <div className="modal-footer">
          <button type="button" className="btn" onClick={onClose}>
            Fechar
          </button>
          <button type="button" className="btn btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? 'Salvando...' : 'Salvar alterações'}
          </button>
        </div>
      </div>
    </div>
  );
}

import type { PersonalFormValues } from '../types/medinteract';

interface PersonalFormFieldsProps {
  values: PersonalFormValues;
  onChange: (patch: Partial<PersonalFormValues>) => void;
  disabled?: boolean;
}

// Campos de informações pessoais compartilhados entre cadastro e modal de edição
export default function PersonalFormFields({ values, onChange, disabled }: PersonalFormFieldsProps) {
  return (
    <>
      <div className="form-grid">
        <div className="field">
          <label htmlFor="pf-idade">Idade</label>
          <input
            id="pf-idade"
            className="input"
            inputMode="numeric"
            placeholder="Ex.: 35"
            value={values.idade}
            disabled={disabled}
            onChange={(e) => onChange({ idade: e.target.value })}
          />
        </div>
        <div className="field">
          <label htmlFor="pf-peso">Peso (kg)</label>
          <input
            id="pf-peso"
            className="input"
            inputMode="decimal"
            placeholder="Ex.: 72,5"
            value={values.peso}
            disabled={disabled}
            onChange={(e) => onChange({ peso: e.target.value })}
          />
        </div>
        <div className="field">
          <label htmlFor="pf-altura">Altura (m)</label>
          <input
            id="pf-altura"
            className="input"
            inputMode="decimal"
            placeholder="Ex.: 1,75"
            value={values.altura}
            disabled={disabled}
            onChange={(e) => onChange({ altura: e.target.value })}
          />
        </div>
        <div className="field">
          <label htmlFor="pf-sono">Horas de sono</label>
          <input
            id="pf-sono"
            className="input"
            inputMode="decimal"
            placeholder="Ex.: 7,5"
            value={values.horasSono}
            disabled={disabled}
            onChange={(e) => onChange({ horasSono: e.target.value })}
          />
        </div>
      </div>

      <label className="check-row">
        <input
          type="checkbox"
          checked={values.gestanteLactante}
          disabled={disabled}
          onChange={(e) => onChange({ gestanteLactante: e.target.checked })}
        />
        Gestante ou lactante
      </label>

      <div className="field">
        <label htmlFor="pf-alergias">Alergias</label>
        <textarea
          id="pf-alergias"
          className="input"
          placeholder="Ex.: dipirona, penicilina"
          value={values.alergias}
          disabled={disabled}
          onChange={(e) => onChange({ alergias: e.target.value })}
        />
      </div>
      <div className="field">
        <label htmlFor="pf-saude">Problemas de saúde</label>
        <textarea
          id="pf-saude"
          className="input"
          placeholder="Ex.: hipertensão, diabetes"
          value={values.problemasSaude}
          disabled={disabled}
          onChange={(e) => onChange({ problemasSaude: e.target.value })}
        />
      </div>
      <div className="field">
        <label htmlFor="pf-meds">Medicações contínuas</label>
        <textarea
          id="pf-meds"
          className="input"
          placeholder="Ex.: losartana 50 mg"
          value={values.medicacoesContinuas}
          disabled={disabled}
          onChange={(e) => onChange({ medicacoesContinuas: e.target.value })}
        />
      </div>
      <div className="field">
        <label htmlFor="pf-esportes">Prática de esportes</label>
        <textarea
          id="pf-esportes"
          className="input"
          placeholder="Ex.: corrida 3x por semana"
          value={values.praticaEsportes}
          disabled={disabled}
          onChange={(e) => onChange({ praticaEsportes: e.target.value })}
        />
      </div>
    </>
  );
}

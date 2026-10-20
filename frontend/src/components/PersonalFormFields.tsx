import type { KeyboardEvent } from 'react';
import type { PersonalFormValues } from '../types/medinteract';

interface PersonalFormFieldsProps {
  values: PersonalFormValues;
  onChange: (patch: Partial<PersonalFormValues>) => void;
  disabled?: boolean;
}

// Bloqueia digitação de sinal negativo nos campos numéricos
function bloquearSinalNegativo(e: KeyboardEvent<HTMLInputElement>) {
  if (e.key === '-' || e.key === '+' || e.key === 'e' || e.key === 'E') {
    e.preventDefault();
  }
}

function semNegativo(valor: string): string {
  return valor.replace(/-/g, '');
}

export default function PersonalFormFields({ values, onChange, disabled }: PersonalFormFieldsProps) {
  return (
    <>
      <div className="form-grid">
        <div className="field">
          <label htmlFor="pf-idade">Idade</label>
          <input
            id="pf-idade"
            type="number"
            min={0}
            max={130}
            step={1}
            className="input"
            placeholder="Ex.: 35"
            value={values.idade}
            disabled={disabled}
            onKeyDown={bloquearSinalNegativo}
            onChange={(e) => onChange({ idade: semNegativo(e.target.value) })}
          />
        </div>
        <div className="field">
          <label htmlFor="pf-peso">Peso (kg)</label>
          <input
            id="pf-peso"
            type="number"
            min={0}
            max={500}
            step="0.1"
            className="input"
            placeholder="Ex.: 72.5"
            value={values.peso}
            disabled={disabled}
            onKeyDown={bloquearSinalNegativo}
            onChange={(e) => onChange({ peso: semNegativo(e.target.value) })}
          />
        </div>
        <div className="field">
          <label htmlFor="pf-altura">Altura (m)</label>
          <input
            id="pf-altura"
            type="number"
            min={0}
            max={2.5}
            step="0.01"
            className="input"
            placeholder="Ex.: 1.75"
            value={values.altura}
            disabled={disabled}
            onKeyDown={bloquearSinalNegativo}
            onChange={(e) => onChange({ altura: semNegativo(e.target.value) })}
          />
        </div>
        <div className="field">
          <label htmlFor="pf-sono">Horas de sono</label>
          <input
            id="pf-sono"
            type="number"
            min={0}
            max={24}
            step="0.5"
            className="input"
            placeholder="Ex.: 7.5"
            value={values.horasSono}
            disabled={disabled}
            onKeyDown={bloquearSinalNegativo}
            onChange={(e) => onChange({ horasSono: semNegativo(e.target.value) })}
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

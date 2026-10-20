import { useState } from 'react';
import AlertBox from './AlertBox';
import { calculatePediatricDose, calculateRenalClearance } from '../services/api';
import type { Notice, PediatricDoseResponse, RenalClearanceResponse } from '../types/medinteract';

interface CalculatorsModalProps {
  onClose: () => void;
}

type TabType = 'pediatric' | 'renal';

export default function CalculatorsModal({ onClose }: CalculatorsModalProps) {
  const [activeTab, setActiveTab] = useState<TabType>('pediatric');
  const [notice, setNotice] = useState<Notice | null>(null);
  const [loading, setLoading] = useState(false);

  // Estados Dose Pediátrica
  const [pedWeight, setPedWeight] = useState('');
  const [pedDosePerKg, setPedDosePerKg] = useState('');
  const [pedResult, setPedResult] = useState<PediatricDoseResponse | null>(null);

  // Estados Clearance Renal
  const [renalAge, setRenalAge] = useState('');
  const [renalWeight, setRenalWeight] = useState('');
  const [renalCreatinine, setRenalCreatinine] = useState('');
  const [renalSex, setRenalSex] = useState<'M' | 'F'>('M');
  const [renalResult, setRenalResult] = useState<RenalClearanceResponse | null>(null);

  const handlePediatricSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const weight = parseFloat(pedWeight.replace(',', '.'));
    const dosePerKg = parseFloat(pedDosePerKg.replace(',', '.'));

    if (isNaN(weight) || weight <= 0 || isNaN(dosePerKg) || dosePerKg <= 0) {
      setNotice({ message: 'Informe valores válidos maiores que zero para peso e dose/kg.', alertType: 'warning' });
      return;
    }

    setLoading(true);
    setNotice(null);
    try {
      const res = await calculatePediatricDose(weight, dosePerKg);
      setPedResult(res);
    } catch {
      setNotice({ message: 'Não foi possível calcular a dose pediátrica.', alertType: 'danger' });
    } finally {
      setLoading(false);
    }
  };

  const handleRenalSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const age = parseInt(renalAge, 10);
    const weight = parseFloat(renalWeight.replace(',', '.'));
    const creatinine = parseFloat(renalCreatinine.replace(',', '.'));

    if (isNaN(age) || age <= 0 || isNaN(weight) || weight <= 0 || isNaN(creatinine) || creatinine <= 0) {
      setNotice({ message: 'Preencha idade, peso e creatinina com valores positivos.', alertType: 'warning' });
      return;
    }

    setLoading(true);
    setNotice(null);
    try {
      const res = await calculateRenalClearance(age, weight, creatinine, renalSex);
      setRenalResult(res);
    } catch {
      setNotice({ message: 'Não foi possível calcular o clearance renal.', alertType: 'danger' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="calc-modal-title">
        <div className="modal-header">
          <h2 id="calc-modal-title">Calculadoras Clínicas</h2>
          <button type="button" className="btn" onClick={onClose} aria-label="Fechar">
            ✕
          </button>
        </div>

        <div className="segmented" style={{ marginBottom: '16px' }}>
          <button
            type="button"
            aria-pressed={activeTab === 'pediatric'}
            onClick={() => {
              setActiveTab('pediatric');
              setNotice(null);
            }}
          >
            👶 Dose Pediátrica
          </button>
          <button
            type="button"
            aria-pressed={activeTab === 'renal'}
            onClick={() => {
              setActiveTab('renal');
              setNotice(null);
            }}
          >
            🩺 Clearance Renal (Cockcroft-Gault)
          </button>
        </div>

        {notice && (
          <div style={{ marginBottom: '12px' }}>
            <AlertBox type={notice.alertType} message={notice.message} onClose={() => setNotice(null)} />
          </div>
        )}

        {activeTab === 'pediatric' ? (
          <form onSubmit={handlePediatricSubmit} className="stack">
            <p className="field-hint" style={{ margin: 0 }}>
              Cálculo de dosagem total baseada no peso corporal infantil (mg/dose ou mg/dia).
            </p>

            <div className="form-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="field">
                <label htmlFor="ped-weight">Peso da Criança (kg)</label>
                <input
                  id="ped-weight"
                  type="number"
                  step="0.1"
                  min="0.5"
                  className="input"
                  placeholder="Ex: 14.5"
                  value={pedWeight}
                  onChange={(e) => setPedWeight(e.target.value)}
                  disabled={loading}
                />
              </div>

              <div className="field">
                <label htmlFor="ped-dose">Dose por kg (mg/kg)</label>
                <input
                  id="ped-dose"
                  type="number"
                  step="0.1"
                  min="0.1"
                  className="input"
                  placeholder="Ex: 10"
                  value={pedDosePerKg}
                  onChange={(e) => setPedDosePerKg(e.target.value)}
                  disabled={loading}
                />
              </div>
            </div>

            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Calculando...' : 'Calcular Dose'}
            </button>

            {pedResult && (
              <div className="readonly-box" style={{ marginTop: '8px', borderLeft: '4px solid var(--primary, #0ea5e9)' }}>
                <strong>Resultado:</strong>
                <p style={{ margin: '4px 0 0 0', fontSize: '1.05rem' }}>
                  Dose Recomendada: <strong>{pedResult.recommendedDose.toFixed(2)} {pedResult.unit}</strong>
                </p>
                <span className="field-hint">
                  ({pedResult.weight} kg × {pedResult.dosePerKg} mg/kg)
                </span>
              </div>
            )}
          </form>
        ) : (
          <form onSubmit={handleRenalSubmit} className="stack">
            <p className="field-hint" style={{ margin: 0 }}>
              Estimativa da Taxa de Filtração Glomerular para ajuste de dosagem em insuficiência renal.
            </p>

            <div className="form-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="field">
                <label htmlFor="renal-age">Idade (anos)</label>
                <input
                  id="renal-age"
                  type="number"
                  min="1"
                  max="120"
                  className="input"
                  placeholder="Ex: 65"
                  value={renalAge}
                  onChange={(e) => setRenalAge(e.target.value)}
                  disabled={loading}
                />
              </div>

              <div className="field">
                <label htmlFor="renal-weight">Peso (kg)</label>
                <input
                  id="renal-weight"
                  type="number"
                  step="0.1"
                  min="1"
                  className="input"
                  placeholder="Ex: 70"
                  value={renalWeight}
                  onChange={(e) => setRenalWeight(e.target.value)}
                  disabled={loading}
                />
              </div>

              <div className="field">
                <label htmlFor="renal-cr">Creatinina Sérica (mg/dL)</label>
                <input
                  id="renal-cr"
                  type="number"
                  step="0.01"
                  min="0.1"
                  className="input"
                  placeholder="Ex: 1.2"
                  value={renalCreatinine}
                  onChange={(e) => setRenalCreatinine(e.target.value)}
                  disabled={loading}
                />
              </div>

              <div className="field">
                <label htmlFor="renal-sex">Sexo Biológico</label>
                <select
                  id="renal-sex"
                  className="input"
                  value={renalSex}
                  onChange={(e) => setRenalSex(e.target.value as 'M' | 'F')}
                  disabled={loading}
                >
                  <option value="M">Masculino</option>
                  <option value="F">Feminino (fator 0.85)</option>
                </select>
              </div>
            </div>

            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Calculando...' : 'Calcular Clearance'}
            </button>

            {renalResult && (
              <div className="readonly-box" style={{ marginTop: '8px', borderLeft: '4px solid var(--primary, #0ea5e9)' }}>
                <strong>Resultado Clínico:</strong>
                <p style={{ margin: '4px 0 0 0', fontSize: '1.05rem' }}>
                  Clearance Estimado: <strong>{renalResult.renalClearanceMlMin.toFixed(1)} {renalResult.unit}</strong>
                </p>
                <p style={{ margin: '4px 0 0 0', color: 'var(--text-secondary)' }}>
                  Classificação: <strong>{renalResult.renalClassification}</strong>
                </p>
              </div>
            )}
          </form>
        )}

        <div className="modal-footer" style={{ marginTop: '16px' }}>
          <button type="button" className="btn" onClick={onClose}>
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}

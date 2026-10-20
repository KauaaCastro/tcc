import { useState } from 'react';

interface TermsModalProps {
  onAccept: () => void;
  onDecline: () => void;
}

// Modal obrigatório de termos de uso e consentimento de uso dos dados
export default function TermsModal({ onAccept, onDecline }: TermsModalProps) {
  const [agreed, setAgreed] = useState(false);

  return (
    <div className="modal-backdrop">
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="terms-title">
        <div className="modal-header">
          <h2 id="terms-title">Termos de uso e consentimento</h2>
        </div>

        <div className="stack">
          <p>
            O MedInteract usa as informações informadas no seu cadastro (idade, peso, altura, alergias, problemas de
            saúde, medicações contínuas, hábitos e demais dados pessoais) para auxiliar a IA na análise das suas
            consultas sobre bulas e interações medicamentosas.
          </p>
          <p>
            Esses dados são usados apenas para personalizar as respostas. As respostas da IA têm caráter informativo e
            não substituem a avaliação de um médico ou farmacêutico.
          </p>

          <label className="checkbox-row">
            <input type="checkbox" checked={agreed} onChange={(e) => setAgreed(e.target.checked)} />
            <span>Li e permito o uso dos meus dados para auxiliar na análise da IA.</span>
          </label>
        </div>

        <div className="modal-footer">
          <button type="button" className="btn" onClick={onDecline}>
            Não permito (sair)
          </button>
          <button type="button" className="btn btn-primary" disabled={!agreed} onClick={onAccept}>
            Continuar
          </button>
        </div>
      </div>
    </div>
  );
}

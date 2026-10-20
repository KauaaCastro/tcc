import type { ReactNode } from 'react';
import type { AlertType, OfficialLink } from '../types/medinteract';

const ICONS: Record<AlertType, string> = {
  danger: '⛔',
  warning: '⚠️',
  restriction: '🔒',
  info: 'ℹ️',
};

const DEFAULT_TITLES: Record<AlertType, string> = {
  danger: 'Atenção: risco grave',
  warning: 'Use com cautela',
  restriction: 'Serviço indisponível',
  info: 'Informação',
};

interface AlertBoxProps {
  type: AlertType;
  message: ReactNode;
  title?: string;
  links?: OfficialLink[];
  onClose?: () => void;
}

// Único componente de alerta do sistema (erros, avisos clínicos e fallback)
export default function AlertBox({ type, message, title, links, onClose }: AlertBoxProps) {
  const safeLinks = (links ?? []).filter((link) => /^https?:\/\//i.test(link.url));

  return (
    <div className={`alert alert-${type}`} role={type === 'info' ? 'status' : 'alert'}>
      <span className="alert-icon" aria-hidden="true">
        {ICONS[type]}
      </span>
      <div className="alert-body">
        <div className="alert-title">{title ?? DEFAULT_TITLES[type]}</div>
        <div className="alert-message">{message}</div>
        {safeLinks.length > 0 && (
          <div className="alert-links">
            {safeLinks.map((link) => (
              <a key={link.url} className="alert-link" href={link.url} target="_blank" rel="noopener noreferrer">
                {link.name}
              </a>
            ))}
          </div>
        )}
      </div>
      {onClose && (
        <button type="button" className="alert-close" onClick={onClose} aria-label="Fechar aviso">
          ×
        </button>
      )}
    </div>
  );
}

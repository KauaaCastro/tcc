import type { HistoryItem } from '../types/medinteract';
import { formatDateTime } from '../utils/format';

const MAX_ITEMS = 30;

interface HistorySidebarProps {
  items: HistoryItem[];
  selectedId: number | null;
  loading: boolean;
  onSelect: (item: HistoryItem) => void;
  onNew: () => void;
}

// Barra esquerda com as conversas recentes vindas do backend
export default function HistorySidebar({ items, selectedId, loading, onSelect, onNew }: HistorySidebarProps) {
  return (
    <aside className="sidebar" aria-label="Conversas recentes">
      <button type="button" className="btn btn-primary btn-block" onClick={onNew}>
        + Nova conversa
      </button>
      <h2>Conversas recentes</h2>
      {loading ? (
        <p className="sidebar-empty">Carregando...</p>
      ) : items.length === 0 ? (
        <p className="sidebar-empty">Suas conversas aparecerão aqui.</p>
      ) : (
        <ul className="history-list">
          {items.slice(0, MAX_ITEMS).map((item) => (
            <li key={item.idConsulta}>
              <button
                type="button"
                className={`history-item ${item.idConsulta === selectedId ? 'active' : ''}`}
                onClick={() => onSelect(item)}
                title={item.perguntaUsuario}
              >
                <span className="history-title">{item.perguntaUsuario}</span>
                <span className="history-date">{formatDateTime(item.dataHora)}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}

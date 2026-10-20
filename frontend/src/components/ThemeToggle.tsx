import type { Theme } from '../types/medinteract';

interface ThemeToggleProps {
  theme: Theme;
  onToggle: () => void;
}

export default function ThemeToggle({ theme, onToggle }: ThemeToggleProps) {
  const next = theme === 'light' ? 'escuro' : 'claro';
  return (
    <button type="button" className="btn" onClick={onToggle} title={`Mudar para modo ${next}`}>
      {theme === 'light' ? 'Escuro' : 'Claro'}
    </button>
  );
}

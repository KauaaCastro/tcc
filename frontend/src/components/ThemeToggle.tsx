import type { Theme } from '../types/medinteract';

interface ThemeToggleProps {
  theme: Theme;
  onToggle: () => void;
}

export default function ThemeToggle({ theme, onToggle }: ThemeToggleProps) {
  return (
    <button type="button" className="btn" onClick={onToggle}>
      {theme === 'light' ? 'Modo escuro' : 'Modo claro'}
    </button>
  );
}

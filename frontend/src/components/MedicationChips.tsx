import { useState, type KeyboardEvent } from 'react';

const MAX_CHIPS = 10;

interface MedicationChipsProps {
  value: string[];
  onChange: (next: string[]) => void;
  disabled?: boolean;
}

// Campo de medicamentos (Enter ou vírgula adiciona)
export default function MedicationChips({ value, onChange, disabled }: MedicationChipsProps) {
  const [draft, setDraft] = useState('');

  const addDraft = () => {
    const name = draft.trim().replace(/,+$/, '').trim();
    setDraft('');
    if (!name || value.length >= MAX_CHIPS) return;
    const exists = value.some((item) => item.toLowerCase() === name.toLowerCase());
    if (!exists) onChange([...value, name.slice(0, 60)]);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' || event.key === ',') {
      event.preventDefault();
      addDraft();
    } else if (event.key === 'Backspace' && !draft && value.length > 0) {
      onChange(value.slice(0, -1));
    }
  };

  return (
    <div className="chips">
      {value.map((name) => (
        <span className="chip" key={name}>
          {name}
          <button
            type="button"
            disabled={disabled}
            onClick={() => onChange(value.filter((item) => item !== name))}
            aria-label={`Remover ${name}`}
          >
            ×
          </button>
        </span>
      ))}
      <input
        value={draft}
        disabled={disabled || value.length >= MAX_CHIPS}
        placeholder={value.length === 0 ? 'Medicamentos (opcional): digite e tecle Enter' : 'Adicionar outro'}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={addDraft}
        aria-label="Adicionar medicamento"
      />
    </div>
  );
}

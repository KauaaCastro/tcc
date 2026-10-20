import type { PersonalFormValues, PersonalProfile } from '../types/medinteract';

export const emptyPersonalForm: PersonalFormValues = {
  apelido: '',
  idade: '',
  peso: '',
  altura: '',
  gestanteLactante: false,
  alergias: '',
  problemasSaude: '',
  medicacoesContinuas: '',
  praticaEsportes: '',
  horasSono: '',
};

function toText(value: number | string | null | undefined): string {
  return value === null || value === undefined ? '' : String(value);
}

// Converte "1,75" ou "1.75" em número; vazio ou inválido vira undefined
function parseNumber(value: string): number | undefined {
  const normalized = value.trim().replace(',', '.');
  if (!normalized) return undefined;
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : undefined;
}

export function formFromProfile(apelido: string, perfil: PersonalProfile | null): PersonalFormValues {
  return {
    apelido,
    idade: toText(perfil?.idade),
    peso: toText(perfil?.peso),
    altura: toText(perfil?.altura),
    gestanteLactante: Boolean(perfil?.gestanteLactante),
    alergias: toText(perfil?.alergias),
    problemasSaude: toText(perfil?.problemasSaude),
    medicacoesContinuas: toText(perfil?.medicacoesContinuas),
    praticaEsportes: toText(perfil?.praticaEsportes),
    horasSono: toText(perfil?.horasSono),
  };
}

// Monta o corpo enviado ao backend; campos numéricos vazios são omitidos
export function toProfilePayload(values: PersonalFormValues): Record<string, unknown> {
  const idade = parseNumber(values.idade);
  const payload: Record<string, unknown> = {
    apelido: values.apelido.trim(),
    gestanteLactante: values.gestanteLactante,
    alergias: values.alergias.trim(),
    problemasSaude: values.problemasSaude.trim(),
    medicacoesContinuas: values.medicacoesContinuas.trim(),
    praticaEsportes: values.praticaEsportes.trim(),
  };
  if (idade !== undefined) payload.idade = Math.round(idade);
  const peso = parseNumber(values.peso);
  if (peso !== undefined) payload.peso = peso;
  const altura = parseNumber(values.altura);
  if (altura !== undefined) payload.altura = altura;
  const horasSono = parseNumber(values.horasSono);
  if (horasSono !== undefined) payload.horasSono = horasSono;
  return payload;
}

// Valida só faixas de digitação; regras clínicas continuam no backend
export function validatePersonalForm(values: PersonalFormValues): string | null {
  if (!values.apelido.trim()) return 'Informe como deseja ser chamado (apelido).';

  const idade = parseNumber(values.idade);
  if (values.idade.trim() && (idade === undefined || idade < 0 || idade > 130)) {
    return 'A idade deve estar entre 0 e 130 anos.';
  }
  const peso = parseNumber(values.peso);
  if (values.peso.trim() && (peso === undefined || peso < 1 || peso > 500)) {
    return 'O peso deve estar entre 1 e 500 kg.';
  }
  const altura = parseNumber(values.altura);
  if (values.altura.trim() && (altura === undefined || altura < 0.3 || altura > 2.5)) {
    return 'A altura deve ser informada em metros (ex.: 1,75).';
  }
  const horasSono = parseNumber(values.horasSono);
  if (values.horasSono.trim() && (horasSono === undefined || horasSono < 0 || horasSono > 24)) {
    return 'As horas de sono devem estar entre 0 e 24.';
  }
  return null;
}

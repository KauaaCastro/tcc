// Tipos utilizados na comunicação entre o frontend e as APIs Java e Python

export type AlertType = 'danger' | 'warning' | 'restriction' | 'info';

export type ProfileType = 'PATIENT' | 'PROFESSIONAL';

export type Theme = 'light' | 'dark';

export interface OfficialLink {
  name: string;
  url: string;
}

export interface Session {
  idUsuario: string;
  token: string;
}

export interface UserAccount {
  idUsuario: string;
  apelido: string;
  email: string;
}

export interface PersonalProfile {
  idade: number | null;
  peso: number | null;
  altura: number | null;
  gestanteLactante: boolean | null;
  alergias: string | null;
  problemasSaude: string | null;
  medicacoesContinuas: string | null;
  praticaEsportes: string | null;
  horasSono: number | null;
}

export interface HistoryItem {
  idConsulta: number;
  perguntaUsuario: string;
  respostaIa: string;
  dataHora: string;
}

export interface AuthResponse {
  mensagem: string;
  idUsuario: string;
  token: string;
  usuario: UserAccount;
  perfil: PersonalProfile | null;
  imcCalculado?: number | null;
}

export interface ProfileResponse {
  usuario: UserAccount | null;
  perfil: PersonalProfile | null;
  imcCalculado: number | null;
  historico?: HistoryItem[];
}

export interface PersonalFormValues {
  apelido: string;
  idade: string;
  peso: string;
  altura: string;
  gestanteLactante: boolean;
  alergias: string;
  problemasSaude: string;
  medicacoesContinuas: string;
  praticaEsportes: string;
  horasSono: string;
}

export interface ChatRequest {
  idUsuario: string;
  question: string;
  profile: ProfileType;
  medications: string[];
}

export interface StreamChunk {
  chunk: string;
  alert_type: AlertType | null;
  sources: string[];
  links: OfficialLink[];
  is_final: boolean;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  medications?: string[];
  alertType?: AlertType | null;
  links?: OfficialLink[];
  sources?: string[];
  streaming?: boolean;
}

export interface Notice {
  message: string;
  alertType: AlertType;
}



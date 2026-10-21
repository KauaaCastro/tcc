import type {
  AlertType,
  AuthResponse,
  ChatRequest,
  PersonalFormValues,
  ProfileResponse,
  Session,
  StreamChunk,
} from '../types/medinteract';
import { toProfilePayload } from '../utils/profileForm';

const UUID_KEY = 'bula_uuid';
const TOKEN_KEY = 'bula_token';
const ALERT_TYPES: AlertType[] = ['danger', 'warning', 'restriction', 'info'];

export class ApiError extends Error {
  status: number;
  alertType: AlertType;

  constructor(message: string, status: number, alertType: AlertType = 'danger') {
    super(message);
    this.status = status;
    this.alertType = alertType;
  }
}

// Sessões
export function loadSession(): Session | null {
  const idUsuario = localStorage.getItem(UUID_KEY);
  const token = localStorage.getItem(TOKEN_KEY);
  return idUsuario && token ? { idUsuario, token } : null;
}

export function saveSession(session: Session): void {
  localStorage.setItem(UUID_KEY, session.idUsuario);
  localStorage.setItem(TOKEN_KEY, session.token);
}

export function clearSession(): void {
  localStorage.removeItem(UUID_KEY);
  localStorage.removeItem(TOKEN_KEY);
}

export function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError';
}

// Obtém os erros do backend (java ou python)
function extractErrorMessage(data: unknown, fallback: string): string {
  if (data && typeof data === 'object') {
    const body = data as Record<string, unknown>;
    if (typeof body.erro === 'string') return body.erro;
    if (typeof body.detail === 'string') return body.detail;
    const nested = body.error as Record<string, unknown> | undefined;
    if (nested && typeof nested.message === 'string') return nested.message;
  }
  return fallback;
}

function extractAlertType(data: unknown, status: number): AlertType {
  if (data && typeof data === 'object') {
    const candidate = (data as Record<string, unknown>).alert_type;
    if (ALERT_TYPES.includes(candidate as AlertType)) return candidate as AlertType;
  }
  return status >= 500 ? 'danger' : 'warning';
}

function networkError(): ApiError {
  return new ApiError(
    'Não foi possível conectar ao servidor. Verifique se o backend está em execução.',
    0,
    'danger',
  );
}

async function safeJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function buildHeaders(token?: string): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

async function request<T>(
  path: string,
  options: { method?: 'GET' | 'POST'; body?: unknown; token?: string } = {},
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      method: options.method ?? 'GET',
      headers: buildHeaders(options.token),
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    });
  } catch {
    throw networkError();
  }

  const data = await safeJson(response);
  if (!response.ok) {
    throw new ApiError(
      extractErrorMessage(data, 'Não foi possível concluir a solicitação.'),
      response.status,
      extractAlertType(data, response.status),
    );
  }
  return data as T;
}

export function login(email: string, password: string): Promise<AuthResponse> {
  return request<AuthResponse>('/api/auth/login', { method: 'POST', body: { email, password } });
}

export function register(data: { apelido: string; email: string; password: string }): Promise<AuthResponse> {
  return request<AuthResponse>('/api/auth/register', { method: 'POST', body: data });
}

export function fetchProfile(session: Session): Promise<ProfileResponse> {
  return request<ProfileResponse>(`/api/perfil/${session.idUsuario}`, { token: session.token });
}

// O backend limpa o texto, calcula o IMC e grava a ficha
export function saveProfile(session: Session, values: PersonalFormValues): Promise<ProfileResponse> {
  return request<ProfileResponse>('/api/perfil', {
    method: 'POST',
    token: session.token,
    body: { idUsuario: session.idUsuario, ...toProfilePayload(values) },
  });
}

// Lê eventos de POST /api/chat/stream em tempo real
export async function streamChat(
  payload: ChatRequest,
  onChunk: (chunk: StreamChunk) => void,
  signal?: AbortSignal,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { ...buildHeaders(), Accept: 'text/event-stream' },
      body: JSON.stringify(payload),
      signal,
    });
  } catch (error) {
    throw isAbortError(error) ? error : networkError();
  }

  if (!response.ok || !response.body) {
    const data = await safeJson(response);
    throw new ApiError(
      extractErrorMessage(data, 'Não foi possível processar a consulta.'),
      response.status,
      extractAlertType(data, response.status),
    );
  }

  const handleEvent = (rawEvent: string) => {
    const data = rawEvent
      .split(/\r?\n/)
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.slice(5).trim())
      .join('');
    if (!data) return;
    try {
      onChunk(JSON.parse(data) as StreamChunk);
    } catch {
      
    }
  };

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split(/\r?\n\r?\n/);
      buffer = events.pop() ?? '';
      events.forEach(handleEvent);
    }
  } catch (error) {
    throw isAbortError(error) ? error : networkError();
  }

  buffer += decoder.decode();
  if (buffer.trim()) handleEvent(buffer);
}




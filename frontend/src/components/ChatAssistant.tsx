import { useEffect, useRef, useState, type KeyboardEvent } from 'react';
import AlertBox from './AlertBox';
import MarkdownText from './MarkdownText';
import MedicationChips from './MedicationChips';
import { ApiError, isAbortError, streamChat } from '../services/api';
import type { AlertType, ChatMessage, HistoryItem, Notice, ProfileType, Session } from '../types/medinteract';
import { newId } from '../utils/format';

const MIN_QUESTION = 3;
const MAX_QUESTION = 1500;

const RESPONSE_ALERTS: Partial<Record<AlertType, { title?: string; message: string }>> = {
  danger: {
    title: 'Interação grave ou contraindicada',
    message: 'Revise a resposta acima e confirme com um profissional de saúde antes de qualquer decisão.',
  },
  warning: {
    title: 'Uso com cautela',
    message: 'Pode exigir monitoramento ou ajuste. Confirme com um profissional de saúde.',
  },
  restriction: {
    message: 'Serviço de IA indisponível. Consulte as fontes oficiais abaixo.',
  },
};

// Identifica medicamentos citados nos chips, no texto da pergunta e nas fontes da bula
function identificarMedicamentos(pergunta: string, chips: string[], sources?: string[]): string[] {
  const lista: string[] = [...chips];

  const padraoFarmaco = /\b[a-zà-ÿ]{3,}(?:ina|zol|mol|pril|sartana|statina|cilina|floxacino|pam|lol|dipino|profeno|ofenaco|micina|ona|ato|ol)\b/gi;
  const encontradosNoTexto = pergunta.match(padraoFarmaco) ?? [];

  for (const item of encontradosNoTexto) {
    if (!lista.some((m) => m.toLowerCase() === item.toLowerCase())) {
      lista.push(item);
    }
  }

  for (const src of sources ?? []) {
    const nomeBula = src.split(' - Chunk')[0]?.trim();
    if (nomeBula && !lista.some((m) => nomeBula.toLowerCase().includes(m.toLowerCase()) || m.toLowerCase().includes(nomeBula.toLowerCase()))) {
      lista.push(nomeBula);
    }
  }

  return lista;
}

interface ChatAssistantProps {
  session: Session;
  profile: ProfileType;
  selected: HistoryItem | null;
  resetKey: number;
  onConversationSaved: () => void;
}

export default function ChatAssistant({ session, profile, selected, resetKey, onConversationSaved }: ChatAssistantProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [medications, setMedications] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Notice | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    abortRef.current?.abort();
    setIsLoading(false);
    setError(null);
    setMedications([]);
    setMessages(
      selected
        ? [
            {
              id: newId(),
              role: 'user',
              content: selected.perguntaUsuario,
              medications: identificarMedicamentos(selected.perguntaUsuario, []),
            },
            { id: newId(), role: 'assistant', content: selected.respostaIa },
          ]
        : [],
    );
  }, [selected, resetKey]);

  useEffect(() => () => abortRef.current?.abort(), []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (isLoading) return;
    const text = question.trim();
    if (text.length < MIN_QUESTION || text.length > MAX_QUESTION) {
      setError({
        message: `A pergunta deve ter entre ${MIN_QUESTION} e ${MAX_QUESTION} caracteres.`,
        alertType: 'warning',
      });
      return;
    }

    const controller = new AbortController();
    abortRef.current = controller;
    const userId = newId();
    const assistantId = newId();
    const medsIniciais = identificarMedicamentos(text, medications);

    const updateAssistant = (update: (message: ChatMessage) => ChatMessage) =>
      setMessages((prev) => prev.map((m) => (m.id === assistantId ? update(m) : m)));

    setMessages((prev) => [
      ...prev,
      { id: userId, role: 'user', content: text, medications: medsIniciais },
      { id: assistantId, role: 'assistant', content: '', streaming: true },
    ]);
    setQuestion('');
    setError(null);
    setIsLoading(true);

    try {
      await streamChat(
        { idUsuario: session.idUsuario, question: text, profile, medications },
        (chunk) => {
          updateAssistant((m) => ({
            ...m,
            content: m.content + chunk.chunk,
            ...(chunk.is_final
              ? { alertType: chunk.alert_type, sources: chunk.sources, links: chunk.links, streaming: false }
              : {}),
          }));
          if (chunk.is_final && chunk.sources.length > 0) {
            const medsCompletos = identificarMedicamentos(text, medications, chunk.sources);
            setMessages((prev) =>
              prev.map((m) => (m.id === userId ? { ...m, medications: medsCompletos } : m)),
            );
          }
        },
        controller.signal,
      );
      updateAssistant((m) => ({ ...m, streaming: false }));
      onConversationSaved();
    } catch (err) {
      if (isAbortError(err)) return;
      const apiError = err instanceof ApiError ? err : null;
      setError({
        message: apiError?.message ?? 'Não foi possível concluir a consulta.',
        alertType: apiError?.alertType ?? 'danger',
      });
      setMessages((prev) => prev.filter((m) => !(m.id === assistantId && !m.content)));
    } finally {
      if (abortRef.current === controller) {
        setIsLoading(false);
        abortRef.current = null;
      }
    }
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      void handleSend();
    }
  };

  return (
    <section className="chat">
      <div className="chat-messages" aria-live="polite">
        {messages.length === 0 ? (
          <div className="chat-welcome">
            <h2>Consulta de medicamentos</h2>
            <p>Digite uma dúvida abaixo ou selecione uma conversa recente na barra à esquerda.</p>
          </div>
        ) : (
          messages.map((message) => {
            const alert = !message.streaming && message.alertType ? RESPONSE_ALERTS[message.alertType] : undefined;
            return (
              <div key={message.id} className={`msg msg-${message.role}`}>
                <div className="bubble">
                  {message.role === 'user' ? (
                    message.content
                  ) : message.content ? (
                    <MarkdownText text={message.content} />
                  ) : (
                    <span>Consultando bulas...</span>
                  )}
                </div>
                {message.role === 'user' && message.medications && message.medications.length > 0 && (
                  <div className="msg-sources">
                    Medicamentos citados: <strong>{message.medications.join(', ')}</strong>
                  </div>
                )}
                {alert && message.alertType && (
                  <AlertBox type={message.alertType} title={alert.title} message={alert.message} links={message.links} />
                )}
                {!message.streaming && message.sources && message.sources.length > 0 && (
                  <div className="msg-sources">Fontes: {message.sources.join(' · ')}</div>
                )}
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-composer">
        {error && <AlertBox type={error.alertType} message={error.message} onClose={() => setError(null)} />}
        <MedicationChips value={medications} onChange={setMedications} disabled={isLoading} />
        <div className="composer-row">
          <textarea
            className="input"
            rows={1}
            maxLength={MAX_QUESTION}
            placeholder="Digite sua dúvida sobre medicamentos..."
            value={question}
            disabled={isLoading}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            aria-label="Pergunta"
          />
          <button type="button" className="btn btn-primary" onClick={() => void handleSend()} disabled={isLoading || !question.trim()}>
            {isLoading ? 'Aguarde...' : 'Enviar'}
          </button>
        </div>
        <p className="disclaimer">As informações apresentadas têm caráter educativo e não substituem avaliação médica.</p>
      </div>
    </section>
  );
}

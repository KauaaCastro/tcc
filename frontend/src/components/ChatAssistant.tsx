import { useEffect, useRef, useState, type KeyboardEvent } from 'react';
import AlertBox from './AlertBox';
import MarkdownText from './MarkdownText';
import MedicationChips from './MedicationChips';
import { ApiError, isAbortError, streamChat } from '../services/api';
import type { AlertType, ChatMessage, HistoryItem, Notice, ProfileType, Session } from '../types/medinteract';
import { newId } from '../utils/format';

const MIN_QUESTION = 3;
const MAX_QUESTION = 1500;

// Mensagem curta exibida abaixo da resposta, conforme o tipo de alerta
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

interface ChatAssistantProps {
  session: Session;
  profile: ProfileType;
  selected: HistoryItem | null;
  resetKey: number;
  onConversationSaved: () => void;
}

// Área central: chatbot simples com resposta em tempo real (SSE)
export default function ChatAssistant({ session, profile, selected, resetKey, onConversationSaved }: ChatAssistantProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [medications, setMedications] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Notice | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Troca de conversa ou nova conversa: cancela o stream e recarrega a tela
  useEffect(() => {
    abortRef.current?.abort();
    setIsLoading(false);
    setError(null);
    setMedications([]);
    setMessages(
      selected
        ? [
            { id: newId(), role: 'user', content: selected.perguntaUsuario },
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
    const assistantId = newId();
    const updateAssistant = (update: (message: ChatMessage) => ChatMessage) =>
      setMessages((prev) => prev.map((m) => (m.id === assistantId ? update(m) : m)));

    setMessages((prev) => [
      ...prev,
      { id: newId(), role: 'user', content: text },
      { id: assistantId, role: 'assistant', content: '', streaming: true },
    ]);
    setQuestion('');
    setError(null);
    setIsLoading(true);

    try {
      await streamChat(
        { idUsuario: session.idUsuario, question: text, profile, medications },
        (chunk) =>
          updateAssistant((m) => ({
            ...m,
            content: m.content + chunk.chunk,
            ...(chunk.is_final
              ? { alertType: chunk.alert_type, sources: chunk.sources, links: chunk.links, streaming: false }
              : {}),
          })),
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

  // Enter envia; Shift+Enter quebra a linha
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
            <h2>Como posso ajudar?</h2>
            <p>Pergunte sobre medicamentos, doses e interações. As respostas seguem as bulas oficiais da ANVISA.</p>
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
                    <>
                      <MarkdownText text={message.content} />
                      {message.streaming && <span className="cursor" aria-hidden="true" />}
                    </>
                  ) : (
                    <span>Analisando as bulas...</span>
                  )}
                </div>
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
            {isLoading ? 'Respondendo...' : 'Enviar'}
          </button>
        </div>
        <p className="disclaimer">O MedInteract é um apoio informativo e não substitui a avaliação de um profissional de saúde.</p>
      </div>
    </section>
  );
}

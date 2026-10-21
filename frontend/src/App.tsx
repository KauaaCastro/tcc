import { useCallback, useEffect, useState } from 'react';
import AlertBox from './components/AlertBox';
import AuthScreen from './components/AuthScreen';
import ChatAssistant from './components/ChatAssistant';
import HistorySidebar from './components/HistorySidebar';
import PersonalInfoModal from './components/PersonalInfoModal';
import TermsModal from './components/TermsModal';
import ThemeToggle from './components/ThemeToggle';
import { useTheme } from './hooks/useTheme';
import { ApiError, clearSession, fetchProfile, loadSession, saveSession } from './services/api';
import type {
  HistoryItem,
  Notice,
  PersonalProfile,
  ProfileResponse,
  ProfileType,
  Session,
  UserAccount,
} from './types/medinteract';

const SESSION_ERRORS = [401, 403, 404];
const TERMS_KEY = 'medinteract_terms_accepted';

export default function App() {
  const { theme, toggleTheme } = useTheme();
  const [session, setSession] = useState<Session | null>(loadSession);
  const [account, setAccount] = useState<UserAccount | null>(null);
  const [perfil, setPerfil] = useState<PersonalProfile | null>(null);
  const [imc, setImc] = useState<number | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [authNotice, setAuthNotice] = useState<Notice | null>(null);
  const [profileType, setProfileType] = useState<ProfileType>('PATIENT');
  const [selected, setSelected] = useState<HistoryItem | null>(null);
  const [resetKey, setResetKey] = useState(0);
  const [showPersonalInfo, setShowPersonalInfo] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(() => localStorage.getItem(TERMS_KEY) === 'true');
  const [termsDeclined, setTermsDeclined] = useState(false);

  const acceptTerms = () => {
    localStorage.setItem(TERMS_KEY, 'true');
    setTermsAccepted(true);
  };

  // Recusa encerra a sessão e tenta fechar a aba
  const declineTerms = () => {
    clearSession();
    localStorage.removeItem(TERMS_KEY);
    setSession(null);
    setTermsDeclined(true);
    window.close();
  };

  const logout = useCallback((message?: string) => {
    clearSession();
    setSession(null);
    setAccount(null);
    setPerfil(null);
    setImc(null);
    setHistory([]);
    setSelected(null);
    setNotice(null);
    setShowPersonalInfo(false);
    setAuthNotice(message ? { message, alertType: 'info' } : null);
  }, []);

  const applyProfile = useCallback((data: ProfileResponse) => {
    setAccount(data.usuario);
    setPerfil(data.perfil);
    setImc(data.imcCalculado);
    if (data.historico) setHistory(data.historico);
  }, []);

  const loadProfile = useCallback(
    async (current: Session) => {
      try {
        applyProfile(await fetchProfile(current));
      } catch (err) {
        if (err instanceof ApiError && SESSION_ERRORS.includes(err.status)) {
          logout('Sua sessão expirou. Entre novamente.');
          return;
        }
        setNotice({
          message: err instanceof ApiError ? err.message : 'Não foi possível carregar seus dados.',
          alertType: err instanceof ApiError ? err.alertType : 'danger',
        });
      } finally {
        setLoadingProfile(false);
      }
    },
    [applyProfile, logout],
  );

  useEffect(() => {
    if (!session) return;
    setLoadingProfile(true);
    void loadProfile(session);
  }, [session, loadProfile]);

  const handleAuthenticated = (newSession: Session, newNotice?: Notice) => {
    saveSession(newSession);
    setAuthNotice(null);
    setNotice(newNotice ?? null);
    setSelected(null);
    setSession(newSession);
  };

  const handleNewConversation = () => {
    setSelected(null);
    setResetKey((key) => key + 1);
  };

  if (termsDeclined) {
    return (
      <main className="auth-page">
        <section className="auth-card">
          <h1>MedInteract</h1>
          <p className="auth-subtitle">
            Sem a permissão de uso dos dados não é possível utilizar o sistema. Você já pode fechar esta página.
          </p>
          <button type="button" className="btn btn-primary btn-block" onClick={() => setTermsDeclined(false)}>
            Rever os termos
          </button>
        </section>
      </main>
    );
  }

  if (!termsAccepted) {
    return <TermsModal onAccept={acceptTerms} onDecline={declineTerms} />;
  }

  if (!session) {
    return <AuthScreen notice={authNotice} onAuthenticated={handleAuthenticated} />;
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <span className="app-logo">MedInteract</span>
          {account && <span className="app-greeting">Olá, {account.apelido}</span>}
        </div>
        <div className="header-actions">
          <div className="segmented" role="group" aria-label="Perfil de resposta">
            <button type="button" aria-pressed={profileType === 'PATIENT'} onClick={() => setProfileType('PATIENT')}>
              Paciente
            </button>
            <button type="button" aria-pressed={profileType === 'PROFESSIONAL'} onClick={() => setProfileType('PROFESSIONAL')}>
              Profissional
            </button>
          </div>
          <ThemeToggle theme={theme} onToggle={toggleTheme} />
          <button type="button" className="btn btn-primary" onClick={() => setShowPersonalInfo(true)}>
            Informações pessoais
          </button>
          <button type="button" className="btn" onClick={() => logout()}>
            Sair
          </button>
        </div>
      </header>

      <div className="app-body">
        <HistorySidebar
          items={history}
          selectedId={selected?.idConsulta ?? null}
          loading={loadingProfile}
          onSelect={setSelected}
          onNew={handleNewConversation}
        />
        <div className="chat-column">
          {notice && (
            <div className="chat-notice">
              <AlertBox type={notice.alertType} message={notice.message} onClose={() => setNotice(null)} />
            </div>
          )}
          <ChatAssistant
            session={session}
            profile={profileType}
            selected={selected}
            resetKey={resetKey}
            onConversationSaved={() => void loadProfile(session)}
          />
        </div>
      </div>

      {showPersonalInfo && (
        <PersonalInfoModal
          session={session}
          account={account}
          perfil={perfil}
          imc={imc}
          onClose={() => setShowPersonalInfo(false)}
          onSaved={applyProfile}
        />
      )}
    </div>
  );
}

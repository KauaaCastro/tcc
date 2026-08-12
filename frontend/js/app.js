/* ─────────────────────────────────────────────
   CONFIG — Adapte para integração com seu backend
   ────────────────────────────────────────────── */
const CONFIG = {
  // URL local relativa (Docker Nginx proxy) ou URL direta com fallback para desenvolvimento local sem Docker
  API_BASE_URL: (window.location.protocol === 'file:' || (window.location.hostname === 'localhost' && window.location.port !== ''))
    ? "http://localhost:5000/api/chat"
    : "/api/chat",

  // Dados do usuário
  USER: {
    name: "Dr. Usuário",
    initials: "Dr",
    role: "Farmacêutico Clínico",
  }
};

/* ─────────────────────────────────────────────
   STATE
   ────────────────────────────────────────────── */
let state = {
  conversations: [],   // Array de { id, title, messages, date, count }
  activeConvId: null,
  isLoading: false,
  isDark: true,
  messageCount: 0,
};

/* ─────────────────────────────────────────────
   API ADAPTER
   ────────────────────────────────────────────── */
async function callAI(messages) {
  const response = await fetch(CONFIG.API_BASE_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      messages: messages.map(m => ({ role: m.role, content: m.content }))
    })
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `HTTP ${response.status}`);
  }

  const data = await response.json();
  return data?.response || 'Sem resposta do servidor.';
}

/* ─────────────────────────────────────────────
   CONVERSATION MANAGEMENT
   ────────────────────────────────────────────── */
function createConversation(firstMessage = null) {
  const id = 'conv_' + Date.now();
  const conv = {
    id,
    title: firstMessage ? summarizeTitle(firstMessage) : 'Nova Conversa',
    messages: [],
    date: new Date(),
    icon: getRandomIcon(),
  };
  state.conversations.unshift(conv);
  state.activeConvId = id;
  renderSidebar();
  return conv;
}

function getActiveConv() {
  return state.conversations.find(c => c.id === state.activeConvId) || null;
}

function summarizeTitle(text) {
  const clean = text.trim();
  if (clean.length <= 38) return clean;
  return clean.substring(0, 36) + '…';
}

function getRandomIcon() {
  const icons = ['💊', '⚗️', '🔬', '🧬', '🩺', '🧪', '📋', '🩸'];
  return icons[Math.floor(Math.random() * icons.length)];
}

function selectConversation(id) {
  state.activeConvId = id;
  renderSidebar();
  renderMessages();
  const conv = getActiveConv();
  updateChatHeader(conv);
}

function updateChatHeader(conv) {
  const title = conv ? conv.title : 'Nova Conversa';
  const count = conv ? conv.messages.filter(m => m.role === 'user').length : 0;
  document.getElementById('chatTitle').textContent = title;
  document.getElementById('chatSubtitle').textContent = `${count} consulta${count !== 1 ? 's' : ''} · MedInteract AI`;
}

/* ─────────────────────────────────────────────
   RENDER SIDEBAR
   ────────────────────────────────────────────── */
function renderSidebar() {
  const list = document.getElementById('convList');
  list.innerHTML = '';

  if (state.conversations.length === 0) {
    list.innerHTML = `<div style="padding:20px 14px;text-align:center;color:var(--text-muted);font-size:12px;">Nenhuma conversa ainda.<br>Inicie uma nova consulta.</div>`;
    return;
  }

  // Group by date
  const today = new Date();
  const groups = { today: [], yesterday: [], older: [] };

  state.conversations.forEach(conv => {
    const d = new Date(conv.date);
    const diffDays = Math.floor((today - d) / 86400000);
    if (diffDays === 0) groups.today.push(conv);
    else if (diffDays === 1) groups.yesterday.push(conv);
    else groups.older.push(conv);
  });

  const render = (label, items) => {
    if (!items.length) return;
    const sec = document.createElement('div');
    sec.className = 'conv-section-label';
    sec.textContent = label;
    list.appendChild(sec);

    items.forEach(conv => {
      const el = document.createElement('div');
      el.className = `conv-item ${conv.id === state.activeConvId ? 'active' : ''}`;
      el.setAttribute('data-id', conv.id);

      const msgCount = conv.messages.filter(m => m.role === 'user').length;
      const timeStr = new Date(conv.date).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });

      el.innerHTML = `
        <div class="conv-icon">${conv.icon}</div>
        <div class="conv-info">
          <div class="conv-title">${escHtml(conv.title)}</div>
          <div class="conv-meta">
            <span class="conv-date">${timeStr}</span>
            ${msgCount > 0 ? `<span class="conv-count">${msgCount} msg</span>` : ''}
          </div>
        </div>
        <button class="conv-options" title="Opções" onclick="event.stopPropagation();deleteConv('${conv.id}')">✕</button>
      `;
      el.addEventListener('click', () => selectConversation(conv.id));
      list.appendChild(el);
    });
  };

  render('Hoje', groups.today);
  render('Ontem', groups.yesterday);
  render('Anteriores', groups.older);
}

function deleteConv(id) {
  state.conversations = state.conversations.filter(c => c.id !== id);
  if (state.activeConvId === id) {
    state.activeConvId = null;
    showWelcome();
    updateChatHeader(null);
  }
  renderSidebar();
  showToast('🗑️ Conversa removida');
}

/* ─────────────────────────────────────────────
   RENDER MESSAGES
   ────────────────────────────────────────────── */
function showWelcome() {
  const container = document.getElementById('messagesContainer');
  container.innerHTML = document.getElementById('welcomeScreen')?.outerHTML || '';
  // Re-attach welcome screen
  const ws = createWelcomeScreen();
  container.innerHTML = '';
  container.appendChild(ws);
}

function createWelcomeScreen() {
  const div = document.createElement('div');
  div.className = 'welcome-screen';
  div.id = 'welcomeScreen';
  div.innerHTML = `
    <div class="welcome-logo-large">
      <svg viewBox="0 0 24 24"><path d="M12 2L4 6v6c0 5.55 3.84 10.74 8 12 4.16-1.26 8-6.45 8-12V6l-8-4z"/><rect x="11" y="7" width="2" height="10" fill="rgba(255,255,255,0.6)"/><rect x="7" y="11" width="10" height="2" fill="rgba(255,255,255,0.6)"/></svg>
    </div>
    <h1 class="welcome-headline">Bem-vindo ao <strong>MedInteract</strong></h1>
    <p class="welcome-desc">Plataforma especializada em análise de interações medicamentosas com inteligência artificial. Consulte combinações, mecanismos farmacológicos e condutas clínicas.</p>
    <div class="welcome-grid">
      ${[
        ['⚗️','Paracetamol + Álcool','Riscos hepáticos e doses seguras','Paracetamol e álcool: quais os riscos hepáticos e qual a dose segura?'],
        ['🧠','Síndrome Serotoninérgica','Causas, sintomas e prevenção','Explique a síndrome serotoninérgica: causas, sintomas e quais medicamentos envolvem'],
        ['🔬','CYP450 e Metabolismo','Indutores, inibidores e substratos','Como o sistema CYP450 afeta o metabolismo de medicamentos? Dê exemplos de indutores e inibidores'],
        ['🩸','Warfarina — Interações','Principais interações e mecanismos','Warfarina tem muitas interações medicamentosas. Liste as principais e explique os mecanismos'],
      ].map(([icon,title,desc,q]) => `
        <div class="welcome-card" onclick="sendQuick(${JSON.stringify(q)})">
          <div class="wc-icon">${icon}</div>
          <div class="wc-text">
            <div class="wc-title">${title}</div>
            <div class="wc-desc">${desc}</div>
          </div>
        </div>
      `).join('')}
    </div>
  `;
  return div;
}

function renderMessages() {
  const container = document.getElementById('messagesContainer');
  const conv = getActiveConv();

  if (!conv || conv.messages.length === 0) {
    showWelcome();
    return;
  }

  container.innerHTML = '';

  conv.messages.forEach(msg => {
    container.appendChild(createMessageEl(msg));
  });

  container.scrollTop = container.scrollHeight;
}

function createMessageEl(msg) {
  const div = document.createElement('div');
  div.className = `msg-group ${msg.role}`;

  const isAI = msg.role === 'ai';
  const time = new Date(msg.ts).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  const senderName = isAI ? 'MedInteract AI' : CONFIG.USER.name;

  const avatarHTML = isAI
    ? `<div class="msg-avatar ai-av"><svg viewBox="0 0 24 24"><path d="M12 2L4 6v6c0 5.55 3.84 10.74 8 12 4.16-1.26 8-6.45 8-12V6l-8-4z"/><rect x="11" y="7" width="2" height="10" fill="rgba(255,255,255,0.6)"/><rect x="7" y="11" width="10" height="2" fill="rgba(255,255,255,0.6)"/></svg></div>`
    : `<div class="msg-avatar">${CONFIG.USER.initials}</div>`;

  const badgeHTML = isAI ? `<span class="sender-badge">AI</span>` : '';
  const bubbleContent = isAI ? formatAIContent(msg.content) : `<p>${escHtml(msg.content)}</p>`;

  div.innerHTML = `
    ${avatarHTML}
    <div class="msg-body">
      <div class="msg-sender">${escHtml(senderName)} ${badgeHTML}</div>
      <div class="msg-bubble">${bubbleContent}</div>
      <div class="msg-time">${time}</div>
    </div>
  `;
  return div;
}

function addMessageToDOM(msg) {
  const container = document.getElementById('messagesContainer');
  const welcome = container.querySelector('.welcome-screen');
  if (welcome) welcome.remove();
  const el = createMessageEl(msg);
  container.appendChild(el);
  container.scrollTop = container.scrollHeight;
}

/* ─────────────────────────────────────────────
   AI RESPONSE FORMATTER
   ────────────────────────────────────────────── */
function formatAIContent(text) {
  let h = escHtml(text);

  // Risk levels
  h = h.replace(/\b(ALTO|CONTRAINDICADO|GRAVÍSSIMO)\b/gi,
    '<span class="risk-chip alto">⊗ $1</span>');
  h = h.replace(/\b(MODERADO|CAUTELA|MODERADA)\b/gi,
    '<span class="risk-chip moderado">◈ $1</span>');
  h = h.replace(/\b(BAIXO|MONITORAR|MENOR)\b/gi,
    '<span class="risk-chip baixo">◎ $1</span>');

  // Drug names: **bold** and `code`
  h = h.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  h = h.replace(/`([^`]+)`/g, '<span class="drug-tag">$1</span>');

  // Headers
  h = h.replace(/^###\s+(.+)$/gm, '<h3>$1</h3>');
  h = h.replace(/^##\s+(.+)$/gm,  '<h3>$1</h3>');

  // Lists
  const lines = h.split('\n');
  const out = [];
  let inList = false;

  for (let line of lines) {
    line = line.trim();
    if (!line) continue;

    const isBullet = /^[\-\*•]\s+/.test(line);
    if (isBullet) {
      if (!inList) { out.push('<ul>'); inList = true; }
      out.push(`<li>${line.replace(/^[\-\*•]\s+/, '')}</li>`);
    } else {
      if (inList) { out.push('</ul>'); inList = false; }
      if (line.startsWith('<h3>') || line.startsWith('<ul>') || line.includes('risk-chip')) {
        out.push(line);
      } else {
        out.push(`<p>${line}</p>`);
      }
    }
  }
  if (inList) out.push('</ul>');
  return out.join('');
}

/* ─────────────────────────────────────────────
   SEND MESSAGE
   ────────────────────────────────────────────── */
async function sendMessage(text) {
  text = text.trim();
  if (!text || state.isLoading) return;

  state.isLoading = true;
  updateSendBtn(true);

  // Create conversation if needed
  if (!state.activeConvId) {
    createConversation(text);
  }

  const conv = getActiveConv();

  // User message
  const userMsg = { role: 'user', content: text, ts: Date.now() };
  conv.messages.push(userMsg);
  addMessageToDOM(userMsg);

  // Update title if first message
  if (conv.messages.filter(m => m.role === 'user').length === 1) {
    conv.title = summarizeTitle(text);
    renderSidebar();
    updateChatHeader(conv);
  }

  // Typing indicator
  const typingEl = showTyping();

  try {
    // Build message history for API
    const apiMessages = conv.messages
      .filter(m => m.role === 'user' || m.role === 'ai')
      .map(m => ({ role: m.role === 'ai' ? 'assistant' : 'user', content: m.content }));

    const aiText = await callAI(apiMessages);

    typingEl.remove();

    const aiMsg = { role: 'ai', content: aiText, ts: Date.now() };
    conv.messages.push(aiMsg);
    addMessageToDOM(aiMsg);
    updateChatHeader(conv);
    renderSidebar();

  } catch (err) {
    typingEl.remove();
    const errMsg = { role: 'ai', content: `Erro ao processar a consulta: ${err.message}. Verifique sua conexão e tente novamente.`, ts: Date.now() };
    conv.messages.push(errMsg);
    addMessageToDOM(errMsg);
    console.error('API Error:', err);
  }

  state.isLoading = false;
  updateSendBtn(false);
  document.getElementById('chatInput').focus();
}

function showTyping() {
  const container = document.getElementById('messagesContainer');
  const el = document.createElement('div');
  el.className = 'typing-group';
  el.id = 'typingIndicator';
  el.innerHTML = `
    <div class="msg-avatar ai-av">
      <svg viewBox="0 0 24 24"><path d="M12 2L4 6v6c0 5.55 3.84 10.74 8 12 4.16-1.26 8-6.45 8-12V6l-8-4z"/><rect x="11" y="7" width="2" height="10" fill="rgba(255,255,255,0.6)"/><rect x="7" y="11" width="10" height="2" fill="rgba(255,255,255,0.6)"/></svg>
    </div>
    <div class="typing-bubble">
      <span class="typing-label">MedInteract está analisando</span>
      <div class="t-dots">
        <div class="td"></div><div class="td"></div><div class="td"></div>
      </div>
    </div>
  `;
  container.appendChild(el);
  container.scrollTop = container.scrollHeight;
  return el;
}

function updateSendBtn(loading) {
  const btn = document.getElementById('sendBtn');
  btn.disabled = loading;
  btn.style.opacity = loading ? '0.5' : '1';
}

function sendQuick(text) {
  document.getElementById('chatInput').value = text;
  sendMessage(text);
  document.getElementById('chatInput').value = '';
  document.getElementById('charCount').textContent = '0 / 800';
}

function clearInput() {
  document.getElementById('chatInput').value = '';
  document.getElementById('charCount').textContent = '0 / 800';
  const inp = document.getElementById('chatInput');
  inp.style.height = 'auto';
  inp.focus();
}

function clearChat() {
  const conv = getActiveConv();
  if (!conv) return;
  conv.messages = [];
  showWelcome();
  updateChatHeader(conv);
  renderSidebar();
  showToast('🧹 Conversa limpa');
}

/* ─────────────────────────────────────────────
   INPUT EVENTS
   ────────────────────────────────────────────── */
const chatInput = document.getElementById('chatInput');
const charCount = document.getElementById('charCount');

chatInput.addEventListener('input', () => {
  charCount.textContent = `${chatInput.value.length} / 800`;
  chatInput.style.height = 'auto';
  chatInput.style.height = Math.min(chatInput.scrollHeight, 140) + 'px';
});

chatInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    const text = chatInput.value;
    if (text.trim()) {
      sendMessage(text);
      chatInput.value = '';
      charCount.textContent = '0 / 800';
      chatInput.style.height = 'auto';
    }
  }
});

document.getElementById('sendBtn').addEventListener('click', () => {
  const text = chatInput.value;
  if (text.trim()) {
    sendMessage(text);
    chatInput.value = '';
    charCount.textContent = '0 / 800';
    chatInput.style.height = 'auto';
  }
});

document.getElementById('newChatBtn').addEventListener('click', () => {
  state.activeConvId = null;
  showWelcome();
  updateChatHeader(null);
  document.getElementById('chatInput').focus();
  renderSidebar();
});

/* ─────────────────────────────────────────────
   USER MENU
   ────────────────────────────────────────────── */
const userAvatarBtn = document.getElementById('userAvatarBtn');
const userDropdown  = document.getElementById('userDropdown');

userAvatarBtn.addEventListener('click', e => {
  e.stopPropagation();
  userDropdown.classList.toggle('open');
});

document.addEventListener('click', () => userDropdown.classList.remove('open'));
userDropdown.addEventListener('click', e => e.stopPropagation());

// Populate user info
document.getElementById('userInitials').textContent   = CONFIG.USER.initials;
document.getElementById('dropdownInitials').textContent = CONFIG.USER.initials;
document.getElementById('dropdownName').textContent    = CONFIG.USER.name;

/* ─────────────────────────────────────────────
   DARK MODE
   ────────────────────────────────────────────── */
function toggleDarkMode() {
  state.isDark = !state.isDark;
  document.documentElement.setAttribute('data-theme', state.isDark ? 'dark' : 'light');
  const toggle = document.getElementById('themeToggle');
  const icon   = document.getElementById('themeIcon');
  toggle.classList.toggle('on', state.isDark);
  icon.textContent = state.isDark ? '🌙' : '☀️';
  showToast(state.isDark ? '🌙 Modo escuro ativado' : '☀️ Modo claro ativado');
}

/* ─────────────────────────────────────────────
   ACTIONS
   ────────────────────────────────────────────── */
function openProfile() {
  userDropdown.classList.remove('open');
  showToast('👤 Perfil em desenvolvimento');
}

function openSettings() {
  userDropdown.classList.remove('open');
  showToast('⚙️ Configurações em desenvolvimento');
}

function logout() {
  userDropdown.classList.remove('open');
  showToast('🚪 Saindo...');
  setTimeout(() => { alert('Redirecionando para login...'); }, 1000);
}

/* ─────────────────────────────────────────────
   TOAST
   ────────────────────────────────────────────── */
let toastTimer = null;
function showToast(msg) {
  const t = document.getElementById('toast');
  t.innerHTML = msg;
  t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 2500);
}

/* ─────────────────────────────────────────────
   UTILITIES
   ────────────────────────────────────────────── */
function escHtml(s) {
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

/* ─────────────────────────────────────────────
   SIDEBAR SEARCH FILTER
   ────────────────────────────────────────────── */
document.getElementById('convSearch').addEventListener('input', e => {
  const q = e.target.value.toLowerCase();
  document.querySelectorAll('.conv-item').forEach(el => {
    const title = el.querySelector('.conv-title')?.textContent.toLowerCase() || '';
    el.style.display = title.includes(q) ? '' : 'none';
  });
});

/* ─────────────────────────────────────────────
   PARTICLE CANVAS (fundo animado)
   ────────────────────────────────────────────── */
(function initParticles() {
  const canvas = document.getElementById('bg-canvas');
  const ctx    = canvas.getContext('2d');
  let W, H, particles = [];

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  function makeParticle() {
    return {
      x: Math.random() * W,
      y: Math.random() * H,
      r: Math.random() * 1.4 + 0.3,
      vx: (Math.random() - 0.5) * 0.25,
      vy: (Math.random() - 0.5) * 0.25,
      alpha: Math.random() * 0.4 + 0.05,
    };
  }

  function init() {
    resize();
    particles = Array.from({ length: Math.floor(W / 18) }, makeParticle);
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    const dark = document.documentElement.getAttribute('data-theme') !== 'light';
    const baseColor = dark ? '74,222,128' : '22,163,74';

    // Draw particles
    particles.forEach(p => {
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
      if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${baseColor},${p.alpha})`;
      ctx.fill();
    });

    // Draw connections
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const d  = Math.sqrt(dx * dx + dy * dy);
        if (d < 110) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(${baseColor},${0.07 * (1 - d / 110)})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }
    }

    requestAnimationFrame(draw);
  }

  init();
  draw();
  window.addEventListener('resize', () => { init(); });
})();

/* ─────────────────────────────────────────────
   INIT
   ────────────────────────────────────────────── */
renderSidebar();

/* ══════════════════════════════════════════
   chat.js — Research Agent chat interface
   ══════════════════════════════════════════ */

let currentSessionId = typeof SESSION_ID !== 'undefined' ? SESSION_ID : null;

const chatMessages  = document.getElementById('chatMessages');
const userInput     = document.getElementById('userInput');
const btnSend       = document.getElementById('btnSend');
const btnNewSession = document.getElementById('btnNewSession');
const btnClearChat  = document.getElementById('btnClearChat');
const btnUploadPdf  = document.getElementById('btnUploadPdf');
const btnAttach     = document.getElementById('btnAttach');
const hiddenFile    = document.getElementById('hiddenFileInput');
const modeSelect    = document.getElementById('modeSelect');
const citStyle      = document.getElementById('citationStyle');
const modeLabel     = document.getElementById('modeLabel');
const sessionTitle  = document.getElementById('sessionTitle');
const pdfBar        = document.getElementById('pdfUploadBar');
const welcomeMsg    = document.getElementById('welcomeMsg');

const MODE_LABELS = {
  chat: 'Chat / Q&A', search: 'Search Papers',
  report: 'Generate Report', gaps: 'Research Gaps', cite: 'Generate Citations'
};

// ── Mode label ──────────────────────────────
modeSelect?.addEventListener('change', () => {
  modeLabel.textContent = 'Mode: ' + MODE_LABELS[modeSelect.value];
});

// ── Suggestion chips ────────────────────────
document.querySelectorAll('.suggestion-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const text = btn.textContent.replace(/^[^\w]+/, '').trim();
    userInput.value = text;
    sendMessage();
  });
});

// ── Textarea auto-grow ───────────────────────
userInput?.addEventListener('input', () => {
  userInput.style.height = 'auto';
  userInput.style.height = Math.min(userInput.scrollHeight, 160) + 'px';
  document.getElementById('charCount').textContent = userInput.value.length + ' chars';
});

// ── Ctrl+Enter to send ───────────────────────
userInput?.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); sendMessage(); }
});

btnSend?.addEventListener('click', sendMessage);

// ── New session ──────────────────────────────
btnNewSession?.addEventListener('click', async () => {
  const res  = await fetch('/api/sessions', { method: 'POST' });
  const data = await res.json();
  window.location.href = `/chat/${data.id}`;
});

// ── Clear chat ───────────────────────────────
btnClearChat?.addEventListener('click', () => {
  if (!confirm('Clear this session?')) return;
  if (currentSessionId) {
    fetch(`/api/sessions/${currentSessionId}`, { method: 'DELETE' })
      .then(() => window.location.href = '/chat');
  }
});

// ── PDF upload ───────────────────────────────
btnUploadPdf?.addEventListener('click', () => hiddenFile.click());
btnAttach?.addEventListener('click',    () => hiddenFile.click());
hiddenFile?.addEventListener('change',  () => {
  if (hiddenFile.files[0]) uploadPdf(hiddenFile.files[0]);
});

async function uploadPdf(file) {
  pdfBar.classList.remove('d-none');
  appendMessage('user', `📎 Uploaded: **${file.name}** — analysing…`);
  const fd = new FormData();
  fd.append('file', file);
  try {
    const res  = await fetch('/api/upload', { method: 'POST', body: fd });
    const data = await res.json();
    pdfBar.classList.add('d-none');
    if (data.error) {
      appendMessage('assistant', `⚠️ ${data.error}`);
      return;
    }
    const content =
      `## 📄 ${file.name}\n\n` +
      `**Words:** ${data.word_count?.toLocaleString()}\n\n` +
      `### Summary\n${data.summary}\n\n` +
      `### Key Insights\n${data.insights}`;
    appendMessage('assistant', content, 'text', true);
  } catch (e) {
    pdfBar.classList.add('d-none');
    appendMessage('assistant', `⚠️ Upload failed: ${e.message}`);
  }
}

// ── Send message ─────────────────────────────
async function sendMessage() {
  const text = userInput?.value.trim();
  if (!text) return;

  welcomeMsg?.remove();
  appendMessage('user', text);
  userInput.value = '';
  userInput.style.height = 'auto';
  document.getElementById('charCount').textContent = '0 chars';

  const typingId = showTyping();
  btnSend.disabled = true;

  try {
    const payload = {
      session_id:     currentSessionId,
      message:        text,
      mode:           modeSelect?.value || 'chat',
      citation_style: citStyle?.value  || 'APA',
    };

    const res  = await fetch('/api/chat', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
    });
    const data = await res.json();
    removeTyping(typingId);

    if (data.error) {
      appendMessage('assistant', `⚠️ ${data.error}`);
    } else {
      currentSessionId = data.session_id;
      if (sessionTitle && data.message) {
        // update URL without reload
        history.replaceState({}, '', `/chat/${data.session_id}`);
      }
      appendMessage('assistant', data.message.content, data.message.msg_type, true);
    }
  } catch (e) {
    removeTyping(typingId);
    appendMessage('assistant', `⚠️ Network error: ${e.message}`);
  } finally {
    btnSend.disabled = false;
    userInput.focus();
  }
}

// ── Append bubble ────────────────────────────
function appendMessage(role, content, type = 'text', renderMd = false) {
  const wrap = document.createElement('div');
  wrap.className = `chat-bubble ${role} mb-4`;
  wrap.dataset.type = type;

  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const label = role === 'user'
    ? '<i class="bi bi-person-fill me-1"></i>You'
    : '<i class="bi bi-robot me-1"></i>ResearchAI';
  const badgeCls = role === 'user' ? 'bg-primary' : 'bg-secondary';

  const bodyHtml = (renderMd || role === 'assistant')
    ? renderMarkdown(content)
    : escapeHtml(content);

  wrap.innerHTML = `
    <div class="bubble-meta mb-1">
      <span class="badge ${badgeCls} me-2">${label}</span>
      <small class="text-muted">${now}</small>
      ${role === 'assistant' ? `<button class="btn btn-sm btn-link text-muted ms-2 copy-btn p-0" title="Copy"><i class="bi bi-clipboard"></i></button>` : ''}
    </div>
    <div class="bubble-content ${role === 'assistant' ? 'markdown-body' : ''}">${bodyHtml}</div>`;

  // Copy button
  wrap.querySelector('.copy-btn')?.addEventListener('click', () => {
    navigator.clipboard.writeText(content);
    wrap.querySelector('.copy-btn').innerHTML = '<i class="bi bi-clipboard-check text-success"></i>';
    setTimeout(() => { wrap.querySelector('.copy-btn').innerHTML = '<i class="bi bi-clipboard"></i>'; }, 2000);
  });

  chatMessages.appendChild(wrap);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ── Typing indicator ──────────────────────────
function showTyping() {
  const id = 'typing-' + Date.now();
  const el = document.createElement('div');
  el.id = id;
  el.className = 'chat-bubble assistant mb-4';
  el.innerHTML = `
    <div class="bubble-meta mb-1"><span class="badge bg-secondary"><i class="bi bi-robot me-1"></i>ResearchAI</span></div>
    <div class="bubble-content">
      <div class="typing-indicator"><span></span><span></span><span></span></div>
    </div>`;
  chatMessages.appendChild(el);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return id;
}

function removeTyping(id) {
  document.getElementById(id)?.remove();
}

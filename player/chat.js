// strudel-skills · chat client
//
// Vanilla SSE client for the embedded composing assistant. Talks to the
// server's /api/chat (agent stream) and /api/chat/auth (credential paste-in).
// No framework — matches the player's buildless static setup. The agent edits
// track files via tools; the player's own pollForChanges loop makes a
// write_track audible within ~700ms, so this client just streams + renders.

const $ = (id) => document.getElementById(id);
const el = {
  fab: $('chat-fab'),
  panel: $('chat-panel'),
  close: $('chat-close'),
  newBtn: $('chat-new'),
  dot: $('chat-dot'),
  context: $('chat-context'),
  auth: $('chat-auth'),
  token: $('chat-token'),
  tokenSave: $('chat-token-save'),
  log: $('chat-log'),
  status: $('chat-status'),
  form: $('chat-form'),
  input: $('chat-input'),
  send: $('chat-send'),
  stop: $('chat-stop'),
  trackSelect: $('track-select'),
};

// Conversation lives client-side and is replayed each turn; the server uses
// the last user message as the prompt and `resumeSessionId` for continuity.
// Session id is kept in memory only — a stale id from a previous server
// process would fail to resume, so we deliberately start fresh on reload.
let messages = [];
let resumeSessionId = null;
let pending = false;
let abortController = null;

// ── panel open / close ──────────────────────────────────
function openPanel() {
  el.panel.dataset.open = 'true';
  el.panel.setAttribute('aria-hidden', 'false');
  document.body.classList.add('chat-open');
  refreshAuth();
  updateContext();
  el.input.focus();
}
function closePanel() {
  el.panel.dataset.open = 'false';
  el.panel.setAttribute('aria-hidden', 'true');
  document.body.classList.remove('chat-open');
}

// ── current-track context ───────────────────────────────
function currentTrack() {
  const v = el.trackSelect && el.trackSelect.value;
  return v && /^[A-Za-z0-9][A-Za-z0-9_-]*$/.test(v) ? v : null;
}
function updateContext() {
  const t = currentTrack();
  el.context.textContent = t ? `editing · ${t}` : '';
}

// ── auth ────────────────────────────────────────────────
async function refreshAuth() {
  try {
    const s = await (await fetch('/api/chat/auth')).json();
    const connected = s.hasAuthToken || s.hasApiKey;
    el.dot.classList.toggle('live', connected);
    el.auth.hidden = connected;
    if (!s.binaryFound) {
      el.status.textContent = '⚠ claude binary not found on server';
    } else if (connected) {
      const src = s.authSource || s.apiKeySource || '';
      el.status.textContent = `● connected · ${src}${s.hint ? ' ·' + s.hint : ''}`;
    } else {
      el.status.textContent = 'not connected';
    }
  } catch {
    el.status.textContent = 'server unreachable';
  }
}
async function saveToken() {
  const token = el.token.value.trim();
  if (!token) return;
  el.tokenSave.disabled = true;
  try {
    await fetch('/api/chat/auth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ authToken: token }),
    });
    el.token.value = '';
    await refreshAuth();
  } finally {
    el.tokenSave.disabled = false;
  }
}

// ── rendering ───────────────────────────────────────────
function scrollDown() {
  el.log.scrollTop = el.log.scrollHeight;
}
function showEmpty() {
  el.log.innerHTML =
    '<div class="chat-empty">ask me to tweak the music — e.g. “make 03-surge’s bass darker”, “add a section to drift”, or “what does this track sound like?”. I read the file, make the change, and you hear it live.</div>';
}
function clearEmpty() {
  const e = el.log.querySelector('.chat-empty');
  if (e) e.remove();
}
function renderUser(text) {
  clearEmpty();
  const d = document.createElement('div');
  d.className = 'chat-msg user';
  d.textContent = text;
  el.log.appendChild(d);
  scrollDown();
}
function renderAssistantShell() {
  const wrap = document.createElement('div');
  wrap.className = 'chat-msg assistant';
  const text = document.createElement('div');
  text.className = 'chat-text';
  wrap.appendChild(text);
  el.log.appendChild(wrap);
  scrollDown();
  return { wrap, textEl: text };
}

const TOOL_GLYPH = { read: '↳', write: '✎', remove: '⚠', other: '·' };
function summarizeInput(input) {
  if (!input || typeof input !== 'object') return '';
  if (input.id && input.file) return `${input.id}/${input.file}`;
  if (input.id) return String(input.id);
  return '';
}
function renderToolCall(wrap, ev) {
  const chip = document.createElement('div');
  chip.className = `chat-tool tool-${ev.group || 'other'}`;
  chip.innerHTML =
    '<span class="chat-tool-glyph"></span>' +
    '<span class="chat-tool-name"></span>' +
    '<span class="chat-tool-arg"></span>' +
    '<span class="chat-tool-state">…</span>';
  chip.querySelector('.chat-tool-glyph').textContent = TOOL_GLYPH[ev.group] || '·';
  chip.querySelector('.chat-tool-name').textContent = ev.toolName || 'tool';
  chip.querySelector('.chat-tool-arg').textContent = summarizeInput(ev.input);
  wrap.appendChild(chip);
  scrollDown();
  return chip;
}
function markToolResult(chip, ev) {
  if (!chip) return;
  chip.classList.add(ev.isError ? 'err' : 'ok');
  const state = chip.querySelector('.chat-tool-state');
  if (ev.isError) {
    state.textContent = '✗';
    return;
  }
  const r = ev.result;
  let hint = '✓';
  if (r && typeof r === 'object') {
    if (r.live) hint = '✓ live';
    else if (r.file) hint = '✓ ' + r.file;
    else if (r.created) hint = '✓ new';
    else if (Array.isArray(r.tracks)) hint = `✓ ${r.tracks.length}`;
    else if (Array.isArray(r.sections)) hint = `✓ ${r.sections.length}`;
    else if (r.removed || r.removedLive) hint = '✓ removed';
  }
  state.textContent = hint;
  scrollDown();
}
function renderError(wrap, msg) {
  const d = document.createElement('div');
  d.className = 'chat-error';
  d.textContent = msg;
  (wrap || el.log).appendChild(d);
  scrollDown();
}

// ── composer state ──────────────────────────────────────
function setPending(p) {
  pending = p;
  el.send.hidden = p;
  el.stop.hidden = !p;
  el.input.disabled = p;
}
function autoGrow() {
  el.input.style.height = 'auto';
  el.input.style.height = Math.min(el.input.scrollHeight, 144) + 'px';
}

// ── send / stream ───────────────────────────────────────
async function send(text) {
  if (pending || !text.trim()) return;
  messages.push({ role: 'user', content: text });
  renderUser(text);
  el.input.value = '';
  autoGrow();
  const { wrap, textEl } = renderAssistantShell();
  setPending(true);
  abortController = new AbortController();

  let assistantText = '';
  const toolChips = new Map(); // tool_use id -> chip element

  const handleEvent = (ev) => {
    switch (ev.type) {
      case 'session':
        if (ev.sessionId) resumeSessionId = ev.sessionId;
        break;
      case 'text':
        if (typeof ev.text === 'string') {
          assistantText += ev.text;
          textEl.textContent = assistantText;
          scrollDown();
        }
        break;
      case 'tool_call':
        toolChips.set(ev.id, renderToolCall(wrap, ev));
        break;
      case 'tool_result':
        markToolResult(toolChips.get(ev.toolUseId), ev);
        updateContext(); // a write/remove may have changed the live track
        break;
      case 'assistant_error':
        renderError(wrap, typeof ev.error === 'string' ? ev.error : JSON.stringify(ev.error));
        break;
      case 'error':
        renderError(wrap, ev.message || 'stream error');
        break;
      case 'done':
        if (ev.usage) {
          const i = ev.usage.inputTokens || 0;
          const o = ev.usage.outputTokens || 0;
          const c = typeof ev.cost === 'number' ? ` · $${ev.cost.toFixed(4)}` : '';
          el.status.textContent = `${i}→${o} tok${c}`;
        }
        break;
    }
  };

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      signal: abortController.signal,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages,
        ...(resumeSessionId ? { resumeSessionId } : {}),
        context: { viewingTrack: currentTrack() || undefined },
      }),
    });
    if (!res.ok || !res.body) {
      let msg = `request failed (${res.status})`;
      try {
        const j = await res.json();
        if (j && j.error) msg = j.error;
      } catch {}
      renderError(wrap, msg);
      return;
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let idx;
      while ((idx = buffer.indexOf('\n\n')) !== -1) {
        const chunk = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);
        const payload = chunk
          .split('\n')
          .filter((l) => l.startsWith('data:'))
          .map((l) => l.slice(5).trimStart())
          .join('\n');
        if (!payload) continue;
        let ev;
        try {
          ev = JSON.parse(payload);
        } catch {
          continue;
        }
        handleEvent(ev);
      }
    }
    if (assistantText.trim()) messages.push({ role: 'assistant', content: assistantText });
  } catch (err) {
    if (err && err.name === 'AbortError') renderError(wrap, 'stopped');
    else renderError(wrap, err && err.message ? err.message : 'request failed');
  } finally {
    setPending(false);
    abortController = null;
    el.input.focus();
  }
}

function resetSession() {
  if (pending && abortController) abortController.abort();
  messages = [];
  resumeSessionId = null;
  showEmpty();
  refreshAuth();
}

// ── wiring ──────────────────────────────────────────────
el.fab.addEventListener('click', openPanel);
el.close.addEventListener('click', closePanel);
el.newBtn.addEventListener('click', resetSession);
el.tokenSave.addEventListener('click', saveToken);
el.form.addEventListener('submit', (e) => {
  e.preventDefault();
  send(el.input.value);
});
el.stop.addEventListener('click', () => abortController && abortController.abort());
el.input.addEventListener('input', autoGrow);

// Keep typing in the composer from triggering the player's window-level
// shortcuts (space = play/stop, letters = theme/etc.) — the player only
// guards <input>, not <textarea>, so stop propagation here.
el.input.addEventListener('keydown', (e) => {
  e.stopPropagation();
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    send(el.input.value);
  } else if (e.key === 'Escape') {
    e.preventDefault();
    closePanel();
  }
});
el.token.addEventListener('keydown', (e) => {
  e.stopPropagation();
  if (e.key === 'Enter') {
    e.preventDefault();
    saveToken();
  }
});

// A bare 'c' opens the chat. Skip when a modifier is held (Cmd+C / Ctrl+C is
// copy, Cmd+A select-all, etc.) or when typing in a field.
window.addEventListener('keydown', (e) => {
  if (e.key !== 'c' || e.metaKey || e.ctrlKey || e.altKey) return;
  if (el.panel.dataset.open === 'true') return;
  const t = e.target;
  if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT')) return;
  openPanel();
});

if (el.trackSelect) el.trackSelect.addEventListener('change', updateContext);

// Append text to the composer (used by shift-click note references), keeping
// any draft the user already typed and stacking multiple picks on new lines.
function insertIntoComposer(text) {
  const cur = el.input.value;
  el.input.value = cur && !/\s$/.test(cur) ? `${cur}\n${text}` : cur + text;
  autoGrow();
  el.input.focus();
  el.input.selectionStart = el.input.selectionEnd = el.input.value.length;
}

// Shift-click on a note in the player emits this — drop a reference to the
// exact track / segment / note into the composer so you can talk about it.
window.addEventListener('strudel:note-pick', (e) => {
  const d = e.detail || {};
  if (el.panel.dataset.open !== 'true') openPanel();
  const loc = [d.track, d.segment].filter(Boolean).join(' · ');
  let ref = 're: ';
  if (loc) ref += loc;
  if (d.line) ref += ` · line ${d.line}`;
  if (d.text) ref += ` · \`${d.text}\``;
  const extra = [];
  if (d.note && d.note !== d.text) extra.push(`note ${d.note}`);
  if (d.instrument) extra.push(d.instrument);
  if (extra.length) ref += ` (${extra.join(', ')})`;
  ref += ' — ';
  insertIntoComposer(ref);
});

showEmpty();
refreshAuth();

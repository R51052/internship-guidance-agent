import { api, el, icon, listFrom, setStatus, text } from './api.js';
import { requireAuth } from './auth.js';

const log = document.getElementById('chat-log');
const form = document.getElementById('chat-form');
const input = document.getElementById('message');
const send = document.getElementById('send-message');
const status = document.getElementById('chat-status');
const welcome = document.getElementById('chat-welcome');
const welcomeTemplate = welcome.cloneNode(true);
const selectedId = new URLSearchParams(location.search).get('internship_id');
let roleIds = [];
let busy = false;
let ready = false;
let historyKey = '';
let history = [];

function scrollToLatest() { log.scrollTop = log.scrollHeight; }
function persistHistory() {
  if (!historyKey) return;
  try { localStorage.setItem(historyKey, JSON.stringify(history.slice(-40))); } catch { /* Storage may be unavailable. */ }
}
function addMessage(role, message, { persist = true } = {}) {
  document.getElementById('chat-welcome')?.remove();
  const row = el('article', `message ${role}`); row.setAttribute('aria-label', role === 'user' ? 'You' : 'Assistant');
  const avatar = el('span', 'message-avatar');
  if (role === 'user') avatar.textContent = 'YOU'; else avatar.append(icon('sparkles'));
  avatar.setAttribute('aria-hidden', 'true');
  const body = el('div', 'message-body', message);
  row.append(avatar, body); log.append(row); scrollToLatest();
  if (persist && (role === 'user' || role === 'assistant')) {
    history.push({ role, message }); persistHistory();
  }
  return { row, body };
}
function restoreHistory() {
  try { history = JSON.parse(localStorage.getItem(historyKey) || '[]'); } catch { history = []; }
  if (!Array.isArray(history)) history = [];
  history.forEach(item => {
    if (item && (item.role === 'user' || item.role === 'assistant') && typeof item.message === 'string') {
      addMessage(item.role, item.message, { persist: false });
    }
  });
}
function bindSuggestions(root) {
  root.querySelectorAll('[data-prompt]').forEach(button => button.addEventListener('click', () => {
    if (busy || !ready) return;
    input.value = button.dataset.prompt; form.requestSubmit();
  }));
}
function setBusy(value) {
  busy = value; send.disabled = value || !ready; input.disabled = value || !ready;
  document.getElementById('clear-chat').disabled = value;
  log.setAttribute('aria-busy', String(value));
}
form.addEventListener('submit', async event => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message || busy || !ready) return;
  if (message.length > 4000) { setStatus(status, 'Please keep your message to 4,000 characters.'); return; }
  setStatus(status); addMessage('user', message); input.value = ''; setBusy(true);
  const pending = addMessage('assistant', 'Looking into your question…');
  pending.row.setAttribute('role', 'status');
  try {
    const response = await api.chat({ message, internship_ids: roleIds });
    const answer = response.answer || response.message;
    if (typeof answer !== 'string' || !answer.trim()) throw new Error('The assistant returned an empty response. Please try again.');
    pending.row.removeAttribute('role');
    pending.body.textContent = answer;
    const sources = listFrom(response, ['recommendations']);
    if (sources.length) {
      const links = el('div', 'message-sources'); links.append(el('strong', '', 'Explore the roles mentioned'));
      sources.slice(0, 5).forEach(value => {
        const item = value.internship || value;
        if (!item.id) return;
        const link = el('a', '', `${text(item.title)} · ${text(item.company)}`); link.href = `internship-details.html?id=${encodeURIComponent(item.id)}`; links.append(link);
      }); pending.body.append(links);
    }
    const mode = response.mock || response.mode === 'mock' ? 'Mock assistant · database-backed demo guidance' : response.mode === 'openai' ? 'OpenAI guidance grounded in the internship catalog' : response.mode === 'gemini' ? 'Gemini guidance grounded in the internship catalog' : 'Guidance based on available data';
    document.getElementById('assistant-mode').textContent = `${mode}${response.is_demo ? ' · demo data' : ''}`;
    if (response.warning) setStatus(status, `${response.warning} The reply uses fallback guidance.`, 'info');
  } catch (error) {
    pending.row.remove();
    setStatus(status, error.message);
    input.value = message;
  } finally { setBusy(false); input.focus(); scrollToLatest(); }
});
input.addEventListener('keydown', event => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); form.requestSubmit(); }
});
document.getElementById('clear-chat').addEventListener('click', () => {
  if (busy) return;
  history = []; persistHistory();
  const fresh = welcomeTemplate.cloneNode(true); log.replaceChildren(fresh); bindSuggestions(fresh); setStatus(status); input.value = ''; input.focus();
});
bindSuggestions(welcome);
async function init() {
  if (!await requireAuth()) return;
  try {
    const user = await api.me();
    historyKey = `internpath_chat_${user.id}`;
    restoreHistory();
    const profile = await api.profile();
    document.getElementById('context-skills').textContent = profile.skills?.length ? profile.skills.join(', ') : 'Not specified';
    document.getElementById('context-interests').textContent = profile.interests?.length ? profile.interests.join(', ') : 'Not specified';
  } catch (error) { setStatus(document.getElementById('page-status'), `Profile context could not be loaded. ${error.message}`); }
  if (selectedId) {
    try {
      const role = await api.internship(selectedId); roleIds = [role.id];
      document.getElementById('context-role').textContent = `${text(role.title)} · ${text(role.company)}`;
      document.getElementById('selected-role-context').hidden = false;
    } catch (error) { setStatus(document.getElementById('page-status'), `The selected role could not be loaded. ${error.message}`); }
  }
  ready = true; setBusy(false);
}
init();

// The API origin can be changed using <meta name="api-base-url" content="…">.
export const API_BASE = (document.querySelector('meta[name="api-base-url"]')?.content || 'http://localhost:8000').replace(/\/$/, '');
const TOKEN_KEY = 'internpath_access_token';
export const tokenStore = {
  get() { try { return localStorage.getItem(TOKEN_KEY); } catch { return null; } },
  set(value) { localStorage.setItem(TOKEN_KEY, value); },
  clear() { try { localStorage.removeItem(TOKEN_KEY); } catch { /* Storage may be unavailable. */ } }
};

export class APIError extends Error {
  constructor(message, status = 0) { super(message); this.name = 'APIError'; this.status = status; }
}

function errorMessage(body, fallback) {
  if (typeof body?.detail === 'string') return body.detail;
  if (Array.isArray(body?.detail)) return body.detail.map(item => `${item.loc?.slice(1).join(' ') || 'Input'}: ${item.msg}`).join('; ');
  return body?.message || fallback;
}

export async function request(path, { method = 'GET', body, signal, authenticated = true } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 30000);
  const abort = () => controller.abort();
  signal?.addEventListener('abort', abort, { once: true });
  if (signal?.aborted) controller.abort();
  const headers = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  const token = authenticated ? tokenStore.get() : null;
  if (token) headers.Authorization = `Bearer ${token}`;
  try {
    const response = await fetch(`${API_BASE}/api${path}`, {
      method, headers, signal: controller.signal,
      ...(body === undefined ? {} : { body: JSON.stringify(body) })
    });
    let data = null;
    if (response.status !== 204) {
      const text = await response.text();
      try { data = text ? JSON.parse(text) : null; }
      catch { throw new APIError('The server returned an unexpected response. Please try again.', response.status); }
    }
    if (!response.ok) {
      if (response.status === 401 && authenticated) {
        tokenStore.clear();
        if (!['login', 'register', 'home'].includes(document.body.dataset.page)) {
          const next = `${location.pathname.split('/').pop()}${location.search}`;
          location.replace(`login.html?reason=expired&next=${encodeURIComponent(next)}`);
        }
      }
      throw new APIError(errorMessage(data, `Request failed (${response.status}). Please try again.`), response.status);
    }
    return data;
  } catch (error) {
    if (error instanceof APIError) throw error;
    if (signal?.aborted) throw new DOMException('Request cancelled', 'AbortError');
    if (controller.signal.aborted) throw new APIError('The request took too long. Please try again.');
    throw new APIError(`Unable to reach the API at ${API_BASE}. Check that the backend is running and try again.`);
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener('abort', abort);
  }
}

const queryString = params => {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params || {})) {
    if (value !== '' && value !== null && value !== undefined) query.set(key, String(value));
  }
  return query.size ? `?${query}` : '';
};

export const api = {
  register: body => request('/auth/register', { method: 'POST', body, authenticated: false }),
  login: body => request('/auth/login', { method: 'POST', body, authenticated: false }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  me: () => request('/auth/me'),
  profile: () => request('/profile'),
  saveProfile: body => request('/profile', { method: 'PUT', body }),
  internships: (params, signal) => request(`/internships${queryString(params)}`, { signal }),
  internship: id => request(`/internships/${encodeURIComponent(id)}`),
  recommendations: (params, signal) => request(`/recommendations${queryString(params)}`, { signal }),
  favorites: () => request('/favorites'),
  addFavorite: id => request('/favorites', { method: 'POST', body: { internship_id: id } }),
  removeFavorite: id => request(`/favorites/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  chat: body => request('/agent/chat', { method: 'POST', body })
};

const paths = {
  arrow: '<path d="M5 12h14m-6-6 6 6-6 6"/>', back: '<path d="m12 5-7 7 7 7M5 12h14"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4.5 4.5"/>',
  bookmark: '<path d="M6 4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v17l-6-4-6 4Z"/>',
  sparkles: '<path d="m12 3 2.3 6.7L21 12l-6.7 2.3L12 21l-2.3-6.7L3 12l6.7-2.3ZM20 3v4m-2-2h4"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/>',
  logout: '<path d="M9 5H4v14h5m5-14 7 7-7 7m-6-7h13"/>',
  pin: '<path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z"/><circle cx="12" cy="10" r="2"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  briefcase: '<rect x="3" y="7" width="18" height="14" rx="2"/><path d="M8 7V3h8v4M3 12a20 20 0 0 0 18 0m-9 0v3"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  shield: '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6Z"/><path d="m8 12 3 3 5-6"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  close: '<path d="m6 6 12 12M6 18 18 6"/>',
  send: '<path d="m22 2-7 20-4-9L2 9Zm0 0L11 13"/>',
  book: '<path d="M12 5c-3-3-7-3-10-2v16c3-1 7-1 10 2 3-3 7-3 10-2V3c-3-1-7-1-10 2Zm0 0v16"/>',
  chevron: '<path d="m9 5 7 7-7 7"/>',
  external: '<path d="M14 3h7v7m0-7L10 14m0-10H4v16h16v-6"/>',
  mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 6 9 7 9-7"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v.1"/>',
  target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
  edit: '<path d="m16 3 5 5-12 12-6 1 1-6Zm-2 2 5 5"/>',
  compass: '<circle cx="12" cy="12" r="9"/><path d="m16 8-2 6-6 2 2-6Z"/>',
  calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4m10-4v4M3 11h18"/>'
};
export function icon(name, extra = '') {
  const wrapper = document.createElement('span');
  wrapper.innerHTML = `<svg class="icon ${extra}" viewBox="0 0 24 24" aria-hidden="true">${paths[name] || paths.sparkles}</svg>`;
  return wrapper.firstElementChild;
}
export function hydrateIcons(root = document) {
  root.querySelectorAll('[data-icon]').forEach(node => node.replaceChildren(icon(node.dataset.icon)));
}
export function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
export function setStatus(node, message = '', type = 'error') {
  if (!node) return;
  node.hidden = !message;
  node.className = `status ${type === 'error' ? '' : type}`;
  node.textContent = message;
}
export function loading(container, label = 'Loading…') {
  const loader = el('div', 'loading');
  loader.setAttribute('role', 'status');
  loader.append(el('span', 'spinner'), el('span', '', label));
  container.replaceChildren(loader);
}
export function empty(container, title, description, { href, label, iconName = 'search', retry } = {}) {
  const state = el('div', 'empty-state panel');
  const symbol = el('div', 'empty-icon'); symbol.append(icon(iconName));
  state.append(symbol, el('h3', '', title), el('p', '', description));
  if (href) { const link = el('a', 'btn btn-primary btn-small', label || 'Get started'); link.href = href; state.append(link); }
  if (retry) { const button = el('button', 'btn btn-secondary btn-small', 'Try again'); button.type = 'button'; button.addEventListener('click', retry); state.append(button); }
  container.replaceChildren(state);
}
export function toast(message, isError = false) {
  let region = document.querySelector('.toast-region');
  if (!region) { region = el('div', 'toast-region'); region.setAttribute('aria-live', 'polite'); document.body.append(region); }
  const notice = el('div', `toast${isError ? ' error' : ''}`, message);
  region.append(notice);
  setTimeout(() => notice.remove(), 6000);
}
export function listFrom(data, keys = ['items', 'internships', 'recommendations', 'favorites']) {
  if (Array.isArray(data)) return data;
  for (const key of keys) if (Array.isArray(data?.[key])) return data[key];
  return [];
}
export const unwrap = value => value?.internship || value;
export const text = value => value === undefined || value === null || value === '' ? 'Not specified' : String(value);
export const workMode = value => ({ remote: 'Remote', hybrid: 'Hybrid', onsite: 'On-site', any: 'Any work mode' }[value] || text(value));
export function dateText(value) {
  if (!value) return 'Not specified';
  const date = new Date(`${String(value).slice(0, 10)}T12:00:00`);
  return Number.isNaN(date.getTime()) ? 'Unable to verify' : new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short', year: 'numeric' }).format(date);
}
export function stipendText(item) {
  if (item.stipend === undefined || item.stipend === null) return 'Stipend not specified';
  const amount = Number(item.stipend);
  if (!Number.isFinite(amount)) return 'Stipend unable to verify';
  let formatted;
  try {
    formatted = item.currency ? new Intl.NumberFormat(undefined, { style: 'currency', currency: item.currency, maximumFractionDigits: 0 }).format(amount) : `${amount.toLocaleString()} · currency not specified`;
  } catch { formatted = `${amount.toLocaleString()} · currency unable to verify`; }
  return `${formatted}${item.stipend_period === 'month' ? ' / month' : item.stipend_period === 'total' ? ' total' : ' · period not specified'}`;
}
export function safeURL(value) {
  try { const url = new URL(value); return ['https:', 'http:'].includes(url.protocol) ? url.href : null; } catch { return null; }
}
export function internshipCard(match, { saved = false, onSave } = {}) {
  const item = unwrap(match);
  const card = el('article', 'internship-card');
  const top = el('div', 'card-top');
  const avatar = el('div', 'company-avatar', (item.company || '?').trim().charAt(0).toUpperCase());
  avatar.setAttribute('aria-hidden', 'true');
  top.append(avatar);
  if (onSave) {
    const save = el('button', 'save-btn'); save.type = 'button';
    save.setAttribute('aria-pressed', String(saved));
    const setLabel = isSaved => save.setAttribute('aria-label', `${isSaved ? 'Remove' : 'Save'} ${text(item.title)}${isSaved ? ' from favorites' : ' to favorites'}`);
    setLabel(saved); save.append(icon('bookmark'));
    save.addEventListener('click', async () => {
      save.disabled = true;
      try { const next = await onSave(item, save.getAttribute('aria-pressed') === 'true'); save.setAttribute('aria-pressed', String(next)); setLabel(next); }
      catch (error) { toast(error.message, true); }
      finally { save.disabled = false; }
    });
    top.append(save);
  }
  card.append(top);
  if (Number.isFinite(match.match_score ?? match.score)) {
    const row = el('div', 'match-row');
    const label = el('span', 'flex'); label.append(icon('sparkles'), document.createTextNode(`${Math.round(match.match_score ?? match.score)}% match`));
    row.append(label);
    if (match.eligible === false) row.append(el('span', 'muted', 'Check eligibility'));
    card.append(row);
  }
  const heading = el('h3'); const link = el('a', '', text(item.title));
  link.href = `internship-details.html?id=${encodeURIComponent(item.id)}`; heading.append(link);
  card.append(heading, el('p', 'company-name', text(item.company)));
  const meta = el('div', 'card-meta');
  for (const [symbol, value] of [['pin', item.work_mode === 'remote' ? 'Remote' : text(item.location)], ['clock', item.duration_months ? `${item.duration_months} months` : 'Duration not specified']]) {
    const node = el('span'); node.append(icon(symbol), document.createTextNode(value)); meta.append(node);
  }
  card.append(meta);
  const tags = el('div', 'tag-row');
  if (item.domain) tags.append(el('span', 'pill pill-purple', item.domain));
  if (item.work_mode) tags.append(el('span', 'pill', workMode(item.work_mode)));
  if (item.is_demo) tags.append(el('span', 'pill', 'Demo listing'));
  card.append(tags);
  const footer = el('div', 'card-bottom');
  const detail = el('a', 'btn btn-soft', 'View role'); detail.href = link.href; detail.append(icon('arrow'));
  footer.append(el('span', 'stipend', stipendText(item)), detail); card.append(footer);
  return card;
}
export function profileCompletion(profile = {}) {
  const fields = ['full_name', 'education', 'degree', 'year', 'cgpa', 'skills', 'interests', 'preferred_locations', 'available_from'];
  return Math.round(fields.filter(key => Array.isArray(profile[key]) ? profile[key].length : profile[key] !== null && profile[key] !== undefined && profile[key] !== '').length / fields.length * 100);
}
hydrateIcons();

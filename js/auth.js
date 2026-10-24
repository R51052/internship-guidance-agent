import { api, tokenStore, el, icon, hydrateIcons, setStatus } from './api.js';

const pageTitles = { dashboard: 'Dashboard', recommendations: 'Discover internships', details: 'Internship details', assistant: 'AI assistant', favorites: 'Saved internships' };
export function renderShell(user) {
  const chrome = document.getElementById('app-chrome');
  if (!chrome) return;
  const page = document.body.dataset.page;
  const sidebar = el('aside', 'sidebar'); sidebar.id = 'sidebar'; sidebar.setAttribute('aria-label', 'Main navigation');
  const brand = el('a', 'brand'); brand.href = 'dashboard.html';
  const mark = el('span', 'brand-mark'); mark.append(icon('compass')); brand.append(mark, document.createTextNode('internpath'), el('span', 'brand-dot', '.'));
  sidebar.append(brand, el('div', 'nav-label', 'Your workspace'));
  const nav = el('nav', 'side-nav'); nav.setAttribute('aria-label', 'Workspace');
  const links = [['dashboard', 'grid', 'Overview', 'dashboard.html'], ['recommendations', 'search', 'Discover internships', 'recommendations.html'], ['favorites', 'bookmark', 'Saved internships', 'favorites.html'], ['assistant', 'sparkles', 'AI assistant', 'ai-assistant.html']];
  for (const [key, symbol, label, href] of links) {
    const anchor = el('a', `nav-link${page === key ? ' active' : ''}`); anchor.href = href;
    if (page === key) anchor.setAttribute('aria-current', 'page');
    anchor.append(icon(symbol), document.createTextNode(label)); nav.append(anchor);
  }
  sidebar.append(nav);
  const profileLink = el('a', 'nav-link'); profileLink.href = 'dashboard.html#profile'; profileLink.append(icon('user'), document.createTextNode('My profile'));
  sidebar.append(el('div', 'nav-label', 'Personal'), profileLink);
  const bottom = el('div', 'sidebar-bottom');
  const note = el('div', 'sidebar-note'); note.append(el('strong', '', 'A little guidance goes a long way.'), document.createTextNode('Find your next step with your personal internship assistant.'));
  const assistantLink = el('a', '', 'Let’s talk'); assistantLink.href = 'ai-assistant.html'; assistantLink.append(icon('arrow')); note.append(assistantLink);
  const logout = el('button', 'logout'); logout.type = 'button'; logout.append(icon('logout'), document.createTextNode('Log out'));
  logout.addEventListener('click', async () => {
    logout.disabled = true;
    let reason = 'logout';
    try { await api.logout(); } catch { reason = 'local-logout'; }
    finally { tokenStore.clear(); location.replace(`login.html?reason=${reason}`); }
  });
  bottom.append(note, logout); sidebar.append(bottom);
  const overlay = el('div', 'mobile-overlay'); overlay.setAttribute('aria-hidden', 'true');
  const topbar = el('header', 'app-topbar');
  const menu = el('button', 'mobile-toggle'); menu.type = 'button'; menu.setAttribute('aria-label', 'Open navigation'); menu.setAttribute('aria-expanded', 'false'); menu.setAttribute('aria-controls', 'sidebar'); menu.append(icon('menu'));
  const mobile = matchMedia('(max-width:800px)');
  sidebar.inert = mobile.matches;
  const close = () => { sidebar.classList.remove('open'); sidebar.inert = mobile.matches; overlay.classList.remove('visible'); menu.setAttribute('aria-expanded', 'false'); menu.setAttribute('aria-label', 'Open navigation'); };
  menu.addEventListener('click', () => {
    const open = sidebar.classList.toggle('open'); sidebar.inert = !open && mobile.matches;
    overlay.classList.toggle('visible', open); menu.setAttribute('aria-expanded', String(open)); menu.setAttribute('aria-label', `${open ? 'Close' : 'Open'} navigation`);
    if (open) sidebar.querySelector('a').focus();
  });
  mobile.addEventListener('change', close);
  overlay.addEventListener('click', () => { close(); menu.focus(); });
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && sidebar.classList.contains('open')) { close(); menu.focus(); } });
  sidebar.addEventListener('keydown', event => {
    if (event.key !== 'Tab' || !mobile.matches || !sidebar.classList.contains('open')) return;
    const targets = [...sidebar.querySelectorAll('a, button:not(:disabled)')];
    const first = targets[0], last = targets[targets.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  });
  sidebar.addEventListener('click', event => { if (event.target.closest('a')) close(); });
  const crumbs = el('div', 'breadcrumbs'); crumbs.append(el('span', '', 'Workspace'), icon('chevron'), el('strong', '', pageTitles[page] || 'Internpath'));
  const identity = el('a', 'topbar-profile'); identity.href = 'dashboard.html#profile'; identity.setAttribute('aria-label', 'View your profile');
  const name = user?.name || user?.full_name || 'Your account';
  const initials = name.split(/\s+/).filter(Boolean).slice(0, 2).map(part => part.charAt(0).toUpperCase()).join('');
  const info = el('div', 'topbar-profile-info'); info.append(el('div', 'topbar-profile-name', name), el('div', 'topbar-profile-label', 'Your next chapter starts here'));
  identity.append(el('span', 'avatar', initials || 'U'), info); topbar.append(menu, crumbs, identity);
  chrome.replaceChildren(sidebar, overlay, topbar);
  hydrateIcons();
}

export async function requireAuth() {
  if (!tokenStore.get()) {
    const next = `${location.pathname.split('/').pop()}${location.search}${location.hash}`;
    location.replace(`login.html?next=${encodeURIComponent(next)}`); return null;
  }
  try {
    const user = await api.me(); renderShell(user.user || user); return user.user || user;
  } catch (error) {
    if (error.status === 401) return null;
    renderShell(null);
    const status = document.getElementById('page-status');
    setStatus(status, error.message);
    const retry = el('button', 'btn btn-secondary btn-small', 'Try again'); retry.type = 'button'; retry.style.marginLeft = '12px'; retry.addEventListener('click', () => location.reload()); status?.append(retry);
    document.querySelectorAll('.loading').forEach(loader => { loader.textContent = 'Unable to load. Please try again.'; });
    return null;
  }
}

function safeNext() {
  const next = new URLSearchParams(location.search).get('next') || 'dashboard.html';
  return /^(dashboard|recommendations|internship-details|ai-assistant|favorites)\.html(?:[?#].*)?$/.test(next) ? next : 'dashboard.html';
}
function storeSession(response) {
  if (!response?.access_token) throw new Error('The server did not return an access token. Please try logging in.');
  tokenStore.set(response.access_token);
}

async function initAuth() {
  const form = document.getElementById('auth-form');
  if (!form) return;
  const page = document.body.dataset.page;
  const status = document.getElementById('auth-status');
  const submit = form.querySelector('[type="submit"]');
  const initialLabel = submit.textContent;
  const params = new URLSearchParams(location.search);
  if (params.get('reason') === 'expired') setStatus(status, 'Your session has expired. Please log in again.', 'info');
  if (params.get('reason') === 'logout') setStatus(status, 'You have been logged out.', 'success');
  if (params.get('reason') === 'local-logout') setStatus(status, 'You are logged out of this browser. The server session could not be revoked and will expire automatically.', 'info');
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const data = new FormData(form);
    if (page === 'register' && data.get('password') !== data.get('confirm_password')) {
      setStatus(status, 'Your passwords do not match. Please check them and try again.');
      form.elements.confirm_password.focus(); return;
    }
    submit.disabled = true; submit.textContent = page === 'register' ? 'Creating account…' : 'Logging in…'; setStatus(status);
    try {
      const body = { email: data.get('email').trim(), password: data.get('password') };
      if (page === 'register') body.name = data.get('name').trim();
      const result = await (page === 'register' ? api.register(body) : api.login(body));
      // Some registration endpoints return a user rather than signing in automatically.
      const session = result?.access_token ? result : page === 'register' ? await api.login({ email: body.email, password: body.password }) : result;
      storeSession(session);
      form.reset(); location.assign(safeNext());
    } catch (error) { setStatus(status, error.message); }
    finally { submit.disabled = false; submit.textContent = initialLabel; }
  });
  document.querySelectorAll('[data-toggle-password]').forEach(button => {
    button.addEventListener('click', () => {
      const input = document.getElementById(button.dataset.togglePassword);
      input.type = input.type === 'password' ? 'text' : 'password';
      button.textContent = input.type === 'password' ? 'Show' : 'Hide';
      button.setAttribute('aria-label', `${input.type === 'password' ? 'Show' : 'Hide'} password`);
    });
  });
}
initAuth();

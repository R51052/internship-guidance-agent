import { api, el, empty, internshipCard, listFrom, loading, setStatus, toast, unwrap } from './api.js';
import { requireAuth } from './auth.js';

const form = document.getElementById('filter-form');
const results = document.getElementById('recommendations-results');
const count = document.getElementById('results-count');
const sort = document.getElementById('sort');
const pagination = document.getElementById('pagination');
const PAGE_SIZE = 9;
let matches = [];
let filtered = [];
let page = 1;
let ready = false;
let favoritesAvailable = false;
const savedIds = new Set();

async function save(item, alreadySaved) {
  await (alreadySaved ? api.removeFavorite(item.id) : api.addFavorite(item.id));
  alreadySaved ? savedIds.delete(item.id) : savedIds.add(item.id);
  toast(alreadySaved ? 'Removed from your shortlist.' : 'Added to your shortlist.');
  return !alreadySaved;
}
function numeric(value, fallback = Infinity) { const result = Number(value); return value !== null && value !== undefined && Number.isFinite(result) ? result : fallback; }
function monthly(item) { return numeric(item.stipend, -Infinity) / (item.stipend_period === 'total' ? numeric(item.duration_months, 1) : 1); }
function applyFilters() {
  if (!ready) return;
  const data = new FormData(form);
  const query = data.get('query').trim().toLocaleLowerCase();
  const locationQuery = data.get('location').trim().toLocaleLowerCase();
  const mode = data.get('work_mode');
  const stipend = Number(data.get('min_stipend') || 0);
  filtered = matches.filter(match => {
    const item = unwrap(match);
    const searchable = [item.title, item.company, item.domain, item.description, ...(item.skills_required || [])].join(' ').toLocaleLowerCase();
    return (!query || searchable.includes(query)) && (!locationQuery || (item.location || '').toLocaleLowerCase().includes(locationQuery)) && (!mode || item.work_mode === mode) && (stipend <= 0 || monthly(item) >= stipend);
  });
  filtered.sort((a, b) => {
    const left = unwrap(a), right = unwrap(b);
    if (sort.value === 'stipend-desc') return monthly(right) - monthly(left);
    if (sort.value === 'deadline') return (left.application_deadline || '9999').localeCompare(right.application_deadline || '9999');
    if (sort.value === 'duration') return numeric(left.duration_months) - numeric(right.duration_months);
    if (sort.value === 'title') return (left.title || '').localeCompare(right.title || '');
    return numeric(b.match_score ?? b.score, 0) - numeric(a.match_score ?? a.score, 0);
  });
  const params = new URLSearchParams();
  for (const [name, value] of data) if (String(value).trim()) params.set(name, String(value).trim());
  if (sort.value !== 'match') params.set('sort', sort.value);
  history.replaceState(null, '', `${location.pathname}${params.size ? `?${params}` : ''}`);
  page = 1; render();
}
function render() {
  count.textContent = `${filtered.length} ${filtered.length === 1 ? 'opportunity' : 'opportunities'} for your next chapter`;
  if (!filtered.length) {
    pagination.hidden = true;
    empty(results, matches.length ? 'A different direction might help.' : 'No eligible matches yet.', matches.length ? 'Try a broader search or clear your filters. Your next possibility may be just outside these preferences.' : 'Complete your degree, study year, and skills in your profile. The current catalog may not include an eligible role for you yet.', { href: matches.length ? undefined : 'dashboard.html#profile', label: 'Update my profile', iconName: 'compass' });
    return;
  }
  const grid = el('div', 'internship-grid results-grid');
  filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE).forEach(match => grid.append(internshipCard(match, { saved: savedIds.has(unwrap(match).id), onSave: favoritesAvailable ? save : undefined })));
  results.replaceChildren(grid);
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  pagination.hidden = totalPages <= 1;
  document.getElementById('page-number').textContent = `Page ${page} of ${totalPages}`;
  document.getElementById('previous-page').disabled = page <= 1;
  document.getElementById('next-page').disabled = page >= totalPages;
}
async function load() {
  ready = false; pagination.hidden = true;
  loading(results, 'Looking for possibilities that fit you…');
  count.textContent = 'Finding your possibilities…';
  try {
    // Fetch every API page before applying local filters and sort, so all matches are searchable.
    const first = await api.recommendations({ limit: 100, offset: 0 });
    matches = listFrom(first);
    const total = first.total ?? matches.length;
    while (matches.length < total) {
      const next = await api.recommendations({ limit: 100, offset: matches.length });
      const items = listFrom(next);
      if (!items.length) break;
      matches.push(...items);
    }
    ready = true; applyFilters();
  } catch (error) {
    count.textContent = 'Recommendations unavailable';
    empty(results, 'We couldn’t load your opportunities.', error.message, { retry: load });
  }
}
form.addEventListener('submit', event => { event.preventDefault(); if (form.reportValidity()) applyFilters(); });
sort.addEventListener('change', applyFilters);
document.getElementById('reset-filters').addEventListener('click', () => { form.reset(); sort.value = 'match'; applyFilters(); });
for (const [id, delta] of [['previous-page', -1], ['next-page', 1]]) document.getElementById(id).addEventListener('click', () => { page += delta; render(); results.scrollIntoView({ behavior: 'smooth', block: 'start' }); });
async function init() {
  if (!await requireAuth()) return;
  const params = new URLSearchParams(location.search);
  for (const name of ['query', 'location', 'work_mode', 'min_stipend']) if (params.has(name)) form.elements.namedItem(name).value = params.get(name);
  if ([...sort.options].some(option => option.value === params.get('sort'))) sort.value = params.get('sort');
  try {
    listFrom(await api.favorites(), ['favorites']).forEach(item => savedIds.add(item.internship_id || item.internship?.id));
    favoritesAvailable = true;
  }
  catch (error) { setStatus(document.getElementById('page-status'), `We couldn’t check your saved roles. ${error.message}`); }
  await load();
}
init();

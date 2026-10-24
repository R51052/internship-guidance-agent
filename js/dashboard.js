import { api, el, empty, internshipCard, listFrom, loading, setStatus, toast } from './api.js';
import { requireAuth } from './auth.js';
import { initProfileForm, renderProfileSummary } from './profile.js';

const results = document.getElementById('dashboard-results');
const savedIds = new Set();
let favoritesAvailable = false;
async function toggleFavorite(item, saved) {
  await (saved ? api.removeFavorite(item.id) : api.addFavorite(item.id));
  saved ? savedIds.delete(item.id) : savedIds.add(item.id);
  document.getElementById('favorites-count').textContent = savedIds.size;
  toast(saved ? 'Removed from your shortlist.' : 'Saved to your shortlist.');
  return !saved;
}
async function loadMatches() {
  loading(results, 'Finding your matches…');
  try {
    const data = await api.recommendations({ limit: 4 });
    const matches = listFrom(data);
    document.getElementById('matches-count').textContent = data.total ?? matches.length;
    if (!matches.length) {
      empty(results, 'Your next chapter is still taking shape.', 'Add your degree, year of study, and skills to your profile. There may not be eligible roles in the current catalog yet.', { href: '#profile', label: 'Complete my profile', iconName: 'compass' }); return;
    }
    const grid = el('div', 'internship-grid');
    matches.forEach(match => grid.append(internshipCard(match, { saved: savedIds.has(match.internship.id), onSave: favoritesAvailable ? toggleFavorite : undefined })));
    results.replaceChildren(grid);
  } catch (error) {
    document.getElementById('matches-count').textContent = '—';
    empty(results, 'We couldn’t load your matches.', error.message, { retry: loadMatches });
  }
}
async function init() {
  const user = await requireAuth();
  if (!user) return;
  const firstName = (user.name || '').trim().split(/\s+/)[0];
  document.getElementById('greeting').textContent = firstName ? `Good to see you, ${firstName}.` : 'Welcome to your next chapter.';
  const [profileResult, favoritesResult] = await Promise.allSettled([api.profile(), api.favorites()]);
  const errors = [];
  if (favoritesResult.status === 'fulfilled') {
    favoritesAvailable = true;
    listFrom(favoritesResult.value, ['favorites']).forEach(favorite => savedIds.add(favorite.internship_id || favorite.internship?.id));
    document.getElementById('favorites-count').textContent = savedIds.size;
  } else errors.push(`Saved roles: ${favoritesResult.reason.message}`);
  if (profileResult.status === 'fulfilled') {
    const profile = profileResult.value.profile || profileResult.value;
    renderProfileSummary(profile); initProfileForm(profile, loadMatches);
  } else {
    errors.push(`Profile: ${profileResult.reason.message}`);
    setStatus(document.getElementById('profile-status'), 'Unable to load your profile. Refresh the page to try again.');
  }
  if (errors.length) setStatus(document.getElementById('page-status'), errors.join(' '));
  await loadMatches();
}
init();

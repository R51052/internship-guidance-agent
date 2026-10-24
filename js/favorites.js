import { api, el, empty, internshipCard, listFrom, loading, toast } from './api.js';
import { requireAuth } from './auth.js';

const results = document.getElementById('favorites-results');
const count = document.getElementById('favorites-count');
let favorites = [];
function render() {
  count.textContent = `${favorites.length} saved ${favorites.length === 1 ? 'opportunity' : 'opportunities'}`;
  if (!favorites.length) {
    empty(results, 'Make room for possibility.', 'When a role catches your eye, tap the bookmark to keep it here. Your shortlist is a good place to start your next chapter.', { href: 'recommendations.html', label: 'Find my first opportunity', iconName: 'bookmark' }); return;
  }
  const grid = el('div', 'internship-grid results-grid');
  favorites.forEach(favorite => {
    const id = favorite.internship_id || favorite.internship?.id;
    if (favorite.unavailable || !favorite.internship) {
      const missing = el('article', 'internship-card stack');
      const remove = el('button', 'btn btn-secondary btn-small', 'Remove from saved'); remove.type = 'button';
      remove.addEventListener('click', async () => {
        remove.disabled = true;
        try { await api.removeFavorite(id); favorites = favorites.filter(item => (item.internship_id || item.internship?.id) !== id); render(); toast('Removed unavailable listing.'); }
        catch (error) { toast(error.message, true); remove.disabled = false; }
      });
      missing.append(el('span', 'pill', 'Unavailable'), el('h3', '', 'This listing is no longer available.'), el('p', 'muted text-small', 'The original role was removed from the catalog. Its details are unable to verify.'), remove); grid.append(missing);
      return;
    }
    grid.append(internshipCard(favorite, { saved: true, onSave: async item => {
      await api.removeFavorite(item.id);
      favorites = favorites.filter(value => (value.internship_id || value.internship?.id) !== item.id);
      render(); toast('Removed from your shortlist.'); return false;
    } }));
  });
  results.replaceChildren(grid);
}
async function load() {
  loading(results, 'Opening your shortlist…');
  try { favorites = listFrom(await api.favorites(), ['favorites']); render(); }
  catch (error) { count.textContent = 'Saved roles unavailable'; empty(results, 'Your shortlist couldn’t be loaded.', error.message, { retry: load, iconName: 'bookmark' }); }
}
async function init() { if (await requireAuth()) await load(); }
init();

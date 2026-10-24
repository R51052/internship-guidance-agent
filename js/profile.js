import { api, setStatus, profileCompletion, text, toast } from './api.js';

export function renderProfileSummary(profile) {
  const percent = profileCompletion(profile);
  document.getElementById('profile-percent').textContent = `${percent}%`;
  const progress = document.getElementById('profile-progress-bar');
  progress.style.width = `${percent}%`;
  progress.parentElement.setAttribute('aria-valuenow', percent);
  document.getElementById('profile-progress-label').textContent = `${percent}% complete · More detail makes a more useful match.`;
  document.getElementById('summary-education').textContent = text(profile.education);
  document.getElementById('summary-skills').textContent = profile.skills?.length ? profile.skills.slice(0, 4).join(', ') : 'Not specified';
  document.getElementById('summary-location').textContent = profile.preferred_locations?.length ? profile.preferred_locations.join(', ') : 'Not specified';
}

const listFields = { skills: 50, interests: 30, preferred_locations: 20 };
function parseList(value, key) {
  const list = [...new Map(value.split(',').map(item => item.trim()).filter(Boolean).map(item => [item.toLocaleLowerCase(), item])).values()];
  if (list.length > listFields[key]) throw new Error(`Please use no more than ${listFields[key]} ${key.replaceAll('_', ' ')}.`);
  if (list.some(item => item.length > 100)) throw new Error(`Each ${key.replaceAll('_', ' ')} entry must be 100 characters or fewer.`);
  return list;
}

export function initProfileForm(profile, onSaved) {
  const form = document.getElementById('profile-form');
  const fields = document.getElementById('profile-fields');
  const status = document.getElementById('profile-status');
  for (const [name, value] of Object.entries(profile)) {
    const input = form.elements.namedItem(name);
    if (!input) continue;
    if (input instanceof HTMLSelectElement && value != null && ![...input.options].some(option => option.value === String(value))) {
      const option = document.createElement('option'); option.value = String(value); option.textContent = `${value} months`; input.append(option);
    }
    input.value = Array.isArray(value) ? value.join(', ') : value ?? '';
  }
  fields.disabled = false;
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const data = new FormData(form);
    const body = {};
    setStatus(status);
    try {
      for (const [name, value] of data) {
        if (name in listFields) body[name] = parseList(value, name);
        else if (['year', 'cgpa', 'max_duration_months'].includes(name)) body[name] = value === '' ? null : Number(value);
        else if (name === 'min_stipend') body[name] = value === '' ? 0 : Number(value);
        else if (name === 'available_from') body[name] = value || null;
        else body[name] = value.trim();
      }
      const save = document.getElementById('save-profile');
      save.disabled = true; save.textContent = 'Saving your profile…';
      try {
        const updated = await api.saveProfile(body);
        renderProfileSummary(updated.profile || updated);
        setStatus(status, 'Profile saved. Your recommendations are being refreshed.', 'success');
        toast('Your profile is up to date.');
        await onSaved?.(updated.profile || updated);
      } finally { save.disabled = false; save.textContent = 'Save my profile'; }
    } catch (error) { setStatus(status, error.message); }
  });
}

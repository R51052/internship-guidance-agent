import { api, dateText, el, empty, icon, listFrom, loading, safeURL, setStatus, stipendText, text, toast, workMode } from './api.js';
import { requireAuth } from './auth.js';

const container = document.getElementById('details-content');
const id = new URLSearchParams(location.search).get('id');
function fact(list, label, value) {
  const row = el('div'); row.append(el('dt', '', label), el('dd', '', text(value))); list.append(row);
}
function paragraph(section, title, content) { section.append(el('h3', '', title), el('p', '', text(content))); }
function bulletList(section, title, values, fallback = 'Not specified') {
  section.append(el('h3', '', title));
  if (!values?.length) { section.append(el('p', '', fallback)); return; }
  const list = el('ul'); values.forEach(value => list.append(el('li', '', value))); section.append(list);
}
async function load() {
  loading(container, 'Getting the full picture…');
  try {
    const item = await api.internship(id);
    document.title = `${text(item.title)} — Internpath`;
    const layout = el('div', 'details-layout');
    const main = el('div');
    const hero = el('section', 'panel details-hero');
    const company = el('div', 'details-company');
    const avatar = el('span', 'company-avatar', (item.company || '?').charAt(0).toUpperCase()); avatar.setAttribute('aria-hidden', 'true');
    company.append(avatar, el('p', 'company-name', text(item.company)));
    hero.append(company, el('h1', '', text(item.title)));
    const tags = el('div', 'tag-row');
    if (item.domain) tags.append(el('span', 'pill pill-purple', item.domain));
    tags.append(el('span', 'pill', workMode(item.work_mode)));
    if (item.is_demo) tags.append(el('span', 'pill', 'Demo listing · not a verified opening'));
    if (Number.isFinite(item.match?.score)) tags.append(el('span', 'pill pill-green', `${Math.round(item.match.score)}% profile match`));
    hero.append(tags);
    const meta = el('div', 'card-meta');
    for (const [symbol, value] of [['pin', text(item.location)], ['clock', item.duration_months ? `${item.duration_months} months` : 'Duration not specified'], ['calendar', `Apply by ${dateText(item.application_deadline)}`]]) {
      const span = el('span'); span.append(icon(symbol), document.createTextNode(value)); meta.append(span);
    }
    hero.append(meta); main.append(hero);
    const description = el('section', 'panel prose-panel'); description.append(el('h2', '', 'A closer look at the opportunity'), el('p', '', text(item.description)));
    bulletList(description, 'Skills the role calls for', item.skills_required);
    description.append(el('h3', '', 'Eligibility requirements'));
    const eligibility = item.eligibility || {};
    const rules = [];
    if (eligibility.min_cgpa !== null && eligibility.min_cgpa !== undefined) rules.push(`Minimum CGPA: ${eligibility.min_cgpa} / 10`);
    if (eligibility.degrees?.length) rules.push(`Degrees: ${eligibility.degrees.join(', ')}`);
    if (eligibility.years?.length) rules.push(`Study years: ${eligibility.years.join(', ')}`);
    if (rules.length) { const list = el('ul'); rules.forEach(rule => list.append(el('li', '', rule))); description.append(list); }
    else description.append(el('p', '', 'Not specified. Confirm eligibility requirements with the employer.'));
    if (item.match) {
      paragraph(description, 'How this fits your profile', item.match.eligible === true ? 'Your saved profile meets the eligibility requirements in this catalog. Employer verification is still needed.' : item.match.eligible === false ? 'Some eligibility requirements are unmet or missing from your profile.' : 'Unable to verify eligibility.');
      bulletList(description, 'Why this match?', item.match.explanation, 'Unable to verify');
      bulletList(description, 'Skills you can build next', item.match.missing_skills, 'No skill gaps identified from the skills listed.');
      if (item.match.ineligibility_reasons?.length) bulletList(description, 'Requirements to check', item.match.ineligibility_reasons);
    } else paragraph(description, 'Profile match', 'Unable to verify.');
    main.append(description);
    const sidebar = el('aside', 'detail-sidebar');
    const overview = el('section', 'panel'); overview.append(el('h2', '', 'The practical details'));
    const facts = el('dl', 'detail-facts');
    fact(facts, 'Stipend', stipendText(item)); fact(facts, 'Duration', item.duration_months ? `${item.duration_months} months` : null);
    fact(facts, 'Start date', dateText(item.start_date)); fact(facts, 'Application deadline', dateText(item.application_deadline));
    fact(facts, 'Work mode', workMode(item.work_mode)); fact(facts, 'Source', item.source);
    overview.append(facts);
    const today = new Date(); const todayString = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
    const expired = item.application_deadline && item.application_deadline < todayString;
    const started = item.start_date && item.start_date < todayString;
    const url = safeURL(item.apply_url);
    if (url && !item.is_demo && !expired && !started) {
      const apply = el('a', 'btn btn-primary btn-full', 'View application'); apply.href = url; apply.target = '_blank'; apply.rel = 'noopener noreferrer'; apply.append(icon('external')); overview.append(apply);
    } else {
      const unavailable = el('p', 'status info', item.is_demo ? 'This is demo data. A real application link is unavailable.' : expired ? 'The listed application deadline has passed.' : started ? 'The listed start date has passed. Confirm availability with the employer.' : 'Application link: Not specified.');
      overview.append(unavailable);
    }
    const save = el('button', 'btn btn-secondary btn-full', 'Checking saved status…'); save.type = 'button'; save.disabled = true; save.style.marginTop = '12px';
    overview.append(save);
    const verification = el('div', 'verification'); verification.append(icon('shield'), el('p', '', item.is_demo ? 'Illustrative demo listing. Company, stipend, dates, and availability are not verified real-world facts.' : 'Unable to verify live availability. Confirm the stipend, dates, and requirements with the employer before applying.'));
    overview.append(verification); sidebar.append(overview);
    const guidance = el('section', 'assistant-promo'); const symbol = el('div', 'empty-icon'); symbol.append(icon('sparkles'));
    const ask = el('a', 'btn btn-primary btn-full', 'Talk through this role'); ask.href = `ai-assistant.html?internship_id=${encodeURIComponent(item.id)}`; ask.append(icon('arrow'));
    guidance.append(symbol, el('h3', '', 'Could this be your next step?'), el('p', '', 'Ask about your skill gaps, eligibility, or how to prepare for this opportunity.'), ask); sidebar.append(guidance);
    layout.append(main, sidebar); container.replaceChildren(layout);
    try {
      const favorites = listFrom(await api.favorites(), ['favorites']);
      let saved = favorites.some(favorite => (favorite.internship_id || favorite.internship?.id) === item.id);
      const update = () => { save.textContent = saved ? 'Remove from saved' : 'Save this opportunity'; save.setAttribute('aria-pressed', String(saved)); save.disabled = false; };
      update();
      save.addEventListener('click', async () => {
        save.disabled = true;
        try { await (saved ? api.removeFavorite(item.id) : api.addFavorite(item.id)); saved = !saved; toast(saved ? 'Saved to your shortlist.' : 'Removed from your shortlist.'); }
        catch (error) { toast(error.message, true); }
        finally { update(); }
      });
    } catch (error) { save.textContent = 'Unable to check saved status'; setStatus(document.getElementById('page-status'), error.message); }
  } catch (error) {
    empty(container, error.status === 404 ? 'This opportunity is no longer here.' : 'We couldn’t load this opportunity.', error.status === 404 ? 'It may have been removed. Explore the current catalog for your next possibility.' : error.message, { href: 'recommendations.html', label: 'Explore opportunities', retry: error.status === 404 ? undefined : load });
  }
}
async function init() {
  if (!await requireAuth()) return;
  if (!id) { empty(container, 'Choose an opportunity first.', 'Open a role from your recommendations or saved internships to see the full details.', { href: 'recommendations.html', label: 'Explore opportunities' }); return; }
  await load();
}
init();

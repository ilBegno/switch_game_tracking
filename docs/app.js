const state = {
  games: [],
  q: '',
  sort: 'recent',
};

const $ = sel => document.querySelector(sel);
const grid = $('#grid');
const empty = $('#empty');
const stats = $('#stats'); // displays total count, total time, and last played

function parsePlaytime(pt) {
  if (!pt) return 0; // minutes
  let h = 0, m = 0;
  const hMatch = pt.match(/(\d+)h/);
  const mMatch = pt.match(/(\d+)m/);
  if (hMatch) h = parseInt(hMatch[1], 10);
  if (mMatch) m = parseInt(mMatch[1], 10);
  return h * 60 + m;
}

function formatPlaytime(mins) {
  if (mins <= 0) return '—';
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  if (h && m) return `${h}h ${m}m`;
  if (h) return `${h}h`;
  return `${m}m`;
}

function formatDateFromEpoch(sec) {
  if (!sec) return '—';
  const d = new Date(parseInt(sec, 10) * 1000);
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

function cmp(a,b){ return a<b?-1:a>b?1:0; }

function computeStats(rows) {
  const total = rows.length;
  const sumMins = rows.reduce((s, r) => s + r.playMins, 0);
  const last = rows.reduce((mx, r) => Math.max(mx, r.last_played||0), 0);
  return { total, sumMins, last };
}

function renderStats(rows) {
  const s = computeStats(rows);
  stats.innerHTML = `
    <div class="stat"><div class="label">Total games</div><div class="value">${s.total}</div></div>
    <div class="stat"><div class="label">Total playtime</div><div class="value">${formatPlaytime(s.sumMins)}</div></div>
    <div class="stat"><div class="label">Last played</div><div class="value">${formatDateFromEpoch(s.last)}</div></div>
  `;
}

function normalize(str){
  return (str||'').normalize('NFD').replace(/\p{Diacritic}/gu,'').toLowerCase();
}

function applyFilters() {
  const q = normalize(state.q.trim());
  let rows = state.games.filter(g => !q || normalize(g.title).includes(q));

  // Update empty message with query
  const msg = q ? `No results for "${state.q}".` : 'No results.';
  empty.textContent = msg;

  switch (state.sort) {
    case 'alpha':
      rows.sort((a,b)=>cmp(a.title.toLowerCase(), b.title.toLowerCase()));
      break;
    case 'playtime-asc':
      rows.sort((a,b)=>a.playMins-b.playMins);
      break;
    case 'playtime-desc':
      rows.sort((a,b)=>b.playMins-a.playMins);
      break;
    default: // recent
      rows.sort((a,b)=> (b.last_played||0) - (a.last_played||0));
  }

  renderStats(rows);
  renderGrid(rows);
}

function renderGrid(rows) {
  if (!rows.length) {
    grid.innerHTML = '';
    empty.hidden = false;
    return;
  }
  empty.hidden = true;
  const frag = document.createDocumentFragment();
  rows.forEach(r => {
    const card = document.createElement('article');
    card.className = 'card';
    card.innerHTML = `
      <img class="thumb" src="${r.image_url}" alt="Cover art for ${r.title}" loading="lazy" decoding="async" referrerpolicy="no-referrer" />
      <div class="content">
        <div class="game-title">${r.title}</div>
        <div class="meta">
          <span class="badge time" title="Playtime">${formatPlaytime(r.playMins)}</span>
          <span>•</span>
          <span class="badge last" title="Last played">${formatDateFromEpoch(r.last_played)}</span>
        </div>
      </div>
    `;
    frag.appendChild(card);
  });
  grid.innerHTML = '';
  grid.appendChild(frag);
}

async function loadJSON() {
  const res = await fetch('games.json', { cache: 'no-store' });
  const games = await res.json();
  const rows = games.map(game => {
    const title = game.title;
    const playtime = game.playtime;
    const image_url = game.image_url;
    const last_played = game.last_played ? Number(game.last_played) : 0;
    return { title, playtime, image_url, last_played, playMins: parsePlaytime(playtime) };
  });
  state.games = rows;
  applyFilters();
}

function bindUI() {
  const q = $('#q');
  const sort = $('#sort');

  q.addEventListener('input', () => { state.q = q.value; applyFilters(); updateURL(); });
  q.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); q.blur(); } });
  window.addEventListener('keydown', (e)=>{ if(e.key==='/' && document.activeElement!==q){ e.preventDefault(); q.focus(); }});

  sort.addEventListener('change', ()=>{ state.sort = sort.value; applyFilters(); updateURL(); });
}

function updateURL(){
  const params = new URLSearchParams();
  if (state.q) params.set('q', state.q);
  if (state.sort && state.sort !== 'recent') params.set('sort', state.sort);
  const url = `${location.pathname}?${params.toString()}`;
  history.replaceState(null, '', url);
}

function initFromURL(){
  const params = new URLSearchParams(location.search);
  const q = params.get('q') || '';
  const sort = params.get('sort') || 'recent';
  state.q = q; state.sort = sort;
  $('#q').value = q; $('#sort').value = sort;
}

initFromURL();
bindUI();
loadJSON();

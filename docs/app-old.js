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

function formatPlaytime(minutes, fullFormat = false) {
  if (minutes < 60) {
    return fullFormat ? `${minutes} min${minutes !== 1 ? 's' : ''}` : `${minutes}m`;
  }
  
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  
  if (fullFormat) {
    const hourText = `${hours} hr${hours !== 1 ? 's' : ''}`;
    const minuteText = remainingMinutes > 0 ? ` ${remainingMinutes} min${remainingMinutes !== 1 ? 's' : ''}` : '';
    return hourText + minuteText;
  } else {
    return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
  }
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
          <span class="badge time" title="Playtime">${formatPlaytime(r.playMins, false)}</span>
          <span class="spacer"></span>
          <span class="badge last" title="Last played">${formatDateFromEpoch(r.last_played)}</span>
        </div>
      </div>
    `;
    // Add click event to show modal
    card.addEventListener('click', () => showGameModal(r));
    frag.appendChild(card);
  });
  grid.innerHTML = '';
  grid.appendChild(frag);
}

function showGameModal(game) {
  // Replace /l/ with /xl/ in the image URL for full resolution
  const fullResImageUrl = game.image_url.replace('/l/', '/xl/');
  
  // Get modal elements
  const modalImage = document.getElementById('modal-image');
  const modal = document.getElementById('game-modal');
  
  // Set initial state with the low-res image while loading
  modalImage.src = game.image_url;
  modalImage.classList.add('loading');
  
  // Update modal content
  document.getElementById('modal-title').textContent = game.title;
  document.getElementById('modal-playtime').textContent = formatPlaytime(game.playMins, true); // Use full format
  document.getElementById('modal-last-played').textContent = formatDateFromEpoch(game.last_played);
  
  // Create a new image to preload the full resolution image
  const img = new Image();
  img.onload = function() {
    // When loaded, update the modal image and remove loading state
    modalImage.src = fullResImageUrl;
    modalImage.classList.remove('loading');
  };
  img.onerror = function() {
    // If there's an error, keep the original image
    modalImage.classList.remove('loading');
  };
  img.src = fullResImageUrl;
  
  // Show modal
  modal.classList.add('active');
  modal.setAttribute('aria-hidden', 'false');
  
  // Prevent body scroll when modal is open
  document.body.style.overflow = 'hidden';
}

function closeGameModal() {
  const modal = document.getElementById('game-modal');
  modal.classList.remove('active');
  modal.setAttribute('aria-hidden', 'true');
  
  // Restore body scroll
  document.body.style.overflow = '';
}

// Close modal when clicking overlay or close button
document.addEventListener('DOMContentLoaded', function() {
  const modal = document.getElementById('game-modal');
  const closeButtons = modal.querySelectorAll('[data-close]');
  
  closeButtons.forEach(button => {
    button.addEventListener('click', closeGameModal);
  });
  
  // Close modal with Escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && modal.classList.contains('active')) {
      closeGameModal();
    }
  });
});

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

// Close modal when clicking overlay or close button
document.addEventListener('DOMContentLoaded', function() {
  const modal = document.getElementById('game-modal');
  const closeButtons = modal.querySelectorAll('[data-close]');
  
  closeButtons.forEach(button => {
    button.addEventListener('click', closeGameModal);
  });
  
  // Close modal with Escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && modal.classList.contains('active')) {
      closeGameModal();
    }
  });
});

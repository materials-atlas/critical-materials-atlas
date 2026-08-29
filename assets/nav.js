/* Shared top navigation for the Critical Materials Atlas.
   Phase-1 IA: five clear top-level destinations, each a real hub page (no hover mega-menus).
   Phase-2 IA: a persistent header SEARCH box over an index of ~168 pages — the true replacement
   for a 58-link menu. The former dropdown links live as curated cards inside the Analysis/Method hubs.
   Rebuilds any <nav class="topnav"> and marks the active page.
   Included site-wide via <script src="assets/nav.js" defer></script>.
   The homepage (index.html) mirrors the link menu inline; keep the two in sync. */
(function () {
  var LINKS = [
    ['explorer', 'Explore', false],
    ['value-chains', 'Value Chains', false],
    ['analysis', 'Analysis', false],
    ['reports', 'Reports', false],
    ['method', 'Method', true]
  ];
  var INDEX_URL = '/out/search-index.json';

  var CSS = [
    '.topnav .navsearch{position:relative;margin-left:.6rem}',
    '.topnav .navsearch input{font:inherit;font-size:.82rem;width:9.5rem;max-width:38vw;padding:.32rem .6rem .32rem 1.7rem;border:1px solid var(--line,#e3e9e8);border-radius:8px;background:var(--bg-soft,#eef3f2) url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'14\' height=\'14\' viewBox=\'0 0 24 24\' fill=\'none\' stroke=\'%237a8a87\' stroke-width=\'2\'%3E%3Ccircle cx=\'11\' cy=\'11\' r=\'7\'/%3E%3Cpath d=\'M21 21l-4.3-4.3\'/%3E%3C/svg%3E") .5rem center/14px no-repeat;color:var(--ink,#1f2d2b);outline:none;transition:width .15s,border-color .15s}',
    '.topnav .navsearch input:focus{width:15rem;border-color:var(--accent,#0e7c74)}',
    '.topnav .navresults{position:absolute;top:100%;right:0;margin-top:.35rem;background:#fff;border:1px solid var(--line,#e3e9e8);border-radius:10px;box-shadow:0 12px 32px rgba(20,50,58,.16);min-width:20rem;max-width:26rem;max-height:60vh;overflow-y:auto;padding:.3rem;display:none;z-index:80}',
    '.topnav .navresults.on{display:block}',
    '.topnav .navresults a{display:block;padding:.4rem .55rem;border-radius:7px;text-decoration:none;color:var(--ink,#1f2d2b)}',
    '.topnav .navresults a:hover,.topnav .navresults a.sel{background:var(--bg-soft,#eef3f2)}',
    '.topnav .navresults .rt{font-weight:600;font-size:.84rem;color:var(--navy,#15323a);line-height:1.25}',
    '.topnav .navresults .rg{font-size:.62rem;text-transform:uppercase;letter-spacing:.06em;color:#9aa6ad;font-weight:700;margin-left:.4rem}',
    '.topnav .navresults .rd{display:block;font-size:.74rem;color:var(--mut,#5a6b68);line-height:1.3;margin-top:.1rem}',
    '.topnav .navresults .rnone{padding:.6rem;color:var(--mut,#5a6b68);font-size:.82rem}',
    '@media(max-width:760px){.topnav .navsearch{display:none}}'
  ].join('');

  function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'); }

  function build() {
    var html = '<a href="./">Atlas</a>';
    LINKS.forEach(function (l) {
      html += '<a href="' + l[0] + '"' + (l[2] ? ' class="hideable"' : '') + '>' + esc(l[1]) + '</a>';
    });
    html += '<a href="data" class="cta">Download data</a>';
    html += '<span class="navsearch"><input type="search" id="nav-q" placeholder="Search the atlas…" '
          + 'autocomplete="off" aria-label="Search the atlas"><div class="navresults" id="nav-r"></div></span>';
    return html;
  }

  var DATA = null, sel = -1, cur = [];
  function href(u){ return '/' + u; }              // clean root-absolute path; '' -> '/'
  function render(q) {
    var box = document.getElementById('nav-r');
    q = q.trim().toLowerCase();
    if (!q) { box.className = 'navresults'; box.innerHTML = ''; cur = []; return; }
    var terms = q.split(/\s+/);
    cur = (DATA || []).map(function (it) {
      var hay = (it.t + ' ' + it.d + ' ' + it.g).toLowerCase();
      var score = 0;
      for (var i = 0; i < terms.length; i++) {
        if (it.t.toLowerCase().indexOf(terms[i]) === 0) score += 6;      // title prefix
        else if (it.t.toLowerCase().indexOf(terms[i]) >= 0) score += 4;  // title contains
        else if (hay.indexOf(terms[i]) >= 0) score += 1;                 // anywhere
        else return null;                                                // every term must hit
      }
      return { it: it, s: score };
    }).filter(Boolean).sort(function (a, b) { return b.s - a.s; }).slice(0, 8).map(function (r) { return r.it; });
    sel = -1;
    if (!cur.length) { box.className = 'navresults on'; box.innerHTML = '<div class="rnone">No page matches “' + esc(q) + '”.</div>'; return; }
    box.innerHTML = cur.map(function (it) {
      return '<a href="' + href(it.u) + '"><span class="rt">' + esc(it.t) + '<span class="rg">' + esc(it.g) + '</span></span>'
           + (it.d ? '<span class="rd">' + esc(it.d) + '</span>' : '') + '</a>';
    }).join('');
    box.className = 'navresults on';
  }
  function highlight() {
    var links = document.querySelectorAll('#nav-r a');
    links.forEach(function (a, i) { a.classList.toggle('sel', i === sel); });
    if (sel >= 0 && links[sel]) links[sel].scrollIntoView({ block: 'nearest' });
  }

  function wireSearch() {
    var q = document.getElementById('nav-q'), box = document.getElementById('nav-r');
    if (!q) return;
    function load() { if (!DATA) fetch(INDEX_URL).then(function (r) { return r.json(); }).then(function (d) { DATA = d; if (q.value) render(q.value); }).catch(function () { DATA = []; }); }
    q.addEventListener('focus', load);
    q.addEventListener('input', function () { render(q.value); });
    q.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); sel = Math.min(sel + 1, cur.length - 1); highlight(); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); sel = Math.max(sel - 1, -1); highlight(); }
      else if (e.key === 'Enter') { var go = cur[sel >= 0 ? sel : 0]; if (go) location.href = href(go.u); }
      else if (e.key === 'Escape') { q.blur(); box.className = 'navresults'; }
    });
    document.addEventListener('click', function (e) { if (!e.target.closest('.navsearch')) box.className = 'navresults'; });
  }

  function init() {
    var nav = document.querySelector('nav.topnav');
    if (!nav) return;
    if (!document.getElementById('nav-shared-css')) {
      var st = document.createElement('style'); st.id = 'nav-shared-css'; st.textContent = CSS;
      document.head.appendChild(st);
    }
    nav.innerHTML = build();
    var here = (location.pathname.split('/').pop() || '').replace(/\.html$/, '');
    nav.querySelectorAll('a[href]').forEach(function (a) {
      if (a.getAttribute('href') === here) a.classList.add('active');
    });
    wireSearch();
  }

  if (document.readyState !== 'loading') init();
  else document.addEventListener('DOMContentLoaded', init);
})();

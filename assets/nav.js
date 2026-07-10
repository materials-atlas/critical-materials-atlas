/* Shared top navigation for the Critical Materials Atlas.
   Self-contained: injects its own dropdown CSS, rebuilds any <nav class="topnav">
   into the canonical grouped menu, wires hover/click dropdowns, marks the active page.
   Included site-wide via <script src="assets/nav.js" defer></script>.
   The homepage (index.html) keeps its own hand-tuned nav with the CSV-download CTA and does NOT load this. */
(function () {
  var CSS = [
    '.topnav .grp{position:relative}',
    '.topnav .grp>button{font:inherit;color:var(--ink-soft,#5a6b68);font-size:.86rem;font-weight:600;letter-spacing:.005em;background:none;border:0;cursor:pointer;padding:0;display:inline-flex;align-items:center;gap:.22rem}',
    '.topnav .grp>button::after{content:"\\25BE";font-size:.72em;opacity:.65}',
    '.topnav .grp:hover>button,.topnav .grp.open>button,.topnav a.active{color:var(--navy,#15323a)}',
    '.topnav a.active{font-weight:700}',
    '.topnav .menu{position:absolute;top:100%;left:0;margin-top:.4rem;background:#fff;border:1px solid var(--line,#e3e9e8);border-radius:10px;box-shadow:0 12px 32px rgba(20,50,58,.14);padding:.4rem;min-width:14.5rem;display:none;flex-direction:column;gap:.05rem;z-index:60}',
    '.topnav .menu::before{content:"";position:absolute;top:-.4rem;left:0;right:0;height:.4rem}',
    '.topnav .grp:hover .menu,.topnav .grp.open .menu{display:flex}',
    '.topnav .menu a{display:block;padding:.42rem .6rem;border-radius:7px;font-size:.84rem;font-weight:500;color:var(--ink,#1f2d2b)}',
    '.topnav .menu a:hover{background:var(--bg-soft,#eef3f2);color:var(--navy,#15323a);text-decoration:none}',
    '.topnav .menu .lbl{font-size:.66rem;text-transform:uppercase;letter-spacing:.07em;color:#9aa6ad;font-weight:700;padding:.5rem .6rem .2rem;border-top:1px solid var(--line,#e3e9e8);margin-top:.25rem}',
    '@media(max-width:760px){.topnav .grp.hideable{display:none}}'
  ].join('');

  var GROUPS = [
    { label: 'Analysis', items: [
      ['trends.html', 'Trends — 22-year evolution'],
      ['volume.html', 'Value vs volume (price effects)'],
      ['network.html', 'Trade-network chokepoints'],
      ['complexity.html', 'Economic complexity'],
      ['origin.html', 'Origin trace'],
      ['criticality.html', 'Governance-weighted criticality'] ] },
    { label: 'Risk', items: [
      ['risk.html', 'Supply-risk index'],
      ['riskmethods.html', 'Risk methods — TOPSIS · GeoPolRisk · tail'],
      ['scenarios.html', 'Shock scenarios'],
      ['__lbl__', 'Interactive'],
      ['index-builder.html', 'Build your own risk index'],
      ['shock-builder.html', 'Build your own supply shock'] ] },
    { label: 'Supply structure', items: [
      ['companionality.html', 'Hostage metals — by-product dependency'],
      ['risk-adjusted.html', 'Risk when supply can’t respond'],
      ['host-shock.html', 'Host shock — the commodities that gate criticals'],
      ['recycling.html', 'Secondary supply — recycling & the trapped metals'] ] },
    { label: 'Satellite', items: [
      ['satellite.html', 'Mine footprint (from orbit)'],
      ['mining-expansion.html', 'Mining expansion — new supply'],
      ['commodity-attribution.html', 'Which mineral? (attribution limit)'] ] },
    { label: 'Rigor', items: [
      ['robustness.html', 'Robustness — do findings survive?'],
      ['network-sensitivity.html', 'Network truncation sensitivity'],
      ['limitations.html', 'Limitations & falsification'] ] },
    { label: 'Reference', items: [
      ['methodology.html', 'Methodology & validation'],
      ['technical-note.html', 'Technical note (PDF)'],
      ['brief.html', 'One-page findings brief'],
      ['casestudies.html', 'Case studies — known-chain audit'],
      ['profiles.html', 'Material & country profiles'],
      ['data.html', 'Open data / API'],
      ['map.html', 'Project map — how it\'s built'],
      ['https://github.com/materials-atlas/comtrade-reconcile', 'Reconciliation engine'] ] }
  ];

  function esc(s){ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;'); }

  function build() {
    var html = '<a href="./">Atlas</a>' +
               '<a href="insights.html">Insights</a>' +
               '<a href="findings.html" class="hideable">Findings</a>';
    GROUPS.forEach(function (g) {
      html += '<div class="grp hideable"><button type="button">' + g.label + '</button><div class="menu">';
      g.items.forEach(function (it) {
        if (it[0] === '__lbl__') html += '<span class="lbl">' + esc(it[1]) + '</span>';
        else html += '<a href="' + it[0] + '"' + (/^https?:/.test(it[0]) ? ' target="_blank" rel="noopener"' : '') + '>' + esc(it[1]) + '</a>';
      });
      html += '</div></div>';
    });
    html += '<a href="data.html" class="cta">Download data</a>';
    return html;
  }

  function init() {
    var nav = document.querySelector('nav.topnav');
    if (!nav) return;
    if (!document.getElementById('nav-shared-css')) {
      var st = document.createElement('style'); st.id = 'nav-shared-css'; st.textContent = CSS;
      document.head.appendChild(st);
    }
    nav.innerHTML = build();
    var here = (location.pathname.split('/').pop() || 'index.html');
    nav.querySelectorAll('a[href]').forEach(function (a) {
      if (a.getAttribute('href') === here) a.classList.add('active');
    });
    nav.querySelectorAll('.grp>button').forEach(function (b) {
      b.addEventListener('click', function (e) {
        e.stopPropagation();
        var g = b.parentElement, open = g.classList.contains('open');
        nav.querySelectorAll('.grp.open').forEach(function (x) { x.classList.remove('open'); });
        if (!open) g.classList.add('open');
      });
    });
    document.addEventListener('click', function () {
      nav.querySelectorAll('.grp.open').forEach(function (x) { x.classList.remove('open'); });
    });
  }

  if (document.readyState !== 'loading') init();
  else document.addEventListener('DOMContentLoaded', init);
})();

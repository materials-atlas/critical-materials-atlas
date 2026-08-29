/* Shared top navigation for the Critical Materials Atlas.
   Phase-1 IA cleanup: five clear top-level destinations, each a real hub page (no hover mega-menus).
   The ~58 former dropdown links now live as curated cards inside the Analysis and Method hubs.
   Rebuilds any <nav class="topnav"> into the canonical menu and marks the active page.
   Included site-wide via <script src="assets/nav.js" defer></script>.
   The homepage (index.html) mirrors this menu inline; keep the two in sync. */
(function () {
  // [href, label, hideableOnMobile]
  var LINKS = [
    ['explorer', 'Explore', false],
    ['value-chains', 'Value Chains', false],
    ['analysis', 'Analysis', false],
    ['reports', 'Reports', false],
    ['method', 'Method', true]
  ];

  function esc(s){ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;'); }

  function build() {
    var html = '<a href="./">Atlas</a>';
    LINKS.forEach(function (l) {
      html += '<a href="' + l[0] + '"' + (l[2] ? ' class="hideable"' : '') + '>' + esc(l[1]) + '</a>';
    });
    html += '<a href="data" class="cta">Download data</a>';
    return html;
  }

  function init() {
    var nav = document.querySelector('nav.topnav');
    if (!nav) return;
    nav.innerHTML = build();
    // active-marker: current page leaf, tolerating both clean and .html URL forms
    var here = (location.pathname.split('/').pop() || '').replace(/\.html$/, '');
    nav.querySelectorAll('a[href]').forEach(function (a) {
      if (a.getAttribute('href') === here) a.classList.add('active');
    });
  }

  if (document.readyState !== 'loading') init();
  else document.addEventListener('DOMContentLoaded', init);
})();

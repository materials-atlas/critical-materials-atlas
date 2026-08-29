/* Shared renderer for the value-chain pilot pages.
   Each page sets window.CHAIN_DATA and window.CHAIN_TRADE before loading this file.
   Renders the uniform chain schema: stats, hops, sections (panels), an optional longitudinal
   history chart, a trade slider, a method table and sources — with per-figure confidence tags. */
(function () {
  var DATA = window.CHAIN_DATA, TRADE = window.CHAIN_TRADE;
  var PALETTE = ['var(--acc)', '#b07a2e', '#5a8a7a', '#8a5a7a'];
  function esc(s) { return String(s == null ? '' : s).replace(/[<>]/g, function (c) { return { '<': '&lt;', '>': '&gt;' }[c]; }); }
  function money(v) { return v >= 1e9 ? '$' + (v / 1e9).toFixed(1) + 'B' : v >= 1e6 ? '$' + (v / 1e6).toFixed(1) + 'M' : '$' + Math.round(v / 1e3) + 'k'; }
  function conf(c) { return c ? ' <span class="conf ' + esc(c) + '" title="evidence type">' + esc(c) + '</span>' : ''; }
  // An 'estimate' is not a figure quoted from a primary source. basis.json says how it was derived and
  // its limits; these render it as a click-to-open note so the reader can see exactly what stands behind it.
  var KINDLABEL = { computed: 'Calculated from primary data', reported: 'Reported by an authoritative body', reconciled: 'Reconciled central value', assessment: 'Our assessment', count: 'A count, not a market share' };
  function closeBasisPop() { var p = document.querySelector('.bpop'); if (p) p.parentNode.removeChild(p); }
  function showBasisPop(anchor, b) {
    closeBasisPop();
    var pop = document.createElement('div'); pop.className = 'bpop';
    pop.innerHTML = '<span class="x" role="button" aria-label="close">&times;</span><span class="k">' + esc(KINDLABEL[b.kind] || 'How this was estimated') + '</span>' + esc(b.text);
    document.body.appendChild(pop);
    var rc = anchor.getBoundingClientRect(), sx = window.pageXOffset, sy = window.pageYOffset;
    var left = Math.min(rc.left + sx, sx + document.documentElement.clientWidth - pop.offsetWidth - 12);
    pop.style.left = Math.max(sx + 8, left) + 'px'; pop.style.top = (rc.bottom + sy + 6) + 'px';
    pop.querySelector('.x').addEventListener('click', closeBasisPop);
  }
  function barsHTML(rows, max) {
    var m = max || Math.max.apply(null, rows.map(function (r) { return r.value || 0; })) || 1;
    return '<div class="bars">' + rows.map(function (r) {
      var v = r.value, w = v == null ? 0 : Math.max(2, v / m * 100);
      var show = v == null ? 'n/a' : (r.fmt === 'pct0' ? Math.round(v) + '%' : (v <= 1 ? Math.round(v * 100) + '%' : v.toLocaleString()));
      return '<div class="barrow"><b>' + esc(r.label) + '</b><span class="track"><span class="fill" style="width:' + w + '%"></span></span><span class="num">' + show + '</span></div>';
    }).join('') + '</div>';
  }
  var _sources = {};
  function srcCite(src) {
    if (!src) return '';
    var keys = Object.prototype.toString.call(src) === '[object Array]' ? src : [src];
    var out = keys.map(function (k) { var s = _sources[k]; return s ? '<a class="srccite" href="' + s.url + '" target="_blank" rel="noopener" title="' + esc(s.title) + '">†</a>' : ''; }).join('');
    return out ? ' ' + out : '';
  }
  function panelHTML(p) {
    var inner = '';
    if (p.h3) inner += '<h3>' + esc(p.h3) + conf(p.conf) + '</h3>';
    if (p.kind === 'bars') inner += barsHTML(p.bars, p.max);
    else if (p.kind === 'big') inner += '<p class="big">' + esc(p.big) + '</p><p>' + esc(p.text) + '</p>';
    else if (p.kind === 'text') inner += '<p style="margin-top:0">' + esc(p.text) + '</p>';
    else if (p.kind === 'cards') inner += '<div class="cards">' + p.cards.map(function (c) { return '<div class="card"><h4>' + esc(c.t) + '</h4><p>' + esc(c.d) + '</p></div>'; }).join('') + '</div>';
    if (p.note) inner += '<p class="note">' + esc(p.note) + srcCite(p.src) + '</p>';
    if (p.flag) inner += '<span class="flag">' + esc(p.flag) + '</span>';
    return '<div class="panel">' + inner + '</div>';
  }
  function historyChart(hist) {
    var W = 760, H = 230, pad = 42;
    var years = [], vals = [];
    hist.series.forEach(function (s) { s.points.forEach(function (p) { years.push(p.y); vals.push(p.v); }); });
    var y0 = Math.min.apply(null, years), y1 = Math.max.apply(null, years);
    // Default: a 0-100% share axis. If hist.unit is set, plot an absolute series with a
    // data-driven axis (unit named in the title/note), e.g. g/W, TWh, GW.
    var isPct = !hist.unit, rawmax = Math.max.apply(null, vals), vmin = 0, vmax, ticks;
    if (isPct) { vmax = Math.min(100, Math.ceil(rawmax / 10) * 10 + 5); ticks = [0, 25, 50, 75, 100].filter(function (g) { return g <= vmax; }); }
    else { var mag = Math.pow(10, Math.floor(Math.log10(rawmax))); vmax = Math.ceil(rawmax / mag) * mag; if (vmax < rawmax * 1.05) vmax += mag; ticks = [0, vmax / 4, vmax / 2, vmax * 3 / 4, vmax]; }
    var fmt = function (g) { return isPct ? g + '%' : (Math.round(g * 100) / 100).toLocaleString(); };
    var px = function (y) { return pad + (y1 === y0 ? 0.5 : (y - y0) / (y1 - y0)) * (W - 2 * pad); };
    var py = function (v) { return H - pad - (v - vmin) / (vmax - vmin) * (H - 2 * pad); };
    var s = '';
    if (!isPct) s += '<text x="6" y="12" font-size="9" fill="#68737a">' + esc(hist.unit) + '</text>';
    ticks.forEach(function (g) {
      s += '<line x1="' + pad + '" y1="' + py(g) + '" x2="' + (W - pad) + '" y2="' + py(g) + '" stroke="#e6e9e8"/><text x="6" y="' + (py(g) + 3) + '" font-size="9" fill="#68737a">' + fmt(g) + '</text>';
    });
    hist.series.forEach(function (ser, i) {
      var col = PALETTE[i % PALETTE.length];
      var pts = ser.points.map(function (p) { return px(p.y) + ',' + py(p.v); }).join(' ');
      s += '<polyline points="' + pts + '" fill="none" stroke="' + col + '" stroke-width="2.6"/>';
      ser.points.forEach(function (p) { s += '<circle cx="' + px(p.y) + '" cy="' + py(p.v) + '" r="2.6" fill="' + col + '"/>'; });
      s += '<text x="' + (W - pad) + '" y="' + (16 + i * 14) + '" text-anchor="end" font-size="10" fill="' + col + '">' + esc(ser.label) + '</text>';
    });
    [y0, Math.round((y0 + y1) / 2), y1].forEach(function (yr) { s += '<text x="' + px(yr) + '" y="' + (H - 12) + '" text-anchor="middle" font-size="10" fill="#68737a">' + yr + '</text>'; });
    return '<svg class="chart" viewBox="0 0 ' + W + ' ' + H + '">' + s + '</svg>';
  }
  function tradeRow(T, i) {
    var y = T.years[i], d = T.years_data[String(y)];
    document.getElementById('trade-year').textContent = y;
    document.getElementById('trade-body').innerHTML = Object.keys(T.codes).map(function (k) {
      var c = d[k], lead = c.exporters && c.exporters[0];
      return '<tr><td><b>' + esc(T.codes[k].title) + '</b><br><span class="note">HS ' + k + '</span></td><td>' + (c.world_usd ? money(c.world_usd) : '—') + '</td><td>' + (lead ? esc(lead.name) + ' · ' + Math.round(lead.share * 100) + '%' : '—') + '</td><td><span class="flag">' + esc(T.codes[k].boundary) + '</span></td></tr>';
    }).join('');
  }
  Promise.all([
    fetch(DATA).then(function (r) { return r.json(); }),
    fetch(TRADE).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; })
  ]).then(function (res) {
    var D = res[0], T = res[1];
    if (D.accent) document.documentElement.style.setProperty('--acc', D.accent);
    var db = document.getElementById('draftbar');
    if (D.published) db.innerHTML = 'Value Chains <span>— a research layer of the Critical Materials Atlas · ' + esc(D.title) + '</span>';
    else db.innerHTML = 'Research pilot · unpublished <span>— ' + esc(D.title) + ', not part of the live Atlas</span>';
    document.getElementById('eyebrow').textContent = D.eyebrow || '';
    document.getElementById('h1').textContent = D.h1 || D.title;
    document.getElementById('deck').innerHTML = esc(D.deck).replace(/&lt;i&gt;/g, '<i>').replace(/&lt;\/i&gt;/g, '</i>');
    document.getElementById('byline').textContent = D.byline || '';
    document.getElementById('correction').innerHTML = '<b>The finding.</b> ' + esc(D.correction);
    document.getElementById('stats').innerHTML = (D.stats || []).map(function (st) { return '<div class="stat"><div class="v">' + st.v + '</div><div class="l">' + st.l + conf(st.conf) + '</div></div>'; }).join('');
    document.getElementById('chain').innerHTML = (D.hops || []).map(function (h) { return '<div class="hop"><div class="n">' + esc(h.n) + '</div><div class="t">' + esc(h.t) + '</div></div>'; }).join('');
    if (D.history && D.history.series && D.history.series.length) {
      var wrap = document.getElementById('history-wrap');
      wrap.innerHTML = '<h2>' + esc(D.history.title) + conf(D.history.conf) + '</h2><div class="panel">' + historyChart(D.history) + '<p class="note">' + esc(D.history.note || '') + '</p></div>';
    }
    _sources = D.sources || {};
    document.getElementById('sections').innerHTML = (D.sections || []).map(function (sec) {
      var ps = sec.panels || [];
      var wrap = ps.length === 2 ? '<div class="split">' + ps.map(panelHTML).join('') + '</div>' : ps.map(panelHTML).join('');
      return '<h2>' + esc(sec.h2) + '</h2>' + wrap;
    }).join('');
    document.getElementById('trade-intro').textContent = D.trade_intro || '';
    document.getElementById('method-body').innerHTML = (D.method || []).map(function (m) { return '<tr><td><b>' + esc(m.stage) + '</b></td><td>' + esc(m.lens) + '</td><td class="note">' + esc(m.why) + '</td></tr>'; }).join('');
    document.getElementById('source-list').innerHTML = Object.keys(D.sources || {}).map(function (k) { var sc = D.sources[k]; return '<li><a href="' + sc.url + '">' + esc(sc.title) + '</a> (' + sc.year + ')' + (sc.note ? ' — <span class="note">' + esc(sc.note) + '</span>' : '') + '</li>'; }).join('');
    document.getElementById('ev-json').href = DATA; document.getElementById('tr-json').href = TRADE;
    var rel = (D.related || []).map(function (r) { return '<a href="' + esc(r.href) + '">' + esc(r.label) + '</a>'; });
    // cross-link into the material-profile / analysis world when this chain maps to a tracked material
    var CHAIN2PROFILE = {
      'antimony-chain':'antimony','arsenic-chain':'arsenic','baryte-chain':'baryte','beryllium-chain':'beryllium',
      'boron-chain':'boron','cobalt-chain':'cobalt','copper-chain':'copper','fluorine-chain':'fluorspar',
      'gallium-chain':'gallium','germanium-chain':'germanium','graphite-chain':'graphite','helium-chain':'helium',
      'lithium-chain':'lithium','magnesium-chain':'magnesium','magnet-chain':'magnets','manganese-chain':'manganese',
      'nickel-chain':'nickel','phosphate-food-chain':'phosphate','silicon-chip':'silicon','strontium-chain':'strontium',
      'tantalum-chain':'tantalum','titanium-chain':'titanium','tungsten-chain':'tungsten','vanadium-chain':'vanadium',
      'aluminium-chain':'bauxite','pgm-catalyst-chain':'platinum','zirconium-chain':'hafnium',
      'steel-alloys-chain':'niobium','steel-chain':'cokingcoal'
    };
    var _parts = location.pathname.replace(/\/$/, '').split('/'), _folder = _parts[_parts.length - 2] || '';
    var _prof = CHAIN2PROFILE[_folder];
    var profLink = _prof ? '<br><b>This material:</b> <a href="../profile-' + _prof + '">' + esc(_prof.charAt(0).toUpperCase() + _prof.slice(1)) + ' profile (reserves &middot; mine &middot; refine &middot; trade)</a> &nbsp;&middot;&nbsp; <a href="../risk">supply-risk index</a>' : '';
    var strip = '<div class="panel" style="margin-top:1.6rem"><h3 style="margin-top:0">Explore the layer</h3><p style="margin:0;line-height:1.9">' +
      '<a href="../value-chains">All value chains</a> &nbsp;·&nbsp; <a href="../chokepoint-map">The Chokepoint Map</a>' +
      profLink +
      (rel.length ? '<br><b>Related chains:</b> ' + rel.join(' &nbsp;·&nbsp; ') : '') + '</p></div>';
    document.querySelector('article').insertAdjacentHTML('beforeend', strip);
    var cl = document.getElementById('conflegend');
    if (cl) cl.innerHTML = 'Confidence: <span class="conf measured">measured</span> reported figure · <span class="conf estimate">estimate</span> published estimate · <span class="conf snapshot">snapshot</span> single-year, no long series · <span class="conf proxy">proxy</span> mixed/indirect.';
    if (T && T.years && T.years.length && T.codes) { var ts = document.getElementById('trade-slider'); ts.max = T.years.length - 1; ts.value = T.years.length - 1; ts.oninput = function () { tradeRow(T, +ts.value); }; tradeRow(T, +ts.value); }
    else { document.getElementById('trade-body').innerHTML = '<tr><td colspan="4" class="note">Trade JSON not built yet — run the chain’s extract_baci.py.</td></tr>'; }
    // Clickable estimate: if this chain's chokepoint is an estimate, load its basis and make every
    // 'estimate' tag on the page open how it was derived + its limits.
    fetch('../basis.json').then(function (r) { return r.ok ? r.json() : null; }).then(function (B) {
      if (!B) return;
      var parts = location.pathname.split('/').filter(Boolean);
      var folder = parts[parts.length - 2] || '';
      var b = B[folder.replace(/-chain$/, '')];
      if (!b) return;
      [].forEach.call(document.querySelectorAll('.conf.estimate'), function (t) {
        t.classList.add('clickable'); t.setAttribute('title', 'how this estimate was derived — click');
        t.addEventListener('click', function (e) { e.stopPropagation(); showBasisPop(t, b); });
      });
      var cor = document.getElementById('correction');
      if (cor && D.chokepoint && D.chokepoint.conf === 'estimate') {
        cor.insertAdjacentHTML('beforeend', ' <button class="basislink">How this estimate was derived, and its limits</button>');
        var bl = cor.querySelector('.basislink');
        bl.addEventListener('click', function (e) { e.stopPropagation(); showBasisPop(bl, b); });
      }
      var lg = document.getElementById('conflegend');
      if (lg) lg.insertAdjacentHTML('beforeend', ' <span class="note">— an <b>estimate</b> tag is clickable: it opens how the figure was derived and its limits.</span>');
    }).catch(function () { });
    document.addEventListener('click', function (e) { if (!(e.target.closest && (e.target.closest('.bpop') || e.target.closest('.conf.estimate') || e.target.closest('.basislink')))) closeBasisPop(); });
  }).catch(function (err) { document.querySelector('article').insertAdjacentHTML('afterbegin', '<div class="callout hot"><b>Evidence JSON did not load.</b> Serve the repository over HTTP.</div>'); console.error(err); });
})();

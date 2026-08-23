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
  function barsHTML(rows, max) {
    var m = max || Math.max.apply(null, rows.map(function (r) { return r.value || 0; })) || 1;
    return '<div class="bars">' + rows.map(function (r) {
      var v = r.value, w = v == null ? 0 : Math.max(2, v / m * 100);
      var show = v == null ? 'n/a' : (r.fmt === 'pct0' ? Math.round(v) + '%' : (v <= 1 ? Math.round(v * 100) + '%' : v.toLocaleString()));
      return '<div class="barrow"><b>' + esc(r.label) + '</b><span class="track"><span class="fill" style="width:' + w + '%"></span></span><span class="num">' + show + '</span></div>';
    }).join('') + '</div>';
  }
  function panelHTML(p) {
    var inner = '';
    if (p.h3) inner += '<h3>' + esc(p.h3) + conf(p.conf) + '</h3>';
    if (p.kind === 'bars') inner += barsHTML(p.bars, p.max);
    else if (p.kind === 'big') inner += '<p class="big">' + esc(p.big) + '</p><p>' + esc(p.text) + '</p>';
    else if (p.kind === 'text') inner += '<p style="margin-top:0">' + esc(p.text) + '</p>';
    else if (p.kind === 'cards') inner += '<div class="cards">' + p.cards.map(function (c) { return '<div class="card"><h4>' + esc(c.t) + '</h4><p>' + esc(c.d) + '</p></div>'; }).join('') + '</div>';
    if (p.note) inner += '<p class="note">' + esc(p.note) + '</p>';
    if (p.flag) inner += '<span class="flag">' + esc(p.flag) + '</span>';
    return '<div class="panel">' + inner + '</div>';
  }
  function historyChart(hist) {
    var W = 760, H = 230, pad = 42;
    var years = [], vals = [];
    hist.series.forEach(function (s) { s.points.forEach(function (p) { years.push(p.y); vals.push(p.v); }); });
    var y0 = Math.min.apply(null, years), y1 = Math.max.apply(null, years);
    var vmax = Math.min(100, Math.ceil(Math.max.apply(null, vals) / 10) * 10 + 5), vmin = 0;
    var px = function (y) { return pad + (y - y0) / (y1 - y0) * (W - 2 * pad); };
    var py = function (v) { return H - pad - (v - vmin) / (vmax - vmin) * (H - 2 * pad); };
    var s = '';
    [0, 25, 50, 75, 100].filter(function (g) { return g <= vmax; }).forEach(function (g) {
      s += '<line x1="' + pad + '" y1="' + py(g) + '" x2="' + (W - pad) + '" y2="' + py(g) + '" stroke="#e6e9e8"/><text x="6" y="' + (py(g) + 3) + '" font-size="9" fill="#68737a">' + g + '%</text>';
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
    document.getElementById('draftbar').innerHTML = 'Research pilot · unpublished <span>— ' + esc(D.title) + ', not part of the live Atlas</span>';
    document.getElementById('eyebrow').textContent = D.eyebrow || '';
    document.getElementById('h1').textContent = D.h1 || D.title;
    document.getElementById('deck').innerHTML = esc(D.deck).replace(/&lt;i&gt;/g, '<i>').replace(/&lt;\/i&gt;/g, '</i>');
    document.getElementById('byline').textContent = D.byline || '';
    document.getElementById('correction').innerHTML = '<b>The correction.</b> ' + esc(D.correction);
    document.getElementById('stats').innerHTML = (D.stats || []).map(function (st) { return '<div class="stat"><div class="v">' + st.v + '</div><div class="l">' + st.l + conf(st.conf) + '</div></div>'; }).join('');
    document.getElementById('chain').innerHTML = (D.hops || []).map(function (h) { return '<div class="hop"><div class="n">' + esc(h.n) + '</div><div class="t">' + esc(h.t) + '</div></div>'; }).join('');
    if (D.history && D.history.series && D.history.series.length) {
      var wrap = document.getElementById('history-wrap');
      wrap.innerHTML = '<h2>' + esc(D.history.title) + conf(D.history.conf) + '</h2><div class="panel">' + historyChart(D.history) + '<p class="note">' + esc(D.history.note || '') + '</p></div>';
    }
    document.getElementById('sections').innerHTML = (D.sections || []).map(function (sec) {
      var ps = sec.panels || [];
      var wrap = ps.length === 2 ? '<div class="split">' + ps.map(panelHTML).join('') + '</div>' : ps.map(panelHTML).join('');
      return '<h2>' + esc(sec.h2) + '</h2>' + wrap;
    }).join('');
    document.getElementById('trade-intro').textContent = D.trade_intro || '';
    document.getElementById('method-body').innerHTML = (D.method || []).map(function (m) { return '<tr><td><b>' + esc(m.stage) + '</b></td><td>' + esc(m.lens) + '</td><td class="note">' + esc(m.why) + '</td></tr>'; }).join('');
    document.getElementById('source-list').innerHTML = Object.keys(D.sources || {}).map(function (k) { var sc = D.sources[k]; return '<li><a href="' + sc.url + '">' + esc(sc.title) + '</a> (' + sc.year + ')' + (sc.note ? ' — <span class="note">' + esc(sc.note) + '</span>' : '') + '</li>'; }).join('');
    document.getElementById('ev-json').href = DATA; document.getElementById('tr-json').href = TRADE;
    var cl = document.getElementById('conflegend');
    if (cl) cl.innerHTML = 'Confidence: <span class="conf measured">measured</span> reported figure · <span class="conf estimate">estimate</span> published estimate · <span class="conf snapshot">snapshot</span> single-year, no long series · <span class="conf proxy">proxy</span> mixed/indirect.';
    if (T && T.years && T.years.length) { var ts = document.getElementById('trade-slider'); ts.max = T.years.length - 1; ts.value = T.years.length - 1; ts.oninput = function () { tradeRow(T, +ts.value); }; tradeRow(T, +ts.value); }
    else { document.getElementById('trade-body').innerHTML = '<tr><td colspan="4" class="note">Trade JSON not built yet — run the chain’s extract_baci.py.</td></tr>'; }
  }).catch(function (err) { document.querySelector('article').insertAdjacentHTML('afterbegin', '<div class="callout hot"><b>Evidence JSON did not load.</b> Serve the repository over HTTP.</div>'); console.error(err); });
})();

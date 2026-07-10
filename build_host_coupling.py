#!/usr/bin/env python3
"""
Host coupling — testing the mechanism: does a companion's price track its HOST, not its own demand?

Child of the price-test page. That page found by-product metals split in price direction by their host's
cycle. This one tests the mechanism head-on: correlate each companion metal's price against its host
commodity's price (World Bank Pink Sheet spot prices, 2002-2024), and against the general base-metals cycle
as a control. If a companion tracks its specific host more than the common commodity cycle, the "host decides"
claim has direct evidence.

Companion price = the atlas's implied trade unit value (volume.json). Host price = Pink Sheet annual average.
We correlate annual log-returns, and compare corr(companion, host) with corr(companion, base-metals index).
Caveats: trade unit values are noisy proxies for price; all commodities co-move on the macro cycle (a common
factor inflates every correlation); ~22 annual points. A directional mechanism test. Public data; deterministic.
Run: python build_host_coupling.py
"""
import json, os, math

ROOT = os.path.dirname(os.path.abspath(__file__))
vol = json.load(open(os.path.join(ROOT, 'out', 'volume.json'), encoding='utf8'))
comp = json.load(open(os.path.join(ROOT, 'out', 'companionality.json'), encoding='utf8'))
YEARS = vol['years']
CO = {r['label']: r for r in comp['rows']}

# --- parse World Bank Pink Sheet -> annual host prices ---
import openpyxl
PINK = os.path.join(ROOT, 'raw', 'pink', 'pink.xlsx')
COLS = {'coal': 5, 'natural gas': 7, 'phosphate': 57, 'aluminum': 62, 'iron ore': 63,
        'copper': 64, 'lead': 65, 'tin': 66, 'nickel': 67, 'zinc': 68, 'gold': 69, 'platinum': 70}
wb = openpyxl.load_workbook(PINK, read_only=True, data_only=True)
ws = wb['Monthly Prices']
acc = {k: {} for k in COLS}   # commodity -> {year: [sum, n]}
for row in ws.iter_rows(min_row=7, values_only=True):
    d = row[0]
    if not d or 'M' not in str(d):
        continue
    try:
        yr = int(str(d)[:4])
    except ValueError:
        continue
    for k, j in COLS.items():
        v = row[j] if j < len(row) else None
        if isinstance(v, (int, float)):
            s = acc[k].setdefault(yr, [0.0, 0]); s[0] += v; s[1] += 1
host_price = {k: {y: (s[0] / s[1]) for y, s in yrs.items() if s[1] >= 6} for k, yrs in acc.items()}

def annual_series(price_by_year):
    return [price_by_year.get(y) for y in YEARS]

def logrets(series):
    out = []
    for i in range(1, len(series)):
        a, b = series[i - 1], series[i]
        out.append(math.log(b / a) if (a and b and a > 0 and b > 0) else None)
    return out

def pearson_aligned(xr, yr):
    xs, ys = [], []
    for x, y in zip(xr, yr):
        if x is not None and y is not None:
            xs.append(x); ys.append(y)
    n = len(xs)
    if n < 6:
        return None, n
    mx = sum(xs) / n; my = sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs); syy = sum((b - my) ** 2 for b in ys)
    if sxx <= 0 or syy <= 0:
        return None, n
    return round(sxy / math.sqrt(sxx * syy), 2), n

# base-metals cycle = mean price of Al/Cu/Pb/Ni/Sn/Zn per year, then log-returns
base_metals = ['aluminum', 'copper', 'lead', 'nickel', 'tin', 'zinc']
base_series = []
for y in YEARS:
    vals = [host_price[m].get(y) for m in base_metals]
    vals = [v for v in vals if v]
    base_series.append(sum(vals) / len(vals) if len(vals) == len(base_metals) else None)
base_ret = logrets(base_series)

# companion -> host commodities (Pink Sheet labels)
PAIRS = {
    'cobalt':    ['copper', 'nickel'],
    'gallium':   ['aluminum', 'zinc'],
    'germanium': ['zinc', 'coal'],
    'helium':    ['natural gas'],
    'vanadium':  ['iron ore'],
    'arsenic':   ['copper', 'lead', 'gold'],
    'antimony':  ['lead', 'zinc', 'gold'],
    'palladium': ['platinum', 'nickel'],
    'tantalum':  ['tin'],
    'magnets':   ['iron ore'],
}
HOSTNM = {'aluminum': 'aluminium', 'iron ore': 'iron ore', 'natural gas': 'natural gas'}

rows = []
for lab, hosts in PAIRS.items():
    mv = vol['materials'].get(lab)
    if not mv:
        continue
    cret = logrets(mv.get('uv') or [])
    base_corr, _ = pearson_aligned(cret, base_ret)
    hostcorrs = []
    for h in hosts:
        hr = logrets(annual_series(host_price.get(h, {})))
        c, n = pearson_aligned(cret, hr)
        if c is not None:
            hostcorrs.append({'host': HOSTNM.get(h, h), 'corr': c, 'n': n})
    if not hostcorrs:
        continue
    best = max(hostcorrs, key=lambda d: d['corr'])
    rows.append({
        'label': lab, 'title': CO.get(lab, {}).get('title', lab),
        'class': CO.get(lab, {}).get('class', 'primary'),
        'companionality_pct': CO.get(lab, {}).get('companionality_pct', 0),
        'hosts': hostcorrs, 'best_host': best['host'], 'best_corr': best['corr'],
        'base_corr': base_corr,
        'host_specific': (base_corr is not None and best['corr'] - base_corr >= 0.1),
    })

rows.sort(key=lambda r: -(r['best_corr'] if r['best_corr'] is not None else -9))
tracked = [r for r in rows if r['best_corr'] is not None and r['best_corr'] >= 0.4]
host_specific = [r for r in rows if r['host_specific']]
valid_best = [r['best_corr'] for r in rows if r['best_corr'] is not None]
mean_best = round(sum(valid_best) / len(valid_best), 2) if valid_best else None

out = {
    'generated': comp.get('generated'),
    'window': f'{YEARS[0]}-{YEARS[-1]}',
    'n': len(rows),
    'mean_best_host_corr': mean_best,
    'n_tracked': len(tracked),
    'tracked_names': [r['title'] for r in tracked],
    'n_host_specific': len(host_specific),
    'host_specific_names': [r['title'] for r in host_specific],
    'rows': rows,
    'source': 'World Bank Pink Sheet (host spot prices) x atlas implied unit values (companions).',
}
os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'out', 'host_coupling.json'), 'w', encoding='utf8'),
          separators=(',', ':'))
print('wrote out/host_coupling.json')
print(f"  mean best host-corr {mean_best} | track host (>=0.4): {', '.join(out['tracked_names'])}")
print(f"  host-specific (beats base cycle): {', '.join(out['host_specific_names'])}")

HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Host coupling — does a companion track its host, not its own demand? · Critical Materials Atlas</title>
<meta name="description" content="Direct test of the mechanism behind the squeeze: correlate each by-product metal's price against its host commodity (World Bank Pink Sheet), and against the general base-metals cycle as a control. Which companions are genuinely gated by their host?">
<meta property="og:title" content="Does a by-product metal's price track its host? A mechanism test">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<style>
 .muted{color:#5a6b68;font-size:.86rem}
 .stat4{display:grid;grid-template-columns:repeat(4,1fr);gap:.9rem;margin:1.2rem 0}
 @media(max-width:720px){.stat4{grid-template-columns:repeat(2,1fr)}}
 .stat{background:#fff;border:1px solid #e3e9e8;border-left:4px solid #0e7c74;border-radius:10px;padding:.8rem .9rem}
 .stat .v{font-size:1.5rem;font-weight:800;color:#15323a;letter-spacing:-.02em}
 .stat .l{font-size:.76rem;color:#5a6b68;margin-top:.15rem;line-height:1.35}
 table.tidy{width:100%;border-collapse:collapse;font-size:.87rem;margin:.4rem 0}
 table.tidy th,table.tidy td{padding:.4rem .5rem;border-bottom:1px solid #eef1f0;text-align:left}
 table.tidy th.n,table.tidy td.n{text-align:right;font-variant-numeric:tabular-nums}
 .cbar{display:grid;grid-template-columns:130px 1fr 150px;align-items:center;gap:.6rem;margin:.28rem 0;font-size:.86rem}
 .cbar .nm{text-align:right;font-weight:600;color:#15323a}
 .cbar .track{position:relative;background:#eef3f2;border-radius:5px;height:20px}
 .cbar .zero{position:absolute;left:50%;top:0;bottom:0;width:1px;background:#c9d2d0}
 .cbar .fill{position:absolute;top:0;bottom:0;border-radius:4px}
 .cbar .meta{color:#5a6b68;font-size:.78rem}
 .keyline{background:#f2f6f5;border:1px solid #d9e6e3;border-left:4px solid #0e7c74;border-radius:10px;padding:.9rem 1.1rem;margin:1.2rem 0}
 .keyline b{color:#0e7c74}
</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="price-squeeze.html">Price test</a><a href="host-shock.html">Host shock</a>
  <a href="companionality.html" class="hideable">Hostage metals</a><a href="limitations.html" class="hideable">Limitations</a>
  <a href="https://github.com/materials-atlas/comtrade-reconcile" class="hideable">Engine</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · mechanism · falsification</div>
  <h1>Does the companion follow its host?</h1>
  <p class="deck">The <a href="price-squeeze.html" style="color:#fff;text-decoration:underline">price test</a> claimed a by-product metal&rsquo;s fate is set by its host&rsquo;s cycle, not its own demand. That is a mechanism, and mechanisms can be checked. So: correlate each companion&rsquo;s price against its <b>host commodity</b> (World Bank spot prices) &mdash; and against the general metals cycle as a control &mdash; and see which companions are genuinely gated by the metal they ride on.</p>
</div></section>
<article style="max-width:1040px">
  <div class="callout"><span id="lead"></span>
  <details class="howto"><summary>How the coupling is measured (and the confound)</summary>
  <p>Host prices are <b>World Bank Pink Sheet</b> spot prices (aluminium, copper, nickel, zinc, lead, tin, iron ore, gold, platinum, coal, gas), annual 2002&ndash;2024. Companion prices are the atlas&rsquo;s implied trade unit values. We correlate annual <b>log-returns</b>, companion vs host, and report the best-matching host. As a control we also correlate each companion against a <b>base-metals cycle</b> (mean of the six LME base metals) &mdash; a companion is <b>host-specific</b> only if it tracks its own host clearly more than the common cycle.</p>
  <p class="howto-src"><b>Confound (important):</b> all commodities co-move on the macro cycle, so every correlation is inflated by a common factor &mdash; that is exactly why the base-cycle control matters. Trade unit values are noisy; ~22 annual points; hafnium/zirconium and a few hosts have no spot series. Directional evidence, not proof of causation. Inputs: <a href="out/volume.json">volume.json</a> &times; Pink Sheet &rarr; <a href="out/host_coupling.json">host_coupling.json</a>.</p>
  </details></div>

  <div class="stat4" id="stats"></div>

  <div class="keyline" id="keyline"></div>

  <h2 style="margin:1.6rem 0 .3rem">Companion &harr; host price coupling</h2>
  <p class="muted" style="margin-top:0">Bar = correlation of each companion&rsquo;s price with its best-matching host (annual log-returns, 2002&ndash;24). The marker shows the base-metals-cycle control: a bar reaching well past its <span style="color:#b07a18">◆</span> is genuinely host-specific, not just riding the general cycle.</p>
  <div id="bars"></div>

  <h2 style="margin:1.6rem 0 .3rem">Every pair, with the cycle control</h2>
  <table class="tidy" id="tab"><thead><tr><th>Companion</th><th>host(s)</th><th class="n">corr with host</th><th class="n">corr with base cycle</th><th>verdict</th></tr></thead><tbody></tbody></table>

  <h2 style="margin:1.8rem 0 .3rem">Where the chain of reasoning has arrived</h2>
  <p>Five layers ago the atlas noticed satellites can&rsquo;t name a mineral; that opened companionality, which opened the squeeze, which opened the price test, which posed this mechanism &mdash; and here it either holds or it doesn&rsquo;t, in public data. Where a companion tracks its host tightly and beyond the common cycle, the &ldquo;host decides&rdquo; story is earned; where it doesn&rsquo;t, the honest read is that trade unit values are too coarse to see it, or the metal has enough of its own market to break free. Either way the next child is set: swap noisy trade unit values for real reported prices where they exist (cobalt, lithium, the PGMs) and re-run the coupling on clean series. The atlas keeps interrogating its own last answer.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="price-squeeze.html">Price test</a><br><a href="host-shock.html">Host shock</a><br><a href="companionality.html">Hostage metals</a><br><a href="limitations.html">Limitations</a></div>
  <div><h4>Sources</h4>World Bank Pink Sheet (host spot prices) × atlas implied unit values (companions)</div>
  <div class="fineprint">Commodities co-move on the macro cycle; the base-cycle control separates host-specific coupling from the common factor.</div>
</div></footer>
<script>
fetch('out/host_coupling.json').then(r=>r.json()).then(S=>{
  document.getElementById('lead').innerHTML='<b>Result:</b> '+S.n_tracked+' of '+S.n+' by-product metals track their host&rsquo;s price at r&ge;0.4 (mean best-host correlation '+S.mean_best_host_corr+'), and '+S.n_host_specific+' do so <i>beyond</i> the general commodity cycle &mdash; '+(S.host_specific_names.join(', ')||'none clearly')+'. The &ldquo;host decides&rdquo; mechanism is visible for some pairs and lost in the noise for others, which is the honest state of the evidence.';
  const stats=[
    {v:S.mean_best_host_corr,l:'mean correlation of a companion with its best-matching host (log-returns)'},
    {v:S.n_tracked+' / '+S.n,l:'companions that track a host at r ≥ 0.4'},
    {v:S.n_host_specific,l:'host-specific: track their own host clearly more than the base-metals cycle'},
    {v:S.window,l:'annual price window (World Bank Pink Sheet)'},
  ];
  document.getElementById('stats').innerHTML=stats.map(s=>'<div class="stat"><div class="v">'+s.v+'</div><div class="l">'+s.l+'</div></div>').join('');
  document.getElementById('keyline').innerHTML='<b>What passes the control:</b> a positive host correlation alone proves little &mdash; everything rose in the 2000s supercycle and fell after. The metals that clear the base-cycle bar are the ones whose <i>own</i> host, specifically, moves them. Those are the pairs where a host-shock model earns its keep; the rest are a caution that this test needs cleaner price series than trade unit values can give.';
  // bars
  const rows=S.rows.slice();
  const mkbar=r=>{
    const c=r.best_corr, b=r.base_corr;
    const cx=Math.max(-1,Math.min(1,c||0)), bx=(b==null?null:Math.max(-1,Math.min(1,b)));
    const w=Math.abs(cx)*50, left=cx>=0?50:50-w;
    const col=r.host_specific?'#0e7c74':(cx>=0?'#7d9b97':'#c98a8a');
    const bmark=bx==null?'':'<span style="position:absolute;top:-2px;left:'+(50+bx*50)+'%;color:#b07a18;font-size:.7rem;transform:translateX(-50%)" title="base-metals cycle control r='+b+'">&#9670;</span>';
    return '<div class="cbar"><div class="nm">'+r.title+'</div>'+
      '<div class="track"><div class="zero"></div><div class="fill" style="left:'+left+'%;width:'+w+'%;background:'+col+'"></div>'+bmark+'</div>'+
      '<div class="meta">r='+(c==null?'–':c)+' vs '+r.best_host+(r.host_specific?' <b style="color:#0e7c74">·host-specific</b>':'')+'</div></div>';
  };
  document.getElementById('bars').innerHTML=rows.map(mkbar).join('');
  // table
  const tb=document.querySelector('#tab tbody');
  rows.forEach(r=>{
    const hs=r.hosts.map(h=>h.host+' ('+h.corr+')').join(', ');
    let v='—';
    if(r.best_corr==null) v='no series';
    else if(r.host_specific) v='<b style="color:#0e7c74">tracks host, beyond cycle</b>';
    else if(r.best_corr>=0.4) v='tracks host, ~ with cycle';
    else if(r.best_corr>=0) v='weak coupling';
    else v='decoupled';
    const tr=document.createElement('tr');
    tr.innerHTML='<td><b>'+r.title+'</b></td><td class="muted" style="font-size:.82rem">'+hs+'</td>'+
      '<td class="n" style="font-weight:600">'+(r.best_corr==null?'–':r.best_corr)+'</td>'+
      '<td class="n">'+(r.base_corr==null?'–':r.base_corr)+'</td><td class="muted" style="font-size:.82rem">'+v+'</td>';
    tb.appendChild(tr);
  });
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'host-coupling.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('wrote host-coupling.html')

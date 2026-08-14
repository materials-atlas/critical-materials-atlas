#!/usr/bin/env python3
"""
Governance-weighted criticality — replicating the EU/SCRREEN and Graedel supply-risk logic, and comparing
the reordered ranking to our own transparent index.

The ingredient our index lacks is GOVERNANCE: the same concentration is riskier in a low-governance
jurisdiction than in a stable democracy. Using World Bank WGI we form a governance-risk weight
  g_c = clip( (2.5 - WGI_c) / 5 , 0, 1 )                      (0 = best governed, 1 = worst)
and the governance-weighted Herfindahl
  HHI_WGI(stage) = sum_c share_c^2 * g_c .

EU-style supply risk (global perspective; bottleneck = the stage with the higher governance-weighted HHI):
  SR_EU = max( HHI_WGI_production , HHI_WGI_trade ) * (1 - EOL_RIR) * SI
with substitutability SI in {high:1.0, medium:0.8, low:0.6} (good substitutes reduce risk).

Graedel/Yale-style supply-risk axis from the components we actually hold (depletion-time and environmental
implications are omitted - no absolute reserves/production tonnage, no LCA data - and that omission is
stated):
  SR_Graedel = mean( 100*HHI_prod, 100*governance_exposure, 100*(1-EOL_RIR), 100*SI )

We then rank materials by EU-SR, Graedel-SR and our own index, report rank correlations, and isolate what
the GOVERNANCE weighting changes vs an identical un-weighted index (which materials rise because they sit in
low-governance jurisdictions, which fall). Public data; deterministic.

Writes out/criticality.json + criticality.html.  Run:  python build_criticality.py  (needs out/wgi.json)
"""
import json, os, html

ROOT = os.path.dirname(os.path.abspath(__file__))
YEAR = os.environ.get('PROFILE_YEAR', '2024')
flows = json.load(open(os.path.join(ROOT, 'out', f'flows_{YEAR}.json'), encoding='utf8'))
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
WGI = json.load(open(os.path.join(ROOT, 'out', 'wgi.json'), encoding='utf8'))['wgi']
try:
    RISK = {r['label']: r['score'] for r in json.load(open(os.path.join(ROOT, 'out', 'risk.json'), encoding='utf8'))['materials']}
except Exception:
    RISK = {}
NAMES = flows.get('names', {})
TITLES = {m['label']: m['title'].split(' (')[0] for m in data['materials']}
SHARED = {'gallium', 'germanium'}
SI_MAP = {'high': 1.0, 'medium': 0.8, 'low': 0.6}
G_DEFAULT = 0.6   # governance risk for countries WGI doesn't cover (treated as moderately risky)

def cname(i): return NAMES.get(i, i)
def e(s): return html.escape(str(s), quote=True)
def flag(iso):
    if not iso or len(iso) != 2 or not iso.isalpha(): return ''
    return ''.join(chr(0x1F1E6 + ord(c.upper()) - 65) for c in iso)

def grisk(iso):
    w = WGI.get(iso)
    if w is None:
        return G_DEFAULT
    return max(0.0, min(1.0, (2.5 - w) / 5.0))

def export_shares(label):
    o, tot = {}, 0.0
    for f in flows.get('materials', {}).get(label) or []:
        o[f['from']] = o.get(f['from'], 0.0) + f['value']; tot += f['value']
    return ({k: v / tot for k, v in o.items()}, tot) if tot else ({}, 0.0)

def spearman(a, b):
    n = len(a)
    if n < 3: return None
    def ranks(x):
        order = sorted(range(n), key=lambda i: x[i])
        r = [0] * n
        for rank, i in enumerate(order): r[i] = rank
        return r
    ra, rb = ranks(a), ranks(b)
    mra, mrb = sum(ra) / n, sum(rb) / n
    num = sum((ra[i] - mra) * (rb[i] - mrb) for i in range(n))
    da = sum((ra[i] - mra) ** 2 for i in range(n)) ** 0.5
    db = sum((rb[i] - mrb) ** 2 for i in range(n)) ** 0.5
    return round(num / (da * db), 2) if da and db else None

rows = []
for m in data['materials']:
    label = m['label']
    mined = m.get('mined') or []
    si = SI_MAP.get(m.get('substitutability'), 0.8)
    eol = (m.get('recycling') or 0) / 100.0
    # production stage
    prod_hhi = sum((x['v'] / 100.0) ** 2 for x in mined)
    prod_hhi_wgi = sum((x['v'] / 100.0) ** 2 * grisk(x['c']) for x in mined)
    gov_exposure = sum((x['v'] / 100.0) * grisk(x['c']) for x in mined)   # production-weighted governance risk
    top_mine = mined[0]['c'] if mined else None
    msum = sum(x['v'] for x in mined) or 1
    gov_wavg = sum(x['v'] * grisk(x['c']) for x in mined) / msum if mined else None   # production-weighted producer risk
    sig = [x for x in mined if x['v'] >= 10]                               # the worst-governance SIGNIFICANT producer
    worst = max(sig, key=lambda x: grisk(x['c'])) if sig else (mined[0] if mined else None)
    # trade stage
    sh, _ = export_shares(label)
    trade_hhi = sum(s ** 2 for s in sh.values())
    trade_hhi_wgi = sum(s ** 2 * grisk(c) for c, s in sh.items())
    # EU-style SR: governance-weighted (bottleneck stage) and an un-weighted twin for the governance delta
    sr_eu_raw = max(prod_hhi_wgi, trade_hhi_wgi) * (1 - eol) * si
    sr_plain_raw = max(prod_hhi, trade_hhi) * (1 - eol) * si
    graedel = (100 * prod_hhi + 100 * gov_exposure + 100 * (1 - eol) + 100 * si) / 4
    rows.append({'label': label, 'title': TITLES[label], 'shared': label in SHARED,
                 'top_mine': top_mine, 'gov_top': round(grisk(top_mine), 2) if top_mine else None,
                 'gov_wavg': round(gov_wavg, 2) if gov_wavg is not None else None,
                 'worst_c': worst['c'] if worst else None,
                 'worst_g': round(grisk(worst['c']), 2) if worst else None,
                 'sr_eu_raw': sr_eu_raw, 'sr_plain_raw': sr_plain_raw,
                 'graedel': round(graedel, 1), 'ours': RISK.get(label)})

def minmax(vals):
    lo, hi = min(vals), max(vals)
    return [round((v - lo) / (hi - lo) * 100, 1) if hi > lo else 0.0 for v in vals]

eu = minmax([r['sr_eu_raw'] for r in rows])
plain = minmax([r['sr_plain_raw'] for r in rows])
for r, a, b in zip(rows, eu, plain):
    r['eu_score'], r['plain_score'] = a, b

# governance effect = rise in rank when you switch from un-weighted to governance-weighted
def rank_desc(key):
    order = sorted(rows, key=lambda r: r[key], reverse=True)
    return {id(r): i + 1 for i, r in enumerate(order)}
r_eu, r_plain = rank_desc('eu_score'), rank_desc('plain_score')
for r in rows:
    r['gov_delta'] = r_plain[id(r)] - r_eu[id(r)]   # +ve = governance weighting pushed it UP the risk list

rows.sort(key=lambda r: r['eu_score'], reverse=True)

# rank correlations across frameworks (only materials we score in all)
common = [r for r in rows if r['ours'] is not None]
corr = {
    'eu_vs_ours': spearman([r['eu_score'] for r in common], [r['ours'] for r in common]),
    'graedel_vs_ours': spearman([r['graedel'] for r in common], [r['ours'] for r in common]),
    'eu_vs_graedel': spearman([r['eu_score'] for r in rows], [r['graedel'] for r in rows]),
}
promoted = sorted(rows, key=lambda r: r['gov_delta'], reverse=True)[:5]
demoted = sorted(rows, key=lambda r: r['gov_delta'])[:5]

json.dump({'year': YEAR, 'wgi_source': 'World Bank WGI', 'correlations': corr,
           'materials': rows}, open(os.path.join(ROOT, 'out', 'criticality.json'), 'w', encoding='utf8'), indent=1)

# ---- page ----
motif = ('<svg class="hero-motif" viewBox="0 0 560 560" fill="none" aria-hidden="true"><g stroke="#7fd2c8" stroke-opacity=".15" stroke-width="1.1"><circle cx="280" cy="280" r="232"/><ellipse cx="280" cy="280" rx="232" ry="62"/><ellipse cx="280" cy="280" rx="232" ry="132"/><ellipse cx="280" cy="280" rx="232" ry="196"/><ellipse cx="280" cy="280" rx="62" ry="232"/><ellipse cx="280" cy="280" rx="132" ry="232"/><ellipse cx="280" cy="280" rx="196" ry="232"/><line x1="280" y1="48" x2="280" y2="512"/><line x1="48" y1="280" x2="512" y2="280"/></g><g stroke="#9be3da" stroke-opacity=".26" stroke-width="1.4" fill="none"><path d="M120 360 Q 300 110 472 248"/><path d="M158 196 Q 322 300 442 422"/><path d="M120 360 Q 268 430 442 422"/></g><g fill="#bff0e8" fill-opacity=".55"><circle cx="120" cy="360" r="4.2"/><circle cx="472" cy="248" r="4.2"/><circle cx="158" cy="196" r="4.2"/><circle cx="442" cy="422" r="4.2"/></g></svg>')

def gdelta(d):
    if d > 1: return f'<span style="color:#c0392b">▲ {d}</span>'
    if d < -1: return f'<span style="color:#3f9b46">▼ {-d}</span>'
    return '<span style="color:#9aa6ad">·</span>'

mr = []
for i, r in enumerate(rows, 1):
    gc = r['gov_wavg'] if r['gov_wavg'] is not None else r['gov_top']
    gcol = '#c0392b' if gc and gc >= 0.7 else '#b35e16' if gc and gc >= 0.5 else '#3f9b46'
    ours = f'{r["ours"]}' if r['ours'] is not None else '—'
    mr.append(
        f'<tr><td class="n" style="color:#9aa6ad">{i}</td>'
        f'<td><a href="profile-{e(r["label"])}.html">{e(r["title"])}</a>{" ⛓" if r["shared"] else ""}</td>'
        f'<td class="n" style="font-weight:800;color:#15323a">{r["eu_score"]:.0f}</td>'
        f'<td class="n">{r["graedel"]:.0f}</td>'
        f'<td class="n" style="color:#9aa6ad">{ours}</td>'
        f'<td>{flag(r["top_mine"])} <span style="color:{gcol}">{gc:.2f}</span></td>'
        f'<td class="n">{gdelta(r["gov_delta"])}</td></tr>')

def namelist(rs, key='top'):
    out = []
    for r in rs:
        c, g = (r['worst_c'], r['worst_g']) if key == 'worst' and r.get('worst_c') else (r['top_mine'], r['gov_top'])
        gtxt = f' g{g}' if g is not None else ''
        out.append(f'{e(r["title"])} <span style="color:#9aa6ad">({flag(c)}{e(cname(c))}{gtxt})</span>')
    return ', '.join(out)

def corrtxt(v): return f'{v:+.2f}' if v is not None else 'n/a'

out = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Governance-weighted criticality — Critical Materials Atlas</title>
<meta name="description" content="Replicating the EU/SCRREEN and Graedel supply-risk methods on public data: concentration weighted by World Bank governance scores, and how the governance weighting reorders the risk list vs a transparent index.">
<meta property="og:title" content="Governance-weighted criticality">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="methodology.html">Methodology</a><a href="findings.html">Findings</a>
  <a href="risk.html" class="hideable">Risk</a><a href="network.html" class="hideable">Network</a>
  <a href="https://github.com/materials-atlas/critical-materials-atlas" class="hideable">Engine</a></nav>
</div></header>
<section class="hero">{motif}<div class="wrap">
  <div class="eyebrow">Method · established frameworks</div>
  <h1>Concentration in risky places</h1>
  <p class="deck">The official criticality methods (EU/SCRREEN, Graedel/Yale) add the ingredient our index leaves out: <i>governance</i>. The same concentration is more dangerous in a fragile state than in a stable democracy. Weighting by World Bank governance scores reorders the risk list — and shows exactly which materials move.</p>
</div></section>
<article style="max-width:1000px">
  <div class="callout">The same supply concentration is more dangerous when the producers are badly governed. Here I re-weight every material&rsquo;s concentration by the governance of its producers &mdash; and watch the risk list reorder.
  <details class="howto"><summary>How it&rsquo;s built</summary>
  <p>Each producer gets a governance-risk weight <code>g = (2.5 − WGI)/5</code> from the World Bank Worldwide Governance Indicators, which feeds a governance-weighted concentration score <code>Σ shareᵢ²·gᵢ</code>. From that I build an <b>EU/SCRREEN-shaped</b> supply-risk proxy (bottleneck-stage governance-weighted concentration, discounted by recycling, scaled by substitutability) and a <b>Graedel-style</b> supply-risk axis &mdash; both set beside my own index.</p>
  <p class="howto-src">These are proxies on public approximations, <b>not</b> the official EU or Yale scores (which use CRM-specific, stage-granular, expert-weighted inputs) &mdash; read it as a governance <i>lens</i>. Depletion-time and environmental axes are omitted (no tonnage/LCA data), and production concentration uses top-N mine shares. Computed by <code>build_criticality.py</code> from public data.</p>
  </details></div>

  <div class="callout" style="background:#f3f7f6">The rankings sit in the same family — Spearman ρ
  <b>{corrtxt(corr['eu_vs_ours'])}</b> (EU-shaped vs our index), <b>{corrtxt(corr['graedel_vs_ours'])}</b> (Graedel-shaped vs ours),
  <b>{corrtxt(corr['eu_vs_graedel'])}</b> (the two proxies) — but this is partly <i>mechanical</i>: all three share inputs
  (concentration, recycling, substitutability), so read it as "same family", not independent validation. What the
  <b>governance weighting changes</b>: it pushes <b>up</b> materials with a high-governance-risk producer in the mix —
  {namelist(promoted, 'worst')} — and <b>down</b> those mined in well-governed countries — {namelist(demoted, 'top')}.</div>

  <table>
    <thead><tr><th class="n">#</th><th>Material</th>
      <th class="n" title="EU/SCRREEN-style governance-weighted supply risk, scaled 0-100">EU-SR</th>
      <th class="n" title="Graedel/Yale-style supply-risk axis (no depletion/environmental)">Graedel</th>
      <th class="n" title="our transparent index, for comparison">ours</th>
      <th title="production-weighted governance risk of the producers: 0 best, 1 worst">producer risk</th>
      <th class="n" title="rank change from governance weighting (vs the same index un-weighted)">gov. effect</th></tr></thead>
    <tbody>{''.join(mr)}</tbody>
  </table>
  <p class="note">⛓ gallium and germanium share one HS6 code (811292; hafnium is separate). WGI: World Bank (mean of 6 estimates). Computed from <a href="out/data.json">data.json</a> + <a href="out/wgi.json">wgi.json</a> → <a href="out/criticality.json">criticality.json</a>.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="./">Interactive atlas</a><br><a href="risk.html">Supply-risk index</a><br><a href="network.html">Network chokepoints</a><br><a href="complexity.html">Economic complexity</a></div>
  <div><h4>Sources</h4>UN Comtrade · CEPII BACI<br>USGS · IEA · World Bank WGI</div>
  <div class="fineprint">Replication of published methods on public data; not the official EU or Yale assessment.</div>
</div></footer>
</body></html>'''
open(os.path.join(ROOT, 'criticality.html'), 'w', encoding='utf8', newline='\n').write(out)

print(f'wrote criticality.html + out/criticality.json')
print(f"Spearman: EU vs ours {corr['eu_vs_ours']}, Graedel vs ours {corr['graedel_vs_ours']}, EU vs Graedel {corr['eu_vs_graedel']}")
print('\nTOP EU governance-weighted supply risk:')
for r in rows[:8]:
    print(f"  {r['title']:<24} EU {r['eu_score']:.0f}  Graedel {r['graedel']:.0f}  ours {r['ours']}  lead-miner g {r['gov_top']}")
print('\nPROMOTED by governance (low-governance jurisdictions):')
for r in promoted:
    print(f"  {r['title']:<24} +{r['gov_delta']}  (mined {r['top_mine']}, g {r['gov_top']})")
print('DEMOTED by governance (well-governed):')
for r in demoted:
    print(f"  {r['title']:<24} {r['gov_delta']}  (mined {r['top_mine']}, g {r['gov_top']})")

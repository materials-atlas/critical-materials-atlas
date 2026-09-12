#!/usr/bin/env python3
"""
Origin trace — turning the descriptive "origin gap" into a traced, importer-level estimate.

The customs ledger names the EXPORTER (often a refiner or hub), not the mine. We re-attribute each
importer's purchases to a likely true origin using a transparent first-order rule on the data we have:

  for each flow  supplier q -> importer r  of material m, value v:
    if q genuinely mines m (mine share >= 5%)         -> origin = q          (genuine producer)
    else (q is a refiner / re-export hub)             -> origin = top mine    (re-attributed to the
                                                                              dominant producer of m)
  importer r's HIDDEN dependence = value re-attributed away from the apparent supplier / total imports.

This is the hybrid in the MRIO literature reduced to our data: P(mine o -> refiner q) collapsed to "the
material's dominant mine" because we don't observe individual refiner ore-sourcing. So it is a first-order
trace, stated as such — refiners are assumed to draw on the leading mine, which is conservative for the
"refiner illusion" it measures. We also compare, per material, the concentration of APPARENT suppliers
(trade Herfindahl) with that of EMBODIED origin (mine Herfindahl): where embodied > apparent, the refiner
layer makes supply look more diversified than it is.

Writes out/origin_trace.json + origin.html.  Public data; deterministic.
"""
import json, os, html

ROOT = os.path.dirname(os.path.abspath(__file__))
YEAR = os.environ.get('PROFILE_YEAR', '2024')
flows = json.load(open(os.path.join(ROOT, 'out', f'flows_{YEAR}.json'), encoding='utf8'))
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
NAMES = flows.get('names', {})
TITLES = {m['label']: m['title'].split(' (')[0] for m in data['materials']}
MINE = {m['label']: (m.get('mined') or []) for m in data['materials']}
HUBS = {'HK', 'SG', 'AE', 'PA', 'MO', 'GI', 'NL', 'BE'}
MINER_MIN = 5.0   # a supplier counts as a genuine producer of m if its world mine share >= 5%

def cname(i): return NAMES.get(i, i)
def e(s): return html.escape(str(s), quote=True)
def flag(iso):
    if not iso or len(iso) != 2 or not iso.isalpha(): return ''
    return ''.join(chr(0x1F1E6 + ord(c.upper()) - 65) for c in iso)

# ---- per-material apparent vs embodied concentration ----
mat_rows = []
for m in data['materials']:
    label = m['label']
    o, tot = {}, 0.0
    for f in flows.get('materials', {}).get(label) or []:
        o[f['from']] = o.get(f['from'], 0.0) + f['value']; tot += f['value']
    if not tot:
        continue
    app_hhi = sum((v / tot) ** 2 for v in o.values())
    top_app = max(o, key=o.get)
    mined = MINE[label]
    msum = sum(x['v'] for x in mined) or 1
    emb_hhi = sum((x['v'] / msum) ** 2 for x in mined) if mined else 0.0
    top_emb = mined[0]['c'] if mined else None
    mat_rows.append({'label': label, 'title': TITLES[label],
                     'top_apparent': top_app, 'app_hhi': round(app_hhi, 3),
                     'top_origin': top_emb, 'emb_hhi': round(emb_hhi, 3),
                     'disguised': bool(emb_hhi > app_hhi + 0.02)})

# ---- importer-level trace ----
imp_total, imp_hidden, imp_supp, imp_orig, imp_mats = {}, {}, {}, {}, {}
for m in data['materials']:
    label = m['label']
    mined = MINE[label]
    msh = {x['c']: x['v'] for x in mined}
    top = mined[0]['c'] if mined else None
    for f in flows.get('materials', {}).get(label) or []:
        q, r, v = f['from'], f['to'], f['value']
        if v <= 0:
            continue
        imp_total[r] = imp_total.get(r, 0.0) + v
        imp_mats.setdefault(r, set()).add(label)
        imp_supp.setdefault(r, {}); imp_supp[r][q] = imp_supp[r].get(q, 0.0) + v
        if top is not None and msh.get(q, 0) < MINER_MIN:
            origin = top                      # refiner/hub -> re-attribute to the dominant mine
            if origin != q:
                imp_hidden[r] = imp_hidden.get(r, 0.0) + v
        else:
            origin = q                        # genuine producer (or unknown stage)
        imp_orig.setdefault(r, {}); imp_orig[r][origin] = imp_orig[r].get(origin, 0.0) + v

importers = []
for r, tot in imp_total.items():
    if r in HUBS or tot <= 0:
        continue
    supp = imp_supp[r]; orig = imp_orig[r]
    top_supp = max(supp, key=supp.get)
    top_org = max(orig, key=orig.get)
    importers.append({'c': r, 'name': cname(r), 'total': tot, 'n_mats': len(imp_mats[r]),
                      'top_supplier': top_supp, 'supplier_share': round(supp[top_supp] / tot * 100, 1),
                      'top_origin': top_org, 'origin_share': round(orig[top_org] / tot * 100, 1),
                      'hidden': round(imp_hidden.get(r, 0.0) / tot * 100, 1),
                      'shifts': top_supp != top_org})
# real consuming economies only: >= $1B imports across >= 8 materials (drops single-material micro-importers)
importers = [i for i in importers if i['total'] >= 1e9 and i['n_mats'] >= 8]
importers.sort(key=lambda x: x['total'], reverse=True)   # major economies first
TOPI = importers[:25]
n_disguised = sum(1 for r in mat_rows if r['disguised'])

json.dump({'year': YEAR, 'rule': 'refiner/hub imports re-attributed to dominant mine (first-order trace)',
           'materials': mat_rows, 'importers': importers, 'n_disguised': n_disguised},
          open(os.path.join(ROOT, 'out', 'origin_trace.json'), 'w', encoding='utf8'), indent=1)

# ---- page ----
motif = ('<svg class="hero-motif" viewBox="0 0 560 560" fill="none" aria-hidden="true"><g stroke="#7fd2c8" stroke-opacity=".15" stroke-width="1.1"><circle cx="280" cy="280" r="232"/><ellipse cx="280" cy="280" rx="232" ry="62"/><ellipse cx="280" cy="280" rx="232" ry="132"/><ellipse cx="280" cy="280" rx="232" ry="196"/><ellipse cx="280" cy="280" rx="62" ry="232"/><ellipse cx="280" cy="280" rx="132" ry="232"/><ellipse cx="280" cy="280" rx="196" ry="232"/><line x1="280" y1="48" x2="280" y2="512"/><line x1="48" y1="280" x2="512" y2="280"/></g><g stroke="#9be3da" stroke-opacity=".26" stroke-width="1.4" fill="none"><path d="M120 360 Q 300 110 472 248"/><path d="M158 196 Q 322 300 442 422"/><path d="M120 360 Q 268 430 442 422"/></g><g fill="#bff0e8" fill-opacity=".55"><circle cx="120" cy="360" r="4.2"/><circle cx="472" cy="248" r="4.2"/><circle cx="158" cy="196" r="4.2"/><circle cx="442" cy="422" r="4.2"/></g></svg>')

irows = []
for i, r in enumerate(TOPI, 1):
    hcol = '#c0392b' if r['hidden'] >= 50 else '#b35e16' if r['hidden'] >= 25 else '#3f9b46'
    arrow = ' →' if r['shifts'] else ''
    irows.append(
        f'<tr><td class="n" style="color:#9aa6ad">{i}</td>'
        f'<td>{flag(r["c"])} {e(r["name"])}</td>'
        f'<td>{flag(r["top_supplier"])} {e(cname(r["top_supplier"]))} <span style="color:#9aa6ad">{r["supplier_share"]:.0f}%</span></td>'
        f'<td>{flag(r["top_origin"])} {e(cname(r["top_origin"]))} <span style="color:#9aa6ad">{r["origin_share"]:.0f}%</span>{arrow}</td>'
        f'<td class="n" style="font-weight:700;color:{hcol}">{r["hidden"]:.0f}%</td></tr>')

drows = []
for r in sorted(mat_rows, key=lambda x: x['emb_hhi'] - x['app_hhi'], reverse=True):
    if not r['disguised']:
        continue
    drows.append(
        f'<tr><td><a href="profile-{e(r["label"])}.html">{e(r["title"])}</a></td>'
        f'<td>{flag(r["top_apparent"])} {e(cname(r["top_apparent"]))} <span style="color:#9aa6ad">HHI {r["app_hhi"]:.2f}</span></td>'
        f'<td>{flag(r["top_origin"])} {e(cname(r["top_origin"]))} <span style="color:#9aa6ad">HHI {r["emb_hhi"]:.2f}</span></td>'
        f'<td class="n" style="color:#c0392b">+{(r["emb_hhi"]-r["app_hhi"]):.2f}</td></tr>')

out = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Origin trace — Critical Materials Atlas</title>
<meta name="description" content="Tracing the refiner layer: re-attributing each country's critical-material imports from the apparent supplier to the likely true mine origin, and how much of supply is hidden behind refiners.">
<meta property="og:title" content="Origin trace — what's hidden behind the refiner">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="explorer">Explore</a><a href="value-chains">Value Chains</a><a href="analysis">Analysis</a><a href="reports">Reports</a><a href="method">Method</a></nav>
</div></header>
<section class="hero">{motif}<div class="wrap">
  <div class="eyebrow">Method · origin tracing</div>
  <h1>What's hidden behind the refiner</h1>
  <p class="deck">The origin gap, traced — as a first-order estimate. Each country's imports are re-attributed from the apparent supplier (often a refiner or hub) to a likely mine origin, showing how much of a nation's critical-material supply is sourced <i>via a refiner</i> rather than the producer its customs data names.</p>
</div></section>
<article style="max-width:1000px">
  <div class="callout">Each country&rsquo;s imports are re-attributed from the refiner or hub that shipped them back to the mine that likely produced the ore &mdash; showing how much of its supply really comes via a middleman.
  <details class="howto"><summary>The rule, and why it&rsquo;s an upper bound</summary>
  <p>For every import flow: if the supplier genuinely mines the material (world mine share &ge; {MINER_MIN:.0f}%) the origin stays the supplier; otherwise the supplier is treated as a refiner or hub, and the value is re-attributed to the material&rsquo;s <b>dominant mine</b>. A country&rsquo;s <b>hidden dependence</b> is the share of its imports re-attributed away from the apparent supplier.</p>
  <p class="howto-src"><b>First-order trace — an upper bound.</b> We don&rsquo;t observe each refiner&rsquo;s ore sourcing, so all refiner-fronted flow is assigned to the single leading producer; real refiners blend ores, scrap and contracts. Read it as the <i>scale</i> of the refiner illusion, not a customs-grade origin. Computed by <code>build_origin.py</code>.</p>
  </details></div>

  <h2 style="margin:1.6rem 0 .5rem">Hidden dependence by importer</h2>
  <p class="note" style="margin-top:0">Apparent #1 supplier vs the likely #1 origin (upper-bound attribution), and the share of imports that are <i>refiner-fronted</i> (sourced via a non-producer). Re-export hubs excluded; ranked by import value.</p>
  <table>
    <thead><tr><th class="n">#</th><th>Importer</th><th>Apparent #1 supplier</th><th>Likely #1 origin</th><th class="n" title="share of imports sourced via a refiner/non-producer rather than a genuine mine">refiner-fronted</th></tr></thead>
    <tbody>{''.join(irows)}</tbody>
  </table>

  <h2 style="margin:2rem 0 .5rem">Where the mine stage is more concentrated than the trade stage</h2>
  <p class="note" style="margin-top:0">{n_disguised} of {len(mat_rows)} materials are <i>more</i> concentrated at the mine (production) than in trade — apparent-supplier diversity can overstate how diversified the underlying production is. Trade and mine concentration are different objects (multi-stage chains naturally disperse trade), so read this as a flag, not proof of disguise.</p>
  <table>
    <thead><tr><th>Material</th><th>Apparent #1 supplier (trade HHI)</th><th>Traced #1 origin (mine HHI)</th><th class="n" title="how much more concentrated the true origin is">HHI gap</th></tr></thead>
    <tbody>{''.join(drows)}</tbody>
  </table>
  <p class="note">Computed from <a href="out/flows_{YEAR}.json">flows_{YEAR}.json</a> + <a href="out/data.json">data.json</a> → <a href="out/origin_trace.json">origin_trace.json</a>.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="explorer">Explore</a><br><a href="value-chains">Value Chains</a><br><a href="analysis">Analysis</a><br><a href="reports">Reports</a><br><a href="method">Method</a></div>
  <div><h4>Sources</h4>UN Comtrade · CEPII BACI<br>USGS · IEA</div>
  <div class="fineprint">First-order trace; refiner ore-sourcing not observed. Method documented.</div>
</div></footer>
</body></html>'''
open(os.path.join(ROOT, 'origin.html'), 'w', encoding='utf8', newline='\n').write(out)

print(f'wrote origin.html + out/origin_trace.json — {n_disguised}/{len(mat_rows)} materials disguised, {len(importers)} importers')
print('\nHIGHEST HIDDEN DEPENDENCE (importers):')
for r in TOPI[:10]:
    print(f"  {r['name']:<22} apparent {r['top_supplier']} {r['supplier_share']:.0f}% -> traced {r['top_origin']} {r['origin_share']:.0f}%  hidden {r['hidden']:.0f}%")

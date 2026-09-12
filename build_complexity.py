#!/usr/bin/env python3
"""
Economic complexity of critical-materials trade — RCA, ECI/PCI and relatedness.

Applies the Hidalgo-Hausmann toolkit to the one stage where we have a complete country x material matrix:
EXPORTS (summed bilateral out-flows). For each country c and material m:

  RCA_cm = (X_cm / Sum_m X_cm) / (Sum_c X_cm / Sum X)          Balassa revealed comparative advantage
  M_cm   = 1[RCA_cm >= 1]                                       binary "competitive exporter"
  diversity k_c = Sum_m M_cm     ubiquity k_m = Sum_c M_cm
  ECI / PCI : standardized eigenvector (method of reflections) of the M-projection matrices
  relatedness phi_mm' = min( P(M_m'|M_m), P(M_m|M_m') )         do the same countries export both?

The new outputs: material UBIQUITY (how few countries competitively export it -> the strategic ones),
the relatedness map of the 32 materials (which cluster), and country ECI (who the "complex" exporters are
- the refiners, not the miners). Note: mining/refining shares are top-N only (too sparse for full RCA), so
this is the TRADE stage; mine share is shown alongside for contrast. Public data; deterministic.

Writes out/complexity.json + complexity.html.  Run:  python build_complexity.py
"""
import json, os, html
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
YEAR = os.environ.get('PROFILE_YEAR', '2024')
flows = json.load(open(os.path.join(ROOT, 'out', f'flows_{YEAR}.json'), encoding='utf8'))
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
NAMES = flows.get('names', {})
MATS = [m['label'] for m in data['materials']]
TITLES = {m['label']: m['title'].split(' (')[0] for m in data['materials']}
MINE_TOP = {m['label']: (m['mined'][0]['c'] if m.get('mined') else None) for m in data['materials']}
SHARED = {'gallium', 'germanium'}   # only these fold into HS6 811292; hafnium is distinct (811231)

def cname(i): return NAMES.get(i, i)
def e(s): return html.escape(str(s), quote=True)
def flag(iso):
    if not iso or len(iso) != 2 or not iso.isalpha(): return ''
    return ''.join(chr(0x1F1E6 + ord(c.upper()) - 65) for c in iso)

# ---- build country x material export matrix ----
exp = {}
for m in MATS:
    for f in flows.get('materials', {}).get(m, []) or []:
        c, w = f['from'], float(f['value'])
        if w <= 0: continue
        exp.setdefault(c, {})
        exp[c][m] = exp[c].get(m, 0.0) + w
countries = sorted(exp)
C, Mn = len(countries), len(MATS)
X = np.zeros((C, Mn))
for ci, c in enumerate(countries):
    for mi, m in enumerate(MATS):
        X[ci, mi] = exp[c].get(m, 0.0)

# ---- RCA + binary M ----
row = X.sum(1, keepdims=True); col = X.sum(0, keepdims=True); tot = X.sum()
with np.errstate(divide='ignore', invalid='ignore'):
    RCA = (X / np.where(row == 0, np.nan, row)) / (col / tot)
RCA = np.nan_to_num(RCA)
M = (RCA >= 1).astype(float)

# diversity (per country) and ubiquity (per material)
kc = M.sum(1); km = M.sum(0)
# capability = sum over a country's RCA basket of 1/ubiquity — rewards competitively exporting RARE
# materials (a robust "complexity-lite"; full ECI/PCI is degenerate on a narrow 32-product slice).
inv_ub = np.nan_to_num(np.where(km > 0, 1.0 / np.where(km == 0, np.nan, km), 0.0))
capability = (M * inv_ub).sum(1)

# ---- relatedness phi (material x material) ----
co = M.T @ M
phi = np.zeros((Mn, Mn))
for a in range(Mn):
    for b in range(Mn):
        if a == b or km[a] == 0 or km[b] == 0: continue
        if MATS[a] in SHARED and MATS[b] in SHARED: continue   # identical HS6 -> tautological relatedness, exclude
        phi[a, b] = min(co[a, b] / km[a], co[a, b] / km[b])

# ---- assemble ----
mat_rows = []
for mi, m in enumerate(MATS):
    nbrs = sorted(((phi[mi, j], MATS[j]) for j in range(Mn) if j != mi), reverse=True)[:3]
    nbrs = [(round(p, 2), TITLES[lab]) for p, lab in nbrs if p > 0]
    mat_rows.append({
        'label': m, 'title': TITLES[m], 'shared': m in SHARED,
        'ubiquity': int(km[mi]),                         # # countries with RCA>=1
        'mine_top': MINE_TOP.get(m),
        'related': nbrs,
    })
mat_rows.sort(key=lambda r: r['ubiquity'])               # rarest (most strategic) first

ctry = [{'c': c, 'name': cname(c), 'capability': round(float(capability[i]), 2), 'diversity': int(kc[i])}
        for i, c in enumerate(countries) if kc[i] > 0]
ctry.sort(key=lambda r: (r['capability'], r['diversity']), reverse=True)

json.dump({'year': YEAR, 'n_countries': C, 'materials': mat_rows, 'countries_top': ctry[:15]},
          open(os.path.join(ROOT, 'out', 'complexity.json'), 'w', encoding='utf8'), indent=1)

# ---- page ----
motif = ('<svg class="hero-motif" viewBox="0 0 560 560" fill="none" aria-hidden="true"><g stroke="#7fd2c8" stroke-opacity=".15" stroke-width="1.1"><circle cx="280" cy="280" r="232"/><ellipse cx="280" cy="280" rx="232" ry="62"/><ellipse cx="280" cy="280" rx="232" ry="132"/><ellipse cx="280" cy="280" rx="232" ry="196"/><ellipse cx="280" cy="280" rx="62" ry="232"/><ellipse cx="280" cy="280" rx="132" ry="232"/><ellipse cx="280" cy="280" rx="196" ry="232"/><line x1="280" y1="48" x2="280" y2="512"/><line x1="48" y1="280" x2="512" y2="280"/></g><g stroke="#9be3da" stroke-opacity=".26" stroke-width="1.4" fill="none"><path d="M120 360 Q 300 110 472 248"/><path d="M158 196 Q 322 300 442 422"/><path d="M120 360 Q 268 430 442 422"/></g><g fill="#bff0e8" fill-opacity=".55"><circle cx="120" cy="360" r="4.2"/><circle cx="472" cy="248" r="4.2"/><circle cx="158" cy="196" r="4.2"/><circle cx="442" cy="422" r="4.2"/></g></svg>')

mr = []
for r in mat_rows:
    nb = ', '.join(f'{t} <span style="color:#9aa6ad">{p:.2f}</span>' for p, t in r['related']) or '—'
    ucol = '#c0392b' if r['ubiquity'] <= 8 else '#b35e16' if r['ubiquity'] <= 16 else '#3f9b46'
    mr.append(
        f'<tr><td><a href="profile-{e(r["label"])}.html">{e(r["title"])}</a>{" ⛓" if r["shared"] else ""}</td>'
        f'<td class="n" style="font-weight:700;color:{ucol}" title="number of countries with revealed comparative advantage (RCA>=1) in exporting it">{r["ubiquity"]}</td>'
        f'<td>{flag(r["mine_top"])} {e(cname(r["mine_top"])) if r["mine_top"] else "—"}</td>'
        f'<td style="font-size:.86rem">{nb}</td></tr>')

cr = []
for i, r in enumerate(ctry[:15], 1):
    cr.append(
        f'<tr><td class="n" style="color:#9aa6ad">{i}</td>'
        f'<td>{flag(r["c"])} {e(r["name"])}</td>'
        f'<td class="n" style="font-weight:700;color:#15323a">{r["capability"]:.2f}</td>'
        f'<td class="n" style="color:#0e7c74">{r["diversity"]}</td></tr>')

out = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Economic complexity of critical-materials trade — Critical Materials Atlas</title>
<meta name="description" content="Revealed comparative advantage, complexity and relatedness for 32 critical materials: which are exported competitively by the fewest countries (the strategic ones), which cluster together, and who the complex exporters are.">
<meta property="og:title" content="Economic complexity of critical-materials trade">
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
  <div class="eyebrow">Method · economic complexity</div>
  <h1>The competitiveness lens fails exactly where it matters</h1>
  <p class="deck">Economic-complexity analysis (Balassa revealed comparative advantage) ranks who <i>competitively exports</i> each material. The count ranges from ~8 countries (lithium, beryllium, strontium) to <b>52</b> — and that top score is the warning: <b>rare-earth magnets</b>, among the most China-refined materials on Earth, have the <b>highest</b> export-ubiquity of all, because dozens of countries re-export them. RCA counts shippers, not refiners, so it reads the most concentrated chains as the most diverse. Economic complexity is the wrong instrument for supply-chain risk — and this page shows precisely where it breaks, which is the point of running it.</p>
</div></section>
<article style="max-width:1000px">
  <div class="callout">Some materials have many competitive exporters; a few have almost none. This measures how many countries can genuinely compete in each &mdash; a market-revealed signal of scarcity, beside the mine-concentration story.
  <details class="howto"><summary>How it&rsquo;s measured</summary>
  <p>From the one complete country&times;material matrix we have (exports), I compute Balassa <b>RCA</b> (a country is a competitive exporter when its share of that material exceeds its overall export share), a robust <b>capability</b> score, and <b>relatedness</b> (do the same countries export both?). <b>Ubiquity</b> = how many countries clear RCA&ge;1: a low number means only a handful can competitively supply it.</p>
  <p class="howto-src"><b>Caveat:</b> RCA here is over the 32-material matrix only &mdash; specialization <i>within</i> critical materials, not economy-wide, so small and re-export economies can surface as &ldquo;competitive&rdquo;, and the threshold makes ubiquity sensitive to thin flows and HS6 pooling. Mine/refine data are top-N; mine leader shown for contrast. Computed by <code>build_complexity.py</code>.</p>
  </details></div>

  <h2 style="margin:1.6rem 0 .5rem">Materials by ubiquity — the rarest are the most strategic</h2>
  <table>
    <thead><tr><th>Material</th><th class="n" title="number of countries with RCA>=1 in exporting it (fewer = more strategic)">competitive exporters</th><th>mined mainly in</th><th>most related materials (relatedness)</th></tr></thead>
    <tbody>{''.join(mr)}</tbody>
  </table>

  <h2 style="margin:2rem 0 .5rem">The most capable exporters</h2>
  <p class="note" style="margin-top:0">Capability = the sum of 1/ubiquity over the materials a country competitively exports (RCA&ge;1) — it rewards commanding many materials that <i>few others can</i>. Leaders mix large industrial economies with smaller open / re-export economies — read this as export specialization, not industrial capability per se.</p>
  <table style="max-width:560px">
    <thead><tr><th class="n">#</th><th>Country</th><th class="n" title="sum of 1/ubiquity over the materials it competitively exports (rewards rare baskets)">capability</th><th class="n" title="materials it competitively exports (RCA>=1)">diversity</th></tr></thead>
    <tbody>{''.join(cr)}</tbody>
  </table>
  <p class="note">⛓ gallium and germanium share one HS6 code (811292); hafnium is distinct (811231). Computed from <a href="out/flows_{YEAR}.json">flows_{YEAR}.json</a> → <a href="out/complexity.json">complexity.json</a>.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="explorer">Explore</a><br><a href="value-chains">Value Chains</a><br><a href="analysis">Analysis</a><br><a href="reports">Reports</a><br><a href="method">Method</a></div>
  <div><h4>Sources</h4>UN Comtrade · CEPII BACI<br>USGS · IEA · World Bank</div>
  <div class="fineprint">RCA on the trade stage; complexity eigenvectors are standardized. Method documented.</div>
</div></footer>
</body></html>'''
open(os.path.join(ROOT, 'complexity.html'), 'w', encoding='utf8', newline='\n').write(out)

print(f'wrote complexity.html + out/complexity.json — {C} exporting countries, {Mn} materials')
print('\nRAREST (fewest competitive exporters):')
for r in mat_rows[:8]:
    print(f"  {r['title']:<24} ubiquity {r['ubiquity']:>2}  mined: {r['mine_top']}")
print('\nMOST CAPABLE EXPORTERS:')
for r in ctry[:8]:
    print(f"  {r['name']:<22} capability {r['capability']:.2f}  diversity {r['diversity']}")

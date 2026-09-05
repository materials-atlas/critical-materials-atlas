#!/usr/bin/env python3
"""
A TRANSPARENT supply-risk index per material. Not a black-box "criticality" verdict — an explicit weighted
blend of four named, visible components, each 0-100, computed from the public data. The components are
always shown next to the score so a reader can audit (or reweight) it.

  production  (30%)  top miner's share of world output            — USGS
  refining    (25%)  top refiner's share (else export HHI proxy)  — IEA / trade
  trade       (25%)  export Herfindahl (chokepoint in the flow)   — reconciled trade
  opacity     (20%)  origin gap = exporter share - its mine share — how misleading the trade ledger is

Writes out/risk.json (consumed by the atlas + profiles) and risk.html (the league table).
"""
import json, os, html

ROOT = os.path.dirname(os.path.abspath(__file__))
YEAR = os.environ.get('PROFILE_YEAR', '2024')
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
flows = json.load(open(os.path.join(ROOT, 'out', f'flows_{YEAR}.json'), encoding='utf8'))
NAMES = flows.get('names', {})
SHARED = {'gallium', 'germanium'}
W = {'production': 0.30, 'refining': 0.25, 'trade': 0.25, 'opacity': 0.20}

def cname(i): return NAMES.get(i, i)
def e(s): return html.escape(str(s), quote=True)
def flag(iso):
    if not iso or len(iso) != 2 or not iso.isalpha(): return ''
    return ''.join(chr(0x1F1E6 + ord(c.upper()) - 65) for c in iso)

def exporters(label):
    a = (flows.get('materials', {}).get(label)) or []
    o, tot = {}, 0.0
    for f in a:
        o[f['from']] = o.get(f['from'], 0.0) + f['value']; tot += f['value']
    return o, tot

def components(m):
    label = m['label']
    o, tot = exporters(label)
    mined = m.get('mined') or []
    refined = m.get('refined') or []
    prod = mined[0]['v'] if mined else 0.0
    ehhi = (sum((v / tot) ** 2 for v in o.values()) * 100) if tot else 0.0
    ref = (refined[0]['v'] if refined else ehhi)
    # origin gap
    gap = 0.0
    if tot:
        te = max(o, key=o.get); te_sh = o[te] / tot * 100
        te_mine = next((x['v'] for x in mined if x['c'] == te), 0.0)
        gap = max(0.0, te_sh - te_mine)
    opacity = min(gap, 60.0) / 60.0 * 100
    c = {'production': round(prod, 1), 'refining': round(ref, 1),
         'trade': round(ehhi, 1), 'opacity': round(opacity, 1)}
    gross = sum(W[k] * c[k] for k in W)
    recyc = m.get('recycling') or 0
    net = gross * (1 - 0.4 * recyc / 100)   # recyclability discount: up to 40% off at 100% EOL recycling
    return c, round(gross), round(net), recyc

COLORS = {'production': '#c77f0a', 'refining': '#6d5fb0', 'trade': '#0e7c74', 'opacity': '#b4532b'}

def main():
    rows = []
    for m in data['materials']:
        c, gross, score, recyc = components(m)
        rows.append({'label': m['label'], 'title': m['title'].split(' (')[0],
                     'score': score, 'gross': gross, 'recycling': recyc,
                     'substitutability': m.get('substitutability'),
                     'components': c, 'shared': m['label'] in SHARED})
    # ── uncertainty on materials whose refining share is an interval, not a measurement ──────
    # A scalar index needs one number, but germanium's refining share has no measured world value:
    # only two dated anchors (68% USGS world 2020, 94% BGS three-reporter 2024). Publishing the
    # point alone would launder that interval into a fact. So the score is recomputed at each
    # anchor and the resulting score AND RANK BAND travel with the row.
    def score_with(m, ref_override):
        mm = dict(m); mm['refined'] = [{'c': (m.get('refined') or [{}])[0].get('c'),
                                        'v': ref_override}]
        return components(mm)[2]
    for m in data['materials']:
        rng = m.get('refined_range')
        if not rng:
            continue
        row = next((r for r in rows if r['label'] == m['label']), None)
        if not row:
            continue
        lo_s, hi_s = score_with(m, rng[0]), score_with(m, rng[1])
        ranks = []
        for s_alt in (lo_s, hi_s):
            others = sorted([r['score'] for r in rows if r['label'] != m['label']] + [s_alt],
                            reverse=True)
            ranks.append(others.index(s_alt) + 1)
        row['score_range'] = sorted([lo_s, hi_s])
        row['rank_range'] = sorted(ranks)
        row['uncertainty'] = (
            f"refining share is an interval ({rng[0]}-{rng[1]}%), not a measurement; the point "
            f"score uses the midpoint of the dated anchors. Score spans {min(lo_s, hi_s)}-"
            f"{max(lo_s, hi_s)}, rank spans {min(ranks)}-{max(ranks)} of {len(rows)}.")
        row['refined_source'] = m.get('refined_source')

    rows.sort(key=lambda r: r['score'], reverse=True)
    json.dump({'weights': W, 'year': YEAR, 'materials': rows},
              open(os.path.join(ROOT, 'out', 'risk.json'), 'w', encoding='utf8'), indent=1)

    # league-table page
    body = []
    for i, r in enumerate(rows, 1):
        segs = ''.join(
            f'<span title="{e(k)} {r["components"][k]:.0f}/100 (weight {int(W[k]*100)}%)" '
            f'style="display:inline-block;height:14px;width:{W[k]*r["components"][k]*0.9:.1f}%;background:{COLORS[k]}"></span>'
            for k in ['production', 'refining', 'trade', 'opacity'])
        sc = r['score']; scol = '#c0392b' if sc >= 60 else '#b35e16' if sc >= 40 else '#3f9b46'
        sr = r.get('score_range')
        sc_disp = f'{sr[0]}–{sr[1]}' if sr else f'{sc}'
        rec = r['recycling']
        rcell = (f'<td class="n" style="color:#3f9b46" title="end-of-life recycling input rate (EU CRM 2023); '
                 f'discounts the gross score of {r["gross"]}">{rec}%</td>') if rec else '<td class="n" style="color:#c9d2d0">—</td>'
        sub = r.get('substitutability') or '—'
        subcol = {'high': '#c0392b', 'medium': '#b35e16', 'low': '#3f9b46'}.get(sub, '#c9d2d0')
        scell = f'<td style="color:{subcol};font-weight:600;font-size:.8rem;text-transform:uppercase">{e(sub)}</td>'
        # A material whose refining share is an interval does not have an identified rank. Both
        # council engines named publishing the point as the top credibility risk: the midpoint of
        # two anchors measured in different years on different bases is not a statistic, so the
        # rank it produces must not be printed as if it were one.
        rk = r.get('rank_range')
        rank_cell = (f'<td class="n" style="color:#b35e16" title="{e(r.get("uncertainty",""))}">'
                     f'{rk[0]}–{rk[1]}<span style="color:#9aa6ad;font-size:.75rem"> ?</span></td>'
                     if rk else f'<td class="n" style="color:#9aa6ad">{i}</td>')
        body.append(
            f'<tr>{rank_cell}'
            f'<td><a href="profile-{e(r["label"])}.html">{e(r["title"])}</a>{" ⛓" if r["shared"] else ""}</td>'
            f'<td class="n" style="font-weight:800;color:{scol};font-size:1.05rem">{sc_disp}</td>'
            f'{rcell}{scell}'
            f'<td style="width:34%"><span style="display:flex;background:#eef2f1;border-radius:3px;overflow:hidden">{segs}</span></td></tr>')
    legend = ' &nbsp; '.join(f'<span style="color:{COLORS[k]}">■</span> {k} <span style="color:#9aa6ad">({int(W[k]*100)}%)</span>'
                             for k in ['production', 'refining', 'trade', 'opacity'])
    motif = ('<svg class="hero-motif" viewBox="0 0 560 560" fill="none" aria-hidden="true"><g stroke="#7fd2c8" stroke-opacity=".15" stroke-width="1.1"><circle cx="280" cy="280" r="232"/><ellipse cx="280" cy="280" rx="232" ry="62"/><ellipse cx="280" cy="280" rx="232" ry="132"/><ellipse cx="280" cy="280" rx="232" ry="196"/><ellipse cx="280" cy="280" rx="62" ry="232"/><ellipse cx="280" cy="280" rx="132" ry="232"/><ellipse cx="280" cy="280" rx="196" ry="232"/><line x1="280" y1="48" x2="280" y2="512"/><line x1="48" y1="280" x2="512" y2="280"/></g><g stroke="#9be3da" stroke-opacity=".26" stroke-width="1.4" fill="none"><path d="M120 360 Q 300 110 472 248"/><path d="M158 196 Q 322 300 442 422"/><path d="M120 360 Q 268 430 442 422"/></g><g fill="#bff0e8" fill-opacity=".55"><circle cx="120" cy="360" r="4.2"/><circle cx="472" cy="248" r="4.2"/><circle cx="158" cy="196" r="4.2"/><circle cx="442" cy="422" r="4.2"/></g></svg>')
    out = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Supply-risk index — Critical Materials Atlas</title>
<meta name="description" content="A transparent 0-100 supply-risk score for 32 critical materials, built from visible components: production, refining and trade concentration, and origin opacity.">
<meta property="og:title" content="Critical-material supply-risk index">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="methodology.html">Methodology</a><a href="findings.html">Findings</a>
  <a href="profiles.html" class="hideable">Profiles</a><a href="scenarios.html" class="hideable">Scenarios</a>
  <a href="https://github.com/materials-atlas/critical-materials-atlas" class="hideable">Engine</a></nav>
</div></header>
<section class="hero">{motif}<div class="wrap">
  <div class="eyebrow">Index · supply risk</div>
  <h1>Supply-risk index</h1>
  <p class="deck">One 0–100 score per material — but never a black box. It is an explicit weighted blend of four visible components, shown as a bar on every row. Reweight them yourself; the raw numbers are in the open data.</p>
</div></section>
<article style="max-width:960px">
  <div class="callout">One 0&ndash;100 score per material, built from four visible components &mdash; never a black box.
  <details class="howto"><summary>How the score is built</summary>
  <p>{legend}. Each component is 0–100, from public data (production &amp; refining: USGS/IEA shares; trade: reconciled-trade export Herfindahl; opacity: the origin gap). Their weighted sum is the <i>gross</i> score, then <b>discounted for recyclability</b> — gross risk is cut by 0.4 &times; the end-of-life recycling rate (EU CRM 2023), so a highly recycled material (tungsten 42%, aluminium 32%, antimony 28%, cobalt 22%) scores lower than its raw concentration implies. <b>Substitutability</b> is shown alongside but <i>not</i> folded into the score &mdash; a high-risk material that is also hard to substitute is the more strategic.</p>
  <p class="howto-src">A transparent heuristic, <i>not</i> an official criticality assessment; it ignores price and stockpiles.</p>
  </details></div>
  <table>
    <thead><tr><th class="n">#</th><th>Material</th><th class="n">score</th><th class="n" title="end-of-life recycling input rate — a mitigant">recyc</th><th title="how hard to substitute (EU CRM) — shown, not scored">subst.</th><th>gross components (width = weighted contribution)</th></tr></thead>
    <tbody>{''.join(body)}</tbody>
  </table>
  <p class="note">⛓ gallium and germanium share one HS6 code (811292; identical trade; hafnium is separate). Computed by build_risk.py from <a href="out/data.json">data.json</a> + <a href="out/flows_{YEAR}.json">flows_{YEAR}.json</a> → <a href="out/risk.json">risk.json</a>.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="./">Interactive atlas</a><br><a href="findings.html">The origin gap</a><br><a href="scenarios.html">Supply-shock scenarios</a><br><a href="countries.html">Dependency by country</a></div>
  <div><h4>Sources</h4>UN Comtrade · CEPII BACI<br>USGS · IEA · World Bank</div>
  <div class="fineprint">A transparent heuristic, components visible. Not an official criticality score.</div>
</div></footer>
</body></html>'''
    open(os.path.join(ROOT, 'risk.html'), 'w', encoding='utf8', newline='\n').write(out)
    print(f'wrote risk.html + out/risk.json  (top: {rows[0]["title"]} {rows[0]["score"]}, '
          f'{rows[1]["title"]} {rows[1]["score"]}, {rows[2]["title"]} {rows[2]["score"]})')

if __name__ == '__main__':
    main()

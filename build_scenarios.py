#!/usr/bin/env python3
"""
Supply-shock scenarios, computed from the reconciled trade. For a set of canonical disruptions (a key
exporter stops / is cut off), recompute each material's export concentration and rank the materials whose
traded supply is most exposed. First-order reallocation only — it asks "who else exports this today?",
NOT an equilibrium price/substitution model. Deterministic; writes scenarios.html.
"""
import json, os, html

ROOT = os.path.dirname(os.path.abspath(__file__))
YEAR = os.environ.get('PROFILE_YEAR', '2024')
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
flows = json.load(open(os.path.join(ROOT, 'out', f'flows_{YEAR}.json'), encoding='utf8'))
NAMES = flows.get('names', {})
TITLE = {m['label']: m['title'].split(' (')[0] for m in data['materials']}

SCEN = [('CN', 'China'), ('RU', 'Russia'), ('ID', 'Indonesia'), ('CD', 'DR Congo'), ('ZA', 'South Africa')]

def cname(i): return NAMES.get(i, i)
def e(s): return html.escape(str(s), quote=True)
def flag(iso):
    if not iso or len(iso) != 2 or not iso.isalpha(): return ''
    return ''.join(chr(0x1F1E6 + ord(c.upper()) - 65) for c in iso)

def exporter_shares(label):
    a = (flows.get('materials', {}).get(label)) or []
    o, tot = {}, 0.0
    for f in a:
        o[f['from']] = o.get(f['from'], 0.0) + f['value']; tot += f['value']
    return ({k: v / tot for k, v in o.items()}, tot) if tot else ({}, 0)

def hhi(sh): return sum(v * v for v in sh.values())

def scenario_rows(iso):
    rows = []
    for label, title in TITLE.items():
        sh, tot = exporter_shares(label)
        if not tot or iso not in sh:
            continue
        at_risk = sh[iso] * 100
        if at_risk < 5:
            continue
        before = hhi(sh)
        rest = {k: v for k, v in sh.items() if k != iso}
        s = sum(rest.values())
        renorm = {k: v / s for k, v in rest.items()} if s else {}
        after = hhi(renorm)
        newtop = max(renorm, key=renorm.get) if renorm else None
        rows.append({'label': label, 'title': title, 'at_risk': at_risk,
                     'before': before, 'after': after,
                     'newtop': newtop, 'newtop_sh': (renorm[newtop] * 100) if newtop else 0,
                     'stranded': s < 1e-9})
    rows.sort(key=lambda r: r['at_risk'], reverse=True)
    return rows

MOTIF = ('<svg class="hero-motif" viewBox="0 0 560 560" fill="none" aria-hidden="true"><g stroke="#7fd2c8" stroke-opacity=".15" stroke-width="1.1"><circle cx="280" cy="280" r="232"/><ellipse cx="280" cy="280" rx="232" ry="62"/><ellipse cx="280" cy="280" rx="232" ry="132"/><ellipse cx="280" cy="280" rx="232" ry="196"/><ellipse cx="280" cy="280" rx="62" ry="232"/><ellipse cx="280" cy="280" rx="132" ry="232"/><ellipse cx="280" cy="280" rx="196" ry="232"/><line x1="280" y1="48" x2="280" y2="512"/><line x1="48" y1="280" x2="512" y2="280"/></g><g stroke="#9be3da" stroke-opacity=".26" stroke-width="1.4" fill="none"><path d="M120 360 Q 300 110 472 248"/><path d="M158 196 Q 322 300 442 422"/><path d="M120 360 Q 268 430 442 422"/></g><g fill="#bff0e8" fill-opacity=".55"><circle cx="120" cy="360" r="4.2"/><circle cx="472" cy="248" r="4.2"/><circle cx="158" cy="196" r="4.2"/><circle cx="442" cy="422" r="4.2"/></g></svg>')

def section(iso, name):
    rows = scenario_rows(iso)
    if not rows:
        return ''
    over30 = sum(1 for r in rows if r['at_risk'] > 30)
    worst = rows[0]
    body = []
    for r in rows[:14]:
        deltacol = '#c0392b' if r['after'] > r['before'] else '#3f9b46'
        nt = (flag(r['newtop']) + ' ' + cname(r['newtop']) + f' {r["newtop_sh"]:.0f}%') if r['newtop'] else '— none left'
        strand = ' <span title="no other exporter of size — supply stranded" style="color:#c0392b">⚠</span>' if r['stranded'] else ''
        atrisk = f'{r["at_risk"]:.0f}'
        b2, a2 = f'{r["before"]:.2f}', f'{r["after"]:.2f}'
        body.append(
            f'<tr><td><a href="profile-{e(r["label"])}.html">{e(r["title"])}</a></td>'
            f'<td class="n" style="font-weight:700;color:#b4532b">{atrisk}%</td>'
            f'<td>{e(nt)}{strand}</td>'
            f'<td class="n">{b2} <span style="color:{deltacol}">&rarr; {a2}</span></td></tr>')
    return (f'<h2 id="{e(iso)}">If {e(name)} stopped exporting</h2>'
            f'<p>{e(name)} supplies &gt;5% of world trade in <b>{len(rows)}</b> of the tracked materials; '
            f'in <b>{over30}</b> it supplies more than 30%. The most exposed is <b>{e(worst["title"])}</b> '
            f'(<b>{worst["at_risk"]:.0f}%</b> of traded supply would need re-sourcing).</p>'
            f'<table><thead><tr><th>Material</th><th class="n">supply at risk</th><th>next-largest exporter</th>'
            f'<th class="n">export HHI before → after</th></tr></thead><tbody>{"".join(body)}</tbody></table>')

def main():
    nav = ' &nbsp;·&nbsp; '.join(f'<a href="#{iso}">{e(name)}</a>' for iso, name in SCEN)
    secs = ''.join(section(iso, name) for iso, name in SCEN)
    out = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Supply-shock scenarios — Critical Materials Atlas</title>
<meta name="description" content="What if a key exporter stopped? First-order supply-shock scenarios across 32 critical materials, computed from reconciled trade.">
<meta property="og:title" content="Critical-material supply-shock scenarios">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="methodology.html">Methodology</a><a href="findings.html">Findings</a>
  <a href="profiles.html" class="hideable">Profiles</a><a href="countries.html" class="hideable">Countries</a>
  <a href="https://github.com/materials-atlas/critical-materials-atlas" class="hideable">Engine</a></nav>
</div></header>
<section class="hero">{MOTIF}<div class="wrap">
  <div class="eyebrow">Analysis · supply shocks</div>
  <h1>What if a key exporter stopped?</h1>
  <p class="deck">For each canonical disruption, the materials whose traded supply is most exposed — and where it would have to re-source. {nav}</p>
</div></section>
<article style="max-width:900px">
  <div class="callout hot"><b>Read this as a stress test, not a forecast.</b>
  <details class="howto"><summary>What the numbers mean</summary>
  <p>&ldquo;Supply at risk&rdquo; is the share of world trade the exporter currently supplies — the volume that would need re-sourcing if it stopped. The before→after HHI assumes the remaining exporters keep their current relative shares (first-order reallocation); it is <i>not</i> a price, substitution, or capacity model. <b>⚠</b> marks a material with no other exporter of size — where re-sourcing has nowhere obvious to go.</p>
  </details></div>
  {secs}
  <p class="note" style="margin-top:1.4rem">Computed from <a href="out/flows_{YEAR}.json">out/flows_{YEAR}.json</a> by build_scenarios.py.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="./">Interactive atlas</a><br><a href="findings.html">The origin gap</a><br><a href="countries.html">Dependency by country</a><br><a href="methodology.html">Methodology</a></div>
  <div><h4>Sources</h4>UN Comtrade · CEPII BACI<br>USGS · IEA · World Bank</div>
  <div class="fineprint">First-order reallocation from reconciled {YEAR} trade. A stress test, not an equilibrium model.</div>
</div></footer>
</body></html>'''
    open(os.path.join(ROOT, 'scenarios.html'), 'w', encoding='utf8', newline='\n').write(out)
    print('wrote scenarios.html')

if __name__ == '__main__':
    main()

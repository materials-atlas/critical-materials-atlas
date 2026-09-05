#!/usr/bin/env python3
"""comparison.html — what happens when you check our production numbers against a second compilation.

Built from out/pairing.json (build_pairing.py). Derived, so check.py guards it.

FRAMING RULES, from the council review and followed literally:
  * Do not call it corroboration or verification. BGS and USGS are independent COMPILATIONS but not
    independent MEASUREMENTS - both rest largely on the same national returns.
  * Lead with the disagreements and what they teach, NOT a traffic-light of strong vs weak numbers.
    A scoreboard invites "which materials are you bad at"; the reasons are the actual content.
  * State plainly what the page does not claim: accuracy, ground truth, that agreement means a
    figure is right, or that an unpaired material is worse.
  * The reporter-count limit outranks the ratio. A sum over a handful of countries cannot be a
    world census however well the ratio lands.

Run:  python build_comparison.py
"""
import os, sys, json, html

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
e = lambda s: html.escape(str(s), quote=True)

NAMES = {'rare_earths': 'rare earths', 'iron': 'iron ore'}
disp = lambda m: NAMES.get(m, m).replace('_', ' ')

d = json.load(open(os.path.join(ROOT, 'out', 'pairing.json'), encoding='utf-8'))
rows = d['rows']
S = d['summary']
n_thin = sum(1 for r in rows if not r['census_plausible'])
order = {'not_comparable': 0, 'agrees_within_25pct': 1, 'agrees_within_10pct': 2}
rows_sorted = sorted(rows, key=lambda r: (order[r['status']], -abs(r['ratio'] - 1)))

LABEL = {'not_comparable': 'not comparable', 'agrees_within_25pct': 'within 25%',
         'agrees_within_10pct': 'within 10%'}
COLOR = {'not_comparable': '#b4532b', 'agrees_within_25pct': '#b35e16',
         'agrees_within_10pct': '#0e7c5a'}

# the two that were mysteries this morning and are now explained - the page's real content
CASES = [
    ('Cement', 0.066, 'China and India are absent',
     'BGS cement has ~32 reporting countries, led by Turkey, Germany, Italy and Spain. China alone '
     'produces roughly 2.4 of the world’s ~4.2 billion tonnes, and it does not appear at all. '
     'The panel is a Europe-weighted subset, not a world census — so its sum must never be used '
     'as a world denominator. Nothing here is a data error; the series simply does not mean what a '
     'reader would assume it means.'),
    ('Cobalt', 0.597, 'one country, and the gap is growing',
     'The entire shortfall is the DRC row. Every other BGS reporter reconciles with USGS. BGS holds '
     'the DRC roughly flat at 86–109 kt while the USGS world total climbs to 294 kt, so the gap '
     'widens from 52 kt (2010) to 77 kt (2015) to 164 kt (2020) — which is the shape of '
     'artisanal and small-scale output that national statistical returns do not capture. For cobalt '
     'world totals, USGS is the source to use.'),
]

trs = []
for r in rows_sorted:
    tops = ', '.join(t['iso'] for t in r['bgs_top_reporters'][:3])
    thin = '' if r['census_plausible'] else (
        ' <span title="fewer than 8 reporting countries: this sum cannot be a world census, '
        'whatever the ratio says" style="color:#b4532b;font-weight:700">†</span>')
    reason = e(r['reason']) if r['reason'] else '<span style="color:var(--faint)">—</span>'
    trs.append(
        f'<tr><td><b>{e(disp(r["material"]))}</b>{thin}</td>'
        f'<td class="src">{e(r["bgs_form"])}</td>'
        f'<td class="n">{r["ratio"]:.2f}</td>'
        f'<td class="n">{r["bgs_reporters_median"]}</td>'
        f'<td><span class="pill" style="color:{COLOR[r["status"]]};border-color:{COLOR[r["status"]]}33">'
        f'{LABEL[r["status"]]}</span></td>'
        f'<td class="why">{reason}</td></tr>')

cases_html = ''.join(
    f'<div class="case"><div class="ch"><b>{e(t)}</b><span class="ratio">ratio {r:.2f}</span>'
    f'<span class="verdict">{e(v)}</span></div><p>{e(body)}</p></div>'
    for t, r, v, body in CASES)

HTML = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="icon" type="image/png" sizes="192x192" href="/favicon-192.png"><link rel="icon" type="image/png" sizes="96x96" href="/favicon-96.png"><link rel="icon" type="image/png" sizes="48x48" href="/favicon-48.png"><link rel="icon" href="/favicon.ico" sizes="any"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="canonical" href="https://criticalmaterialsatlas.org/comparison">
<title>Two counts of the same world — Critical Materials Atlas</title>
<meta name="description" content="We checked every production figure in the atlas against a second public compilation. 34 of 53 track within 10%. The interesting part is the ones that do not — and why: BGS cement omits China entirely, and the whole cobalt gap is one under-reported country.">
<meta property="og:title" content="Two counts of the same world">
<meta property="og:description" content="Checking our production numbers against a second public compilation. What agrees, what does not, and what each disagreement actually means.">
<meta property="og:url" content="https://criticalmaterialsatlas.org/comparison">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<style>
 article{{max-width:1040px}}
 .lead{{font-size:1.05rem;line-height:1.6;color:var(--ink-soft);max-width:78ch;margin:.2rem 0 1.2rem}}
 .lead b{{color:var(--navy)}}
 .case{{border:1px solid var(--line);border-left:3px solid var(--hot);border-radius:10px;padding:.9rem 1.1rem;margin:.7rem 0;background:var(--bg-soft)}}
 .ch{{display:flex;align-items:baseline;gap:.7rem;flex-wrap:wrap;margin-bottom:.3rem}}
 .ch b{{font-size:1.05rem;color:var(--navy)}}
 .ch .ratio{{font-variant-numeric:tabular-nums;font-size:.8rem;color:var(--mut);font-weight:700}}
 .ch .verdict{{font-size:.85rem;color:var(--hot);font-weight:600}}
 .case p{{margin:0;font-size:.9rem;color:var(--ink-soft);line-height:1.55}}
 table{{font-size:.85rem}}
 td.src{{color:var(--mut);font-size:.8rem}}
 td.why{{color:var(--mut);font-size:.8rem;line-height:1.45;max-width:44ch}}
 .pill{{display:inline-block;border:1px solid;border-radius:99px;padding:.05rem .5rem;font-size:.72rem;font-weight:700;white-space:nowrap}}
 .notclaim{{border:1px solid var(--line);border-radius:10px;padding:1rem 1.2rem;margin:1.2rem 0;background:#fff}}
 .notclaim h3{{margin:0 0 .5rem;font-size:.95rem;color:var(--navy)}}
 .notclaim ul{{margin:0;padding-left:1.1rem}}
 .notclaim li{{font-size:.87rem;color:var(--ink-soft);margin:.25rem 0}}
</style>
</head><body>
<a class="skip" href="#main">Skip to content</a>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="explorer">Explore</a><a href="value-chains">Value Chains</a><a href="analysis">Analysis</a><a href="reports">Reports</a><a href="method">Method</a></nav>
</div></header>
<main id="main">

<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · cross-source comparison</div>
  <h1>Two counts of the same world</h1>
  <p class="deck">Every production figure the atlas publishes comes from a compilation of what countries report. So we ran the obvious check: does a <i>second</i> public compilation say the same thing? For <b>{S['agrees_within_10pct']} of {d['n_materials']}</b> materials the two track within 10%. The useful part is the ones that don&rsquo;t &mdash; because each disagreement turns out to name something specific about how the world&rsquo;s mineral statistics are actually made.</p>
</div></section>

<article>
  <p class="lead">We compare the sum of <b>BGS World Mineral Statistics</b> national returns against the <b>USGS</b> world-production estimate for the same material, over the years both cover. <b>These are independent compilations, but not independent measurements</b> &mdash; both rest largely on the same national statistical returns, so they can agree and still both be wrong. Agreement therefore tells you we have paired the right forms and read the units correctly. It is not evidence that a number is true, and a disagreement does not make either body wrong. Most disagreement here is definitional.</p>

  <h2>The disagreements are the content</h2>
  <p class="note" style="margin:.2rem 0 .4rem;max-width:80ch">Two were unexplained until this week. Neither turned out to be an error in anyone&rsquo;s data.</p>
  {cases_html}

  <div class="callout"><b>The limit that outranks the ratio.</b> A sum over a handful of reporting countries cannot be a world census, however neatly the ratio lands. <b>{n_thin} of {d['n_materials']}</b> materials here rest on fewer than eight reporting countries &mdash; including lithium and rare earths. Germanium is the clearest case: its two figures happen to sit close together, but BGS carries only three reporting countries for it, so that agreement is coincidence rather than confirmation. Those rows are marked <span style="color:#b4532b;font-weight:700">&dagger;</span> below, and the mark should be read before the number.</p></div>

  <h2>All {d['n_materials']} materials</h2>
  <p class="note" style="margin:.2rem 0 .6rem">Ordered by how far apart the two counts are &mdash; least comparable first, because those rows carry the information. Ratio = median (BGS national sum &divide; USGS world estimate) over the overlapping years.</p>
  <div style="overflow-x:auto">
  <table>
    <thead><tr><th>Material</th><th>BGS form paired</th><th class="n">Ratio</th><th class="n">Reporters</th><th>Status</th><th>What the difference is</th></tr></thead>
    <tbody>{''.join(trs)}</tbody>
  </table></div>

  <div class="notclaim">
    <h3>What this page does not claim</h3>
    <ul>
      <li>Not verification. Two compilations sharing the same national returns cannot verify each other.</li>
      <li>Not accuracy, and not ground truth. Neither body measures the ore; both collect what is reported.</li>
      <li>Agreement within 10% does not make a figure correct, and the band is wide.</li>
      <li>A material that does not pair is <i>not</i> thereby worse &mdash; usually the two are simply counting different objects, such as gross ore against contained metal.</li>
      <li>Where the two differ, this page does not declare the atlas&rsquo;s number the winner.</li>
    </ul>
  </div>

  <div class="callout"><b>Method.</b> Pairings are <b>declared explicitly</b> in <code>build_pairing.py</code>, never inferred by matching material names: a ratio between &ldquo;manganese ore, gross weight&rdquo; and &ldquo;manganese, contained metal&rdquo; is a category error, not a disagreement. Both series are read from the atlas&rsquo;s harmonised cube, which keeps every source&rsquo;s native codes and units alongside the common labels. Data: <a href="https://www2.bgs.ac.uk/mineralsuk/statistics/wms.cfc?method=searchWMS">BGS World Mineral Statistics</a> and USGS Historical Statistics &rarr; <a href="out/pairing.json">pairing.json</a>.</div>

  <div class="ftr"><a href="concentration">Concentration over time</a> &middot; <a href="production">The three-source production cross-check</a> &middot; <a href="analysis">All analysis</a></div>
</article>

</main>
<footer class="siteftr"><div class="wrap"><div><h4>Critical Materials Atlas</h4>Public-data value-chain research.</div><div><h4>Related</h4><a href="concentration">Concentration</a><br><a href="method">Method</a></div><div class="fineprint">BGS national-return sums vs USGS world estimates. Independent compilations, not independent measurements.</div></div></footer>
</body></html>
"""

open(os.path.join(ROOT, 'comparison.html'), 'w', encoding='utf-8').write(HTML)
print(f'wrote comparison.html — {d["n_materials"]} materials, {S["agrees_within_10pct"]} within 10%, '
      f'{n_thin} below the census threshold')

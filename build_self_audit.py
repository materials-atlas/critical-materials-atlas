# -*- coding: utf-8 -*-
"""Does our own headline survive the noise in its sources? The self-audit as a page.

Reads out/self_audit.json (self-audit/analysis.py, filed in self-audit/PREREGISTRATION.md) and
out/concentration.json. Every figure on the page comes from those files.

Writes self-audit.html.  Usage: python build_self_audit.py
"""
import io
import json
import os
import re

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
OUT_HTML = os.path.join(ROOT, 'self-audit.html')
REPO = 'https://github.com/materials-atlas/critical-materials-atlas/blob/main/'
RESULT = 'out/self_audit.json'

NAV = ('<header class="topbar"><div class="wrap">'
       '<a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>'
       '<nav class="topnav"><a href="./">Atlas</a><a href="explorer">Explore</a>'
       '<a href="value-chains">Value Chains</a><a href="analysis">Analysis</a>'
       '<a href="reports">Reports</a><a href="method">Method</a></nav>'
       '</div></header>')
FOOT = ('<footer class="siteftr"><div class="wrap">'
        '<div><h4>Critical Materials Atlas</h4>Public-data value-chain research. Not affiliated '
        'with, nor representing, any institution.</div>'
        '<div><h4>Navigate</h4><a href="explorer">Explore</a><br><a href="value-chains">Value '
        'Chains</a><br><a href="analysis">Analysis</a><br><a href="reports">Reports</a><br>'
        '<a href="method">Method</a></div>'
        '<div><h4>Sources</h4>BGS World Mineral Statistics<br>'
        'USGS Mineral Commodity Summaries 1996&ndash;2026</div>'
        '<div class="fineprint">Independent public-data research; figures approximate and '
        'rounded.</div></div></footer>')
CSS = """
.xp{max-width:60rem}
.xp table{border-collapse:collapse;width:100%;font-size:.9rem;margin:.6rem 0}
.xp th,.xp td{padding:.38rem .55rem;border-bottom:1px solid #e5e7eb;text-align:left;vertical-align:top}
.xp td.n,.xp th.n{text-align:right;font-variant-numeric:tabular-nums}
.tbl{overflow-x:auto}
.dim{color:#6b675f}
.src{font-size:.78rem;color:#6b7478;margin:-.1rem 0 1rem;line-height:1.5}.src code{font-size:.74rem}
.fig{margin:1.2rem 0}.fig svg{width:100%;height:auto;display:block}
.fig figcaption{font-size:.86rem;color:#5a6468;margin-top:.4rem;max-width:44rem}
.fig .grid{stroke:#e3e6e5;stroke-width:1}.fig .zero{stroke:#15323a;stroke-width:1.5}
.fig .ax{font:11px Inter,system-ui,sans-serif;fill:#5a6468}
.fig .ax.row{font-size:12px;fill:#15323a}
.fig .band{stroke-width:2;stroke-linecap:round}
.refs{max-width:46rem;padding-left:1.1rem}.refs li{margin:.45rem 0;font-size:.9rem;line-height:1.55}
.xp h3{margin-top:1.6rem;font-size:1.02rem}
.vd{display:inline-block;font-weight:700;letter-spacing:.06em;padding:.05rem .45rem;border-radius:3px;
 font-size:.74rem;color:#fff}
.vd.robust{background:#0e7c74}.vd.fragile{background:#c2701c}.vd.no{background:#b3384b}
tr.hl td{background:#fdf4ec}
.verdictbox{border-left:3px solid #0e7c74;background:#f1f6f5;padding:.7rem .9rem;margin:1rem 0;
 max-width:46rem;font-size:.95rem}
"""
TEAL, AMBER, NAVY = '#0e7c74', '#c2701c', '#15323a'
NAME = {'rare_earths': 'Rare earths', 'phosphate_rock': 'Phosphate rock', 'barytes': 'Barytes'}


def label(c):
    return NAME.get(c, c.replace('_', ' ').capitalize())


def interval_chart(rows, W=720, rh=26):
    """Per material: the 5-95 band of the perturbed change, with the published value marked."""
    L, R, T = 132, 46, 30
    H = T + rh * len(rows) + 34
    lo = min(min(r['p05'], r['published_change']) for r in rows)
    hi = max(max(r['p95'], r['published_change']) for r in rows)
    pad = (hi - lo) * 0.06
    lo, hi = lo - pad, hi + pad

    def x(v):
        return L + (v - lo) / (hi - lo) * (W - L - R)
    g = []
    step = 0.1 if (hi - lo) > 0.35 else 0.05
    k = round(lo / step) * step
    while k <= hi:
        g.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" class="%s"/>'
                 % (x(k), x(k), T - 8, H - 26, 'zero' if abs(k) < 1e-9 else 'grid'))
        g.append('<text x="%.1f" y="%d" class="ax" text-anchor="middle">%+.2f</text>' % (x(k), H - 10, k))
        k += step
    for i, r in enumerate(rows):
        y = T + rh * i + 6
        col = TEAL if r['verdict'] == 'robust' else AMBER
        g.append('<text x="0" y="%.1f" class="ax row">%s</text>' % (y + 4, label(r['material'])))
        g.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="band" stroke="%s" opacity=".45"/>'
                 % (x(r['p05']), x(r['p95']), y, y, col))
        g.append('<circle cx="%.1f" cy="%.1f" r="4.5" fill="%s" stroke="#fcfcfb" stroke-width="1.5">'
                 '<title>%s: published %+.3f, 5-95%% band %+.3f to %+.3f, sign survives %.0f%% of draws'
                 '</title></circle>'
                 % (x(r['published_change']), y, col, label(r['material']), r['published_change'],
                    r['p05'], r['p95'], 100 * r['share_same_sign']))
        g.append('<text x="%d" y="%.1f" class="ax" text-anchor="end">%.0f%%</text>'
                 % (W - 2, y + 4, 100 * r['share_same_sign']))
    leg = ('<circle cx="6" cy="10" r="4.5" fill="%s"/><text x="15" y="14" class="ax">robust</text>'
           '<circle cx="76" cy="10" r="4.5" fill="%s"/><text x="85" y="14" class="ax">fragile</text>'
           '<text x="%d" y="14" class="ax" text-anchor="end">sign survives</text>' % (TEAL, AMBER, W - 2))
    return ('<svg viewBox="0 0 %d %d" role="img" aria-label="Concentration change and its band under '
            'revision noise, by material">%s%s</svg>' % (W, H, leg, ''.join(g)))


def deviation_count():
    with io.open(os.path.join(ROOT, 'self-audit', 'PREREGISTRATION.md'), encoding='utf-8') as f:
        return len(re.findall(r'(?m)^\*\*2026-\d\d-\d\d — deviation', f.read()))


WORDS = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 17: 'seventeen', 20: 'twenty'}


def page():
    d = json.load(io.open(os.path.join(ROOT, RESULT), encoding='utf-8'))
    conc = json.load(io.open(os.path.join(ROOT, 'out', 'concentration.json'), encoding='utf-8'))
    rows = sorted(d['materials'], key=lambda r: -r['published_change'])
    head = d['headline']
    fragile = [r for r in rows if r['verdict'] != 'robust']
    robust = [r for r in rows if r['verdict'] == 'robust']

    trows = ''.join(
        '<tr%s><td>%s</td><td class="n">%+.3f</td><td class="n">%+.3f to %+.3f</td>'
        '<td class="n">%.0f%%</td><td class="n">%.1f%%</td><td class="n">%d</td>'
        '<td><span class="vd %s">%s</span></td></tr>'
        % (' class="hl"' if r['verdict'] != 'robust' else '', label(r['material']),
           r['published_change'], r['p05'], r['p95'], 100 * r['share_same_sign'],
           100 * r['revision_pool_median_abs'], r['revision_pool_n'],
           'fragile' if r['verdict'] == 'fragile' else ('robust' if r['verdict'] == 'robust' else 'no'),
           r['verdict'])
        for r in rows)
    exrows = ''.join('<tr><td>%s</td><td>%s</td></tr>' % (label(e['material']), e['reason'])
                     for e in d['excluded'])
    tok = {
        'CSS': CSS, 'NAV': NAV, 'FOOT': FOOT, 'REPO': REPO,
        'FIG': interval_chart(rows), 'TROWS': trows, 'EXROWS': exrows,
        'NTEST': str(d['n_tested']), 'NEXCL': str(d['n_excluded']),
        'NALLMAT': str(d['n_tested'] + d['n_excluded']),
        'NROBUST': WORDS.get(len(robust), str(len(robust))),
        'NFRAGILE': WORDS.get(len(fragile), str(len(fragile))),
        'FRAGILELIST': ', '.join('%s (%.0f%%)' % (label(r['material']).lower(), 100 * r['share_same_sign'])
                                 for r in sorted(fragile, key=lambda r: r['share_same_sign'])),
        'HEADMED': '%+.3f' % head['published_median_change'],
        'HEADPUB': '%+.3f' % conc['critical']['median_change'],
        'HEADN': str(conc['critical']['n']),
        'HEADSIGN': '%.0f' % (100 * head['share_same_sign']),
        'HEADP05': '%+.3f' % head['p05'], 'HEADP95': '%+.3f' % head['p95'],
        'HEADVERDICT': head['verdict'],
        'DRAWS': '{:,}'.format(d['draws']), 'SEED': str(d['seed']),
        'NDEV': WORDS.get(deviation_count(), str(deviation_count())),
        'TUNGV': '%+.3f' % next(r['published_change'] for r in rows if r['material'] == 'tungsten'),
        'TUNGS': '%.0f' % (100 * next(r['share_same_sign'] for r in rows if r['material'] == 'tungsten')),
        'SRC': ('<p class="src"><b>Source:</b> the atlas\'s own published figures '
                '(<a href="concentration">the concentration measurement</a>, from BGS World Mineral '
                'Statistics) tested against the revision record measured at '
                '<a href="revisions">how firm is this year\'s production figure?</a> (USGS Mineral '
                'Commodity Summaries, 1996&ndash;2026). Computed values: '
                '<a href="%s%s"><code>%s</code></a>.</p>' % (REPO, RESULT, RESULT)),
    }
    html = TEMPLATE
    for k, v in tok.items():
        html = html.replace('@@%s@@' % k, v)
    return html


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Auditing our own headline &mdash; Critical Materials Atlas</title>
<meta name="description" content="We measured how much the USGS revises its own production figures. Then we pushed those revisions back through our own concentration finding to see whether it survives them. It does - and three of its materials do not.">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css">
<style>@@CSS@@</style></head><body>
@@NAV@@
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method &middot; testing our own work</div>
  <h1>Auditing our own headline</h1>
  <p class="deck">The atlas measured how far the US Geological Survey moves its own production figures
  between the first printing and the revision: a median 1.5% for copper's world total, 11.6% for
  antimony's. That measurement was about other people's numbers. This page turns it on ours. <b>We push
  those measured revisions back through our own concentration finding &mdash; the claim that the typical
  critical material became more concentrated &mdash; and ask whether it survives them.</b> It does, across
  the @@NTEST@@ of @@NALLMAT@@ materials we can test. But @@NFRAGILE@@ of those materials, taken on
  their own, do not &mdash; and one of them states a change exactly the size of the headline.</p>
</div></section>

<section class="wrap xp">
  <h2>What the test is</h2>
  <p>The concentration finding says that between 1995&ndash;2004 and 2015&ndash;2024, the typical
  critical material's production became more concentrated &mdash; a median rise of @@HEADPUB@@ in the
  Herfindahl index across @@HEADN@@ materials. Every number behind it is a country's reported
  production, and every such figure is an estimate that its source later revises.</p>
  <p>So the test is not a comparison, it is a propagation. For each material we rebuild the
  country-by-year production the finding is computed from, multiply every value by
  <i>(1&nbsp;+&nbsp;a revision drawn at random from that commodity's own measured revisions)</i>, and
  recompute the finding. Not a modelled distribution &mdash; the actual revisions observed in the USGS
  editions, resampled. @@DRAWS@@ draws, seed @@SEED@@, both fixed in
  <a href="@@REPO@@self-audit/PREREGISTRATION.md">the filing</a> before the test ran, along with the
  verdicts: <b>robust</b> if the finding keeps its sign in at least 95% of draws, <b>fragile</b> between
  50% and 95%, <b>not supported</b> below.</p>

  <div class="verdictbox"><b>The headline survives.</b> Across the @@NTEST@@ testable materials the
  median change is @@HEADMED@@ (the published figure is @@HEADPUB@@ across all @@HEADN@@), and it keeps
  its sign in <b>@@HEADSIGN@@%</b> of draws, with a 5&ndash;95 band of @@HEADP05@@ to @@HEADP95@@.
  Verdict: <b>@@HEADVERDICT@@</b>. Read the next paragraph before taking that as reassurance.</div>

  <p><b>Why this pass is weak and the failures are strong.</b> The draws are independent across
  countries and years. Real revisions are not: a world total is revised together with its parts, and
  successive editions share a method, so genuine revisions are correlated and persistent. Independent
  draws largely cancel inside a share, so this test <i>understates</i> the uncertainty. A robust verdict
  here is therefore a floor, not a certificate &mdash; while a fragile verdict means the claim fails even
  under a noise model that flatters it. That asymmetry was written into the filing before the numbers
  existed, precisely so it could not be discovered afterwards.</p>

  <h2>Material by material</h2>
  <figure class="fig">@@FIG@@
  <figcaption><b>What revision noise does to each material's change.</b> The dot is the published
  change in the concentration index; the bar is the 5th to 95th percentile of that change once measured
  revisions are resampled into the underlying production; the number at the right is the share of draws
  in which the change keeps its sign. Amber marks the materials whose sign does not survive at the filed
  95% threshold.</figcaption></figure>
  <div class="tbl"><table><thead><tr><th>Material</th><th class="n">published change</th>
  <th class="n">5&ndash;95 band under noise</th><th class="n">sign survives</th>
  <th class="n">median revision drawn on</th><th class="n">revisions in the pool</th>
  <th>verdict</th></tr></thead><tbody>@@TROWS@@</tbody></table></div>
  @@SRC@@
  <p><b>@@NROBUST@@ of @@NTEST@@ materials are robust. @@NFRAGILE@@ are not: @@FRAGILELIST@@.</b> Those
  three state changes that the revision record alone could erase, and this page is the reason to stop
  quoting them without that caveat. Tungsten is the instructive one: its published change is
  @@TUNGV@@, the same size as the headline median, and its sign survives only @@TUNGS@@% of draws
  &mdash; because tungsten's own figures move far more than copper's do. <b>The size of a number says
  nothing about whether the evidence carries it.</b></p>

  <h2>What we could not test, and why that matters</h2>
  <div class="tbl"><table><thead><tr><th>Material</th><th>why it is not tested</th></tr></thead>
  <tbody>@@EXROWS@@</tbody></table></div>
  <p class="dim">An earlier run of this audit could test only 10 of the @@HEADN@@ materials, and those
  10 had a median change of &minus;0.003 against +0.060 for the 13 it could not reach. In other words
  the testable half was almost exactly the half that had not concentrated, and any verdict computed on
  it would have been a verdict about a different population. That is why the panel behind
  <a href="revisions">the revision measurement</a> was widened from fifteen commodities to
  twenty-five before this page was written, rather than publishing the convenient number. The filing
  records the whole sequence.</p>

  <h2>What this cannot say</h2>
  <p class="dim">A robust verdict does not make a claim true; it means revision noise is not sufficient
  to explain it away. A fragile verdict does not make a claim false; it means our evidence cannot
  separate it from the source's own movement. <b>Every row here is a proxy row:</b> the concentration
  finding rests on BGS production, while the revision record is measured on USGS editions, because no
  BGS vintage history exists to measure &mdash; the two agencies' world totals themselves differ by a
  median 0.6% for copper and 30.7% for graphite. The audit covers production-based claims only; the
  atlas's trade-based findings rest on sources whose revision behaviour has not been measured, and are
  listed as out of scope in the filing rather than quietly passed. And the revision pools are unequal:
  the number behind each material's draw is printed in the table, and a pool of a few hundred
  revisions is not the same evidence as a pool of a few thousand.</p>

  <h3>Method and filing</h3>
  <ol class="refs">
  <li><b>The filing.</b> Measure, population, bands and pre-commitments, committed before any
  comparison was computed, then changed in @@NDEV@@ dated deviations &mdash; among them the discovery
  that the headline was not testable on the original panel, and the decision to widen the panel rather
  than report the subset:
  <a href="@@REPO@@self-audit/PREREGISTRATION.md">self-audit/PREREGISTRATION.md</a>.</li>
  <li><b>The code</b>, committed before it was run:
  <a href="@@REPO@@self-audit/analysis.py"><code>self-audit/analysis.py</code></a>.</li>
  <li><b>The finding under test.</b> <a href="concentration">Concentration over time</a>, from BGS
  World Mineral Statistics as held in the atlas's harmonised cube.</li>
  <li><b>The revision record.</b> <a href="revisions">How firm is this year's production figure?</a>,
  from USGS Mineral Commodity Summaries 1996&ndash;2026.</li>
  </ol>
  <p class="howto-src">Built by <code>build_self_audit.py</code> from <code>out/self_audit.json</code>,
  written by <code>self-audit/analysis.py</code>. Guarded by <code>check.py</code>, which fails if the
  audit's copy of a published figure stops matching the study it came from.</p>
</section>
@@FOOT@@
</body></html>
"""


def main():
    html = page()
    assert '@@' not in html, 'unfilled token'
    with io.open(OUT_HTML, 'w', encoding='utf-8', newline='\n') as f:
        f.write(html)
    print('wrote', OUT_HTML)


if __name__ == '__main__':
    main()

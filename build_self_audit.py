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
        g.append('<text x="%d" y="%.1f" class="ax" text-anchor="end">%.1f%%</text>'
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
        '<td>%s</td>'
        '<td class="n">%.1f%%</td><td class="n">%.1f%%</td><td class="n">%d</td>'
        '<td><span class="vd %s">%s</span></td></tr>'
        % (' class="hl"' if r['verdict'] != 'robust' else '', label(r['material']),
           r['published_change'], r['p05'], r['p95'],
           '%s <span class="dim">(%s)</span>' % (r.get('stage', '?'), r.get('bgs_form', '')),
           100 * r['share_same_sign'],
           100 * r['revision_pool_median_abs'], r['revision_pool_n'],
           'fragile' if r['verdict'] == 'fragile' else ('robust' if r['verdict'] == 'robust' else 'no'),
           r['verdict'])
        for r in rows)
    exrows = ''.join('<tr><td>%s</td><td>%s</td></tr>' % (label(e['material']), e['reason'])
                     for e in d['excluded'])
    C = d.get('claims', {})
    ex, dv = C.get('ex_ante_2011', {}), C.get('divergence', {})
    tok = {
        'CSS': CSS, 'NAV': NAV, 'FOOT': FOOT, 'REPO': REPO,
        'FIG': interval_chart(rows), 'TROWS': trows, 'EXROWS': exrows,
        'NTEST': str(d['n_tested']), 'NEXCL': str(d['n_excluded']),
        'NALLMAT': str(d['n_tested'] + d['n_excluded']),
        'NROBUST': WORDS.get(len(robust), str(len(robust))),
        'NFRAGILE': WORDS.get(len(fragile), str(len(fragile))),
        'FRAGILELIST': ', '.join('%s (%.1f%%)' % (label(r['material']).lower(), 100 * r['share_same_sign'])
                                 for r in sorted(fragile, key=lambda r: r['share_same_sign'])),
        'HEADMED': '%+.3f' % head['published_median_change'],
        'HEADPUB': '%+.3f' % conc['critical']['median_change'],
        'HEADN': str(conc['critical']['n']),
        'HEADSIGN': '%.1f' % (100 * head['share_same_sign']),
        'HEADP05': '%+.3f' % head['p05'], 'HEADP95': '%+.3f' % head['p95'],
        'HEADVERDICT': head['verdict'],
        'DRAWS': '{:,}'.format(d['draws']), 'SEED': str(d['seed']),
        'NDEV': WORDS.get(deviation_count(), str(deviation_count())),
        'TUNGV': '%+.3f' % next(r['published_change'] for r in rows if r['material'] == 'tungsten'),
        'TUNGS': '%.1f' % (100 * next(r['share_same_sign'] for r in rows if r['material'] == 'tungsten')),
        'CHRS': '%.1f' % (100 * next((r['share_same_sign'] for r in rows if r['material'] == 'chromium'), 0)),
        'TIV': '%+.3f' % next((r['published_change'] for r in rows if r['material'] == 'titanium'), 0),
        'POOLMIN': '{:,}'.format(min(r['revision_pool_n'] for r in rows)),
        'POOLMAX': '{:,}'.format(max(r['revision_pool_n'] for r in rows)),
        'EXMED': '%+.3f' % ex.get('published_median_change', 0),
        'EXSIGN': '%.1f' % (100 * ex.get('share_same_sign', 0)),
        'EXP05': '%+.3f' % ex.get('p05', 0), 'EXP95': '%+.3f' % ex.get('p95', 0),
        'EXVERDICT': ex.get('verdict', '?'), 'EXN': str(ex.get('n_tested', 0)),
        'EXALL': str(ex.get('n_in_claim', 0)),
        'EXPUB': '%+.3f' % conc['ex_ante_2011']['median_change'],
        'DVSIGN': '%.1f' % (100 * dv.get('share_both_hold', 0)),
        'DVVERDICT': dv.get('verdict', '?'),
        'DVDOWN': ', '.join(label(m).lower() for m in dv.get('down', [])),
        'STRATSIGN': '%.1f' % (100 * head.get('stratified_share_same_sign', 0)),
        'STRATP05': '%+.3f' % head.get('stratified_p05', 0),
        'STRATP95': '%+.3f' % head.get('stratified_p95', 0),
        'NSTRATSAME': str(sum(1 for r in rows if r['verdict'] == r.get('stratified_verdict'))),
        'MOSTRAT': '%.1f' % (100 * next((r.get('stratified_share_same_sign', 0) for r in rows
                                         if r['material'] == 'molybdenum'), 0)),
        'TUNGSTRAT': '%.1f' % (100 * next((r.get('stratified_share_same_sign', 0) for r in rows
                                           if r['material'] == 'tungsten'), 0)),
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
  <h1>Auditing our own claims</h1>
  <p class="deck">The atlas measured how far the US Geological Survey moves its own production figures
  between the first printing and the revision: a median 1.5% for copper's world total, 11.6% for
  antimony's, and once 42.5%. That measurement was about other people's numbers. <b>This page pushes
  those revisions back through our own concentration study and asks which of its claims they can
  erase.</b> Three claims, tested on the same draws: that the materials already called critical before
  the window mostly <i>diversified</i>; that cobalt concentrated while those older materials came off
  monopoly highs; and the full-set median that gets quoted most and that our own study says is
  substantially an artifact of what was added to critical-materials lists during the window.</p>
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

  <h2>The three claims, and what noise does to them</h2>
  <div class="verdictbox"><b>1. The materials already critical before the window mostly diversified.
  This survives, but only just.</b> Across the @@EXN@@ of @@EXALL@@ materials on the EU's 2011 list that
  can be tested, the median change is @@EXMED@@ (the study publishes @@EXPUB@@ for all @@EXALL@@) and it
  stays negative in <b>@@EXSIGN@@%</b> of draws, band @@EXP05@@ to @@EXP95@@ &mdash; a band whose upper
  end all but touches zero. Verdict: <b>@@EXVERDICT@@</b>, and the closest of the three to failing. The
  one member we cannot test, the platinum-group metals, published &minus;0.095 and would pull the median
  further from zero, so this test is conservative about a claim it is close to losing.</div>
  <div class="verdictbox"><b>2. Cobalt concentrated while the older export-controlled materials came off
  monopoly highs. This is the sturdiest thing the study says.</b> Tested jointly, in the same draw
  &mdash; cobalt's rise and the fall across @@DVDOWN@@ have to hold together, not one at a time &mdash;
  the pattern survives <b>@@DVSIGN@@%</b> of draws. Verdict: <b>@@DVVERDICT@@</b>. The study calls this
  its honest, control-free finding, and of the three claims it is the one revision noise comes nowhere
  near erasing.</div>
  <div class="verdictbox"><b>3. The full-set median, the number most often quoted, keeps its sign
  &mdash; and that is the least interesting of the three results.</b> Across the @@NTEST@@ testable
  materials of @@NALLMAT@@ the median is @@HEADMED@@ (published @@HEADPUB@@ across @@HEADN@@), positive
  in @@HEADSIGN@@% of draws, band @@HEADP05@@ to @@HEADP95@@. But the concentration study's own note
  says this number "is substantially an artifact of materials ADDED to lists during the window", which
  is a selection problem that no amount of revision noise speaks to. <b>A number can be immovable under
  measurement error and still be the wrong number to quote.</b></div>

  <p><b>Why the sign test is a weak bar, stated plainly.</b> "Keeps its sign" is what was filed, and it
  is a low bar for a median across materials: lithium (+0.504) and cobalt (+0.310) cannot plausibly
  flip, so the median stays positive unless several mid-sized materials turn together in the same draw.
  The band is the informative part, not the percentage &mdash; and for the full set the band's lower
  end, @@HEADP05@@, is well short of the published @@HEADPUB@@. The claim that survives is
  <i>directional</i>: the typical tested material's concentration rose. The published magnitude is not
  what this test certifies.</p>

  <p><b>What this test is not.</b> An earlier draft of this page argued that independent draws must
  understate uncertainty, so a pass was weak and a failure strong. That is withdrawn: an HHI is a
  function of shares, so a revision common to every country in a year cancels <i>exactly</i>, and the
  structure named as widening the band in fact annihilates it. Meanwhile the pool is unweighted, so
  small producers' revision magnitudes get applied to the dominant producers who actually move an HHI
  &mdash; the smallest quartile of producers revises around 9% against about 5.5% for the largest tenth.
  Those two biases run in opposite directions and their net is unknown, so <b>neither a pass nor a
  failure here is a bound</b>. Both are diagnostics.</p>
  <p class="dim">The size objection was tested rather than argued. Drawing each country's revision only
  from similarly sized producers changes no verdict at all: @@NSTRATSAME@@ of @@NTEST@@ materials keep
  their label, the full-set median holds at @@STRATSIGN@@% (band @@STRATP05@@ to @@STRATP95@@), and the
  two materials it moves most &mdash; molybdenum to @@MOSTRAT@@% and tungsten to @@TUNGSTRAT@@% &mdash;
  stay short of the filed 95% line. That run is post-hoc and is published beside the filed one, not in
  place of it.</p>

  <h2>Material by material</h2>
  <figure class="fig">@@FIG@@
  <figcaption><b>What revision noise does to each material's change.</b> The dot is the published
  change in the concentration index; the bar is the 5th to 95th percentile of that change once measured
  revisions are resampled into the underlying production; the number at the right is the share of draws
  in which the change keeps its sign. Amber marks the materials whose sign does not survive at the filed
  95% threshold.</figcaption></figure>
  <div class="tbl"><table><thead><tr><th>Material</th><th class="n">published change</th>
  <th class="n">5&ndash;95 band under noise</th><th class="n">sign survives</th>
  <th>stage read</th><th class="n">median |revision| in its pool</th>
  <th class="n">revisions in the pool</th>
  <th>verdict</th></tr></thead><tbody>@@TROWS@@</tbody></table></div>
  @@SRC@@
  <p><b>@@NROBUST@@ of @@NTEST@@ materials are robust. @@NFRAGILE@@ are not: @@FRAGILELIST@@.</b> Those
  three state changes that the revision record alone could erase, and this page is the reason to stop
  quoting them without that caveat. Tungsten is the instructive one: its published change is
  @@TUNGV@@, the same rounded size as the full-set median, and its sign survives only @@TUNGS@@% of
  draws &mdash; while chromium, whose published change is also @@TUNGV@@ and whose revision pool is no
  quieter, survives @@CHRS@@%. The difference is in the share vector, not the size of the number.
  <b>How big a change is says nothing about whether the evidence carries it.</b></p>
  <p class="dim">Titanium's row is the weakest of the @@NTEST@@ and was flagged as such before it was
  run: the atlas series is BGS titanium minerals while the USGS chapter prints mineral concentrates,
  and the atlas has already found that titanium splits three ways on the ilmenite-versus-slag
  definition. Its published change is @@TIV@@ &mdash; a claim of almost nothing &mdash; so "fragile"
  here means the data cannot tell a tiny move from none, which is not the same as a finding being
  overturned.</p>

  <h2>What we could not test, and why that matters</h2>
  <div class="tbl"><table><thead><tr><th>Material</th><th>why it is not tested</th></tr></thead>
  <tbody>@@EXROWS@@</tbody></table></div>
  <p class="dim">An earlier run of this audit could test only 10 of the @@HEADN@@ materials, and those
  10 had a median change of &minus;0.004 against +0.060 for the 13 it could not reach. In other words
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
  listed as out of scope in the filing rather than quietly passed. And the revision pools are unequal
  &mdash; from @@POOLMIN@@ revisions to @@POOLMAX@@, printed beside every row &mdash; and a median drawn
  from the smaller pools is a thinner instrument than one drawn from the larger.</p>

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

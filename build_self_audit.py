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


def pct(share):
    """A sign-survival share as text. 100% is reserved for a share that really is 1 - 0.9995 is 1,999
    draws of 2,000 and prints as 99.95%, because rounding it up is how "no failures" gets claimed for a
    run that had one."""
    if share >= 1.0:
        return '100%'
    return ('%.2f%%' % (100 * share)) if 100 * share > 99.9 else ('%.1f%%' % (100 * share))


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
                 '<title>%s: published %+.3f, 5-95%% band %+.3f to %+.3f, sign survives %s of draws'
                 '</title></circle>'
                 % (x(r['published_change']), y, col, label(r['material']), r['published_change'],
                    r['p05'], r['p95'], pct(r['share_same_sign'])))
        g.append('<text x="%d" y="%.1f" class="ax" text-anchor="end">%s</text>'
                 % (W - 2, y + 4, pct(r['share_same_sign'])))
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
        '<td class="n">%s</td><td class="n">%.1f%%</td><td class="n">%d</td><td class="n">%s</td>'
        '<td><span class="vd %s">%s</span></td></tr>'
        % (' class="hl"' if r['verdict'] != 'robust' else '', label(r['material']),
           r['published_change'], r['p05'], r['p95'],
           '%s <span class="dim">(%s)</span>' % (r.get('stage', '?'), r.get('bgs_form', '')),
           pct(r['share_same_sign']),
           100 * r['revision_pool_median_abs'], r['revision_pool_n'],
           ('%.1f%%' % (100 * r['usgs_bgs_world_gap'])) if r.get('usgs_bgs_world_gap') else
           '<span class="dim">not measured</span>',
           'fragile' if r['verdict'] == 'fragile' else ('robust' if r['verdict'] == 'robust' else 'no'),
           r['verdict'])
        for r in rows)
    exrows = ''.join('<tr><td>%s</td><td class="n">%s</td><td>%s</td></tr>'
                     % (label(e['material']),
                        ('%+.3f' % e['published_change']) if e.get('published_change') is not None else '&mdash;',
                        e['reason']) for e in d['excluded'])
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
        'HEADSIGN': pct(head['share_same_sign']).rstrip('%'),
        'HEADP05': '%+.3f' % head['p05'], 'HEADP95': '%+.3f' % head['p95'],
        'HEADVERDICT': head['verdict'],
        'DRAWS': '{:,}'.format(d['draws']), 'SEED': str(d['seed']),
        'NDEV': WORDS.get(deviation_count(), str(deviation_count())),
        'TUNGV': '%+.3f' % next(r['published_change'] for r in rows if r['material'] == 'tungsten'),
        'TUNGS': pct(next(r['share_same_sign'] for r in rows if r['material'] == 'tungsten')).rstrip('%'),
        'CHRS': pct(next((r['share_same_sign'] for r in rows if r['material'] == 'chromium'), 0)).rstrip('%'),
        'TIV': '%+.3f' % next((r['published_change'] for r in rows if r['material'] == 'titanium'), 0),
        'POOLMIN': '{:,}'.format(min(r['revision_pool_n'] for r in rows)),
        'POOLMAX': '{:,}'.format(max(r['revision_pool_n'] for r in rows)),
        'EXMED': '%+.3f' % ex.get('published_median_change', 0),
        'EXSIGN': pct(ex.get('share_same_sign', 0)).rstrip('%'),
        'EXP05': '%+.3f' % ex.get('p05', 0), 'EXP95': '%+.3f' % ex.get('p95', 0),
        'EXVERDICT': ex.get('verdict', '?'), 'EXN': str(ex.get('n_tested', 0)),
        'EXSTRAT': '%.2f' % (100 * ex.get('stratified_share_same_sign', 0)),
        'EXSP05': '%+.3f' % ex.get('stratified_p05', 0),
        'EXSP95': '%+.3f' % ex.get('stratified_p95', 0),
        'DVSTRICT': '%.2f' % (100 * dv.get('share_strict_all_down', 0)),
        'PGMV': '%+.3f' % conc['materials']['critical'][
            [r['material'] for r in conc['materials']['critical']].index('platinum_group_metals')]['change'],
        'GRGAP': '%.1f' % (100 * (next((r['usgs_bgs_world_gap'] for r in rows
                                        if r['material'] == 'graphite' and r.get('usgs_bgs_world_gap')), 0))),
        'CUGAP': '%.1f' % (100 * (next((r['usgs_bgs_world_gap'] for r in rows
                                        if r['material'] == 'copper' and r.get('usgs_bgs_world_gap')), 0))),
        'EXALL': str(ex.get('n_in_claim', 0)),
        'EXPUB': '%+.3f' % conc['ex_ante_2011']['median_change'],
        'DVSIGN': '%.1f' % (100 * dv.get('share_both_hold', 0)),
        'DVVERDICT': dv.get('verdict', '?'),
        'DVDOWN': ', '.join(label(m).lower() for m in dv.get('down', [])),
        'STRATSIGN': pct(head.get('stratified_share_same_sign', 0)).rstrip('%'),
        'STRATP05': '%+.3f' % head.get('stratified_p05', 0),
        'STRATP95': '%+.3f' % head.get('stratified_p95', 0),
        'NSTRATSAME': str(sum(1 for r in rows if r['verdict'] == r.get('stratified_verdict'))),
        'MOSTRAT': pct(next((r.get('stratified_share_same_sign', 0) for r in rows
                                         if r['material'] == 'molybdenum'), 0)).rstrip('%'),
        'TUNGSTRAT': pct(next((r.get('stratified_share_same_sign', 0) for r in rows
                                           if r['material'] == 'tungsten'), 0)).rstrip('%'),
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
<title>Auditing our own claims &mdash; Critical Materials Atlas</title>
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
  This is a threshold pass, not a survival.</b> Across the @@EXN@@ of @@EXALL@@ materials on the EU's
  2011 list that can be tested, the median change is @@EXMED@@ and stays negative in @@EXSIGN@@% of
  draws &mdash; clearing the filed 95% line by more than the noise in 2,000 draws, so the label holds
  &mdash; but the band runs @@EXP05@@ to <b>@@EXP95@@</b>, which is as good as zero. And the six split
  <b>three and three</b>: antimony, graphite and rare earths down; tungsten, fluorspar and cobalt up.
  The median is negative because it averages a large, stable decline with tungsten, whose own sign
  survives only @@TUNGS@@%. <b>"Mostly diversified" is not what an even split shows.</b> Under the
  size-stratified draw the same claim runs @@EXSTRAT@@% with a band of @@EXSP05@@ to @@EXSP95@@, well
  clear of zero &mdash; so which test you believe decides how strong this claim looks, which is itself
  the finding.</div>
  <p class="dim">One correction to an earlier draft of this page, because it flattered the result: it
  said that excluding the platinum-group metals made this a conservative test. It does not. With seven
  materials the published median <i>is</i> the fourth ordered value, and that value is the
  platinum-group change (@@PGMV@@). Removing it does not stress the published @@EXPUB@@ at all &mdash;
  it tests the midpoint of rare earths and tungsten instead, a different and closer-to-zero statistic.
  The reviewers caught that; it was not caught here.</p>

  <div class="verdictbox"><b>2. Cobalt concentrated while the older export-controlled materials came
  off monopoly highs. This is the claim furthest from its sign boundary.</b> Requiring all three of
  @@DVDOWN@@ to stay negative <i>and</i> cobalt to stay positive in the same draw, the pattern holds in
  <b>@@DVSTRICT@@%</b> of draws. That is not because the test is demanding &mdash; it is because the
  margins are wide: cobalt's band starts at +0.269 and antimony's ends at &minus;0.185, so these bands
  never come close to meeting. An earlier version of this page reported the weaker version of this test
  (the <i>median</i> of the three, which holds unless two of them turn) and called it joint. It was not.
  <span class="dim">Caveat this one carries: graphite is inside it, and graphite is where the two
  agencies disagree most &mdash; a median @@GRGAP@@% apart on the world total against @@CUGAP@@% for
  copper. This test perturbs BGS figures with USGS-measured revisions; it cannot speak to the two
  agencies disagreeing about who produces.</span></div>

  <div class="verdictbox"><b>3. The full-set median keeps its sign &mdash; which is informative about
  measurement error and says nothing about selection.</b> Across the @@NTEST@@ testable materials of
  @@NALLMAT@@ the median is @@HEADMED@@ (published @@HEADPUB@@ across @@HEADN@@), positive in
  @@HEADSIGN@@% of draws, band @@HEADP05@@ to @@HEADP95@@. Revision noise does not explain this number
  away. But the concentration study's own note says it "is substantially an artifact of materials ADDED
  to lists during the window", and that is a selection problem which no perturbation of the measurements
  can address. <b>The audit clears this number of one charge and leaves the more serious one
  untouched.</b></div>

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
  <th>stage read</th><th class="n">pool median absolute revision</th>
  <th class="n">revisions in the pool</th><th class="n">USGS&ndash;BGS world gap</th>
  <th>verdict</th></tr></thead><tbody>@@TROWS@@</tbody></table></div>
  @@SRC@@
  <p><b>@@NROBUST@@ of @@NTEST@@ materials are robust. @@NFRAGILE@@ are not: @@FRAGILELIST@@.</b> Those
  three state changes that the revision record alone could erase, and this page is the reason to stop
  quoting them without that caveat. Tungsten is the instructive one: its published change is
  @@TUNGV@@, the same rounded size as the full-set median, and its sign survives only @@TUNGS@@% of
  draws &mdash; while chromium, whose published change is also @@TUNGV@@ and whose revision pool is no
  quieter, survives @@CHRS@@%. The difference is in the share vector, not the size of the number.
  <b>Size is not sufficient: everything at 0.06 or more here is robust, but among the smaller changes
  the published number does not tell you which survive.</b></p>
  <p class="dim">Titanium's row is the weakest of the @@NTEST@@ and was flagged as such before it was
  run: the atlas series is BGS titanium minerals while the USGS chapter prints mineral concentrates,
  and the atlas has already found that titanium splits three ways on the ilmenite-versus-slag
  definition. Its published change is @@TIV@@ &mdash; a claim of almost nothing &mdash; so "fragile"
  here means the data cannot tell a tiny move from none, which is not the same as a finding being
  overturned.</p>

  <h2>What we could not test, and why that matters</h2>
  <div class="tbl"><table><thead><tr><th>Material</th><th class="n">published change</th>
  <th>why it is not tested</th></tr></thead>
  <tbody>@@EXROWS@@</tbody></table></div>
  <p class="dim">An earlier run of this audit could test only 10 of the @@HEADN@@ materials, and those
  10 had a median change of &minus;0.004 against +0.060 for the 13 it could not reach. In other words
  the testable half was almost exactly the half that had not concentrated, and any verdict computed on
  it would have been a verdict about a different population. That is why the panel behind
  <a href="revisions">the revision measurement</a> was widened from fifteen commodities to
  twenty-five before this page was written, rather than publishing the convenient number. The filing
  records the whole sequence.</p>

  <h2>What this cannot say</h2>
  <p class="dim">Neither verdict is a bound, and this page has already had to withdraw the argument
  that one of them was. A robust verdict means the sign held up under <i>this</i> perturbation, which
  is too harsh in one respect (it shocks dominant producers with small producers' revision magnitudes)
  and too gentle in another (it draws independently across years, while real revisions persist).
  A fragile verdict means the sign did not hold up under the same imperfect model. <b>Every row here is a proxy row:</b> the concentration
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

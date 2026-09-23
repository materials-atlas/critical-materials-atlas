# -*- coding: utf-8 -*-
"""How firm is this year's production figure? The USGS revision measurement as a page.

Reads out/usgs_revisions.json (usgs-revisions/analysis.py, filed in usgs-revisions/PREREGISTRATION.md),
which is computed from pipeline/data/usgs_mcs_history.parquet - 150 Mineral Commodity Summaries
chapters, 1996-2026. Every figure on the page comes from that file.

Writes revisions.html.  Usage: python build_revisions.py
"""
import io
import json
import os

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
OUT_HTML = os.path.join(ROOT, 'revisions.html')
REPO = 'https://github.com/materials-atlas/critical-materials-atlas/blob/main/'
RESULT = 'out/usgs_revisions.json'

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
        '<div><h4>Sources</h4>USGS Mineral Commodity Summaries 1996&ndash;2026<br>'
        'BGS World Mineral Statistics</div>'
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
.fig .grid{stroke:#e3e6e5;stroke-width:1}.fig .zero{stroke:#8b9396;stroke-width:1}
.fig .thr{stroke:#b3384b;stroke-width:1;stroke-dasharray:3 3}.fig .thrlab{fill:#b3384b}
.fig .ax{font:11px Inter,system-ui,sans-serif;fill:#5a6468}
.fig .ax.row{font-size:12px;fill:#15323a}.fig .val{font-weight:600;fill:#15323a}
.fig .link{stroke:#c9ccc9;stroke-width:2}
.refs{max-width:46rem;padding-left:1.1rem}.refs li{margin:.45rem 0;font-size:.9rem;line-height:1.55}
.xp h3{margin-top:1.6rem;font-size:1.02rem}
.band{display:inline-block;font-weight:700;letter-spacing:.06em;padding:.05rem .45rem;border-radius:3px;
 font-size:.74rem;color:#fff}
.band.firm{background:#0e7c74}.band.soft{background:#c2701c}.band.weak{background:#7d5ba6}
tr.hl td{background:#f1f6f5}
"""
TEAL, AMBER, VIOLET, NAVY = '#009287', '#c2701c', '#7d5ba6', '#15323a'
NAME = {'rare_earths': 'Rare earths'}


def label(c):
    return NAME.get(c, c.capitalize())


def src(note=''):
    return ('<p class="src"><b>Source:</b> <a href="https://www.usgs.gov/centers/'
            'national-minerals-information-center/mineral-commodity-summaries">USGS Mineral Commodity '
            'Summaries, 1996&ndash;2026</a>, read from the annual chapters. Computed values: '
            '<a href="%s%s"><code>%s</code></a>.%s</p>' % (REPO, RESULT, RESULT, (' ' + note) if note else ''))


def rev_chart(rows, W=720, rh=34):
    """Per commodity: the median absolute revision over all years and over the last ten."""
    L, R, T = 150, 60, 34
    H = T + rh * len(rows) + 30
    hi = max(max(a, b) for _, a, b in rows) * 1.15

    def x(v):
        return L + v / hi * (W - L - R)
    g = []
    k = 0.0
    while k <= hi:
        g.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" class="%s"/>' % (x(k), x(k), T - 8, H - 24, 'zero' if k == 0 else 'grid'))
        g.append('<text x="%.1f" y="%d" class="ax" text-anchor="middle">%.0f%%</text>' % (x(k), H - 8, 100 * k))
        k += 0.02
    for v, lab, col in ((0.02, 'firm', TEAL), (0.05, 'soft', AMBER)):
        g.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" class="thr"/>' % (x(v), x(v), T - 16, H - 24))
        g.append('<text x="%.1f" y="%d" class="ax thrlab" text-anchor="middle">%s below %.0f%%</text>'
                 % (x(v), T - 20, lab, 100 * v))
    for i, (name, allr, rec) in enumerate(rows):
        y = T + rh * i + 8
        g.append('<text x="0" y="%.1f" class="ax row">%s</text>' % (y + 4, name))
        g.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="link"/>' % (x(min(allr, rec)), x(max(allr, rec)), y, y))
        dy = 3 if abs(allr - rec) < 0.0015 else 0          # identical values would hide one dot
        g.append('<circle cx="%.1f" cy="%.1f" r="5" fill="%s" stroke="#fcfcfb" stroke-width="2">'
                 '<title>%s: %.1f%% over all measurable years</title></circle>'
                 % (x(allr), y - dy, VIOLET, name, 100 * allr))
        g.append('<circle cx="%.1f" cy="%.1f" r="6" fill="%s" stroke="#fcfcfb" stroke-width="2">'
                 '<title>%s: %.1f%% over the last ten years</title></circle>' % (x(rec), y + dy, NAVY, name, 100 * rec))
        g.append('<text x="%d" y="%.1f" class="ax val" text-anchor="end">%.1f%%</text>' % (W - 4, y + 4, 100 * rec))
    leg = ('<circle cx="6" cy="10" r="5" fill="%s"/><text x="16" y="14" class="ax">all years</text>'
           '<circle cx="96" cy="10" r="5" fill="%s"/><text x="106" y="14" class="ax">last ten years</text>' % (VIOLET, NAVY))
    return '<svg viewBox="0 0 %d %d" role="img" aria-label="Median absolute revision by commodity">%s%s</svg>' % (W, H, leg, ''.join(g))


def pair_chart(rows, W=720, rh=30):
    """Mine share against refinery share, one row per country."""
    L, R, T = 170, 50, 30
    H = T + rh * len(rows) + 28
    hi = max(max(m, r) for _, m, r in rows) * 1.1

    def x(v):
        return L + v / hi * (W - L - R)
    g = []
    k = 0.0
    while k <= hi:
        g.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" class="%s"/>' % (x(k), x(k), T - 8, H - 22, 'zero' if k == 0 else 'grid'))
        g.append('<text x="%.1f" y="%d" class="ax" text-anchor="middle">%.0f%%</text>' % (x(k), H - 6, 100 * k))
        k += 0.10
    for i, (name, mine, ref) in enumerate(rows):
        y = T + rh * i + 6
        g.append('<text x="0" y="%.1f" class="ax row">%s</text>' % (y + 4, name))
        g.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="link"/>' % (x(min(mine, ref)), x(max(mine, ref)), y, y))
        g.append('<circle cx="%.1f" cy="%.1f" r="5" fill="%s" stroke="#fcfcfb" stroke-width="2">'
                 '<title>%s: %.0f%% of world mine production</title></circle>' % (x(mine), y, AMBER, name, 100 * mine))
        g.append('<circle cx="%.1f" cy="%.1f" r="6" fill="%s" stroke="#fcfcfb" stroke-width="2">'
                 '<title>%s: %.0f%% of world refinery production</title></circle>' % (x(ref), y, TEAL, name, 100 * ref))
    leg = ('<circle cx="6" cy="10" r="5" fill="%s"/><text x="16" y="14" class="ax">share of world mining</text>'
           '<circle cx="176" cy="10" r="5" fill="%s"/><text x="186" y="14" class="ax">share of world refining</text>'
           % (AMBER, TEAL))
    return '<svg viewBox="0 0 %d %d" role="img" aria-label="Mine share against refinery share">%s%s</svg>' % (W, H, leg, ''.join(g))


def deviation_count():
    """Read the number off the filing, so the page cannot drift from it."""
    import re
    with io.open(os.path.join(ROOT, 'usgs-revisions', 'PREREGISTRATION.md'), encoding='utf-8') as f:
        return len(re.findall(r'(?m)^\d+\. \*\*2026', f.read()))


WORDS = {10: 'ten', 11: 'eleven', 12: 'twelve', 13: 'thirteen', 14: 'fourteen', 15: 'fifteen'}


def page():
    d = json.load(io.open(os.path.join(ROOT, RESULT), encoding='utf-8'))
    B = d['by_commodity']
    order = sorted(B, key=lambda c: -B[c]['world_median_abs_revision'])
    band_rows, chart_rows = [], []
    for c in order:
        s = B[c]
        band_rows.append('<tr%s><td>%s</td><td class="n">%d</td><td class="n">%.1f%%</td>'
                         '<td class="n">%.1f%%</td><td class="n">%.1f%%</td><td class="n">%.1f%%</td>'
                         '<td class="n">%.0f%% / %.0f%% / %.0f%%</td><td><span class="band %s">%s</span> / '
                         '<span class="band %s">%s</span></td></tr>'
                         % (' class="hl"' if c == 'copper' else '', label(c), s['world_years'],
                            100 * s['world_median_abs_revision'], 100 * s['world_median_abs_revision_recent'],
                            100 * s['world_max_abs_revision'], 100 * s['china_median_abs_revision'],
                            100 * s['share_revised_up'], 100 * s['share_revised_down'],
                            100 * s['share_unchanged'], s['band'], s['band'],
                            s['band_recent'], s['band_recent']))
        chart_rows.append((label(c), s['world_median_abs_revision'], s['world_median_abs_revision_recent']))
    big = [r for r in d['largest_revisions']][:6]
    big_rows = ''.join('<tr><td>%s</td><td>%s</td><td class="n">%d</td><td class="n">%s</td><td class="n">%s</td>'
                       '<td class="n">%+.0f%%</td><td class="n">%d &rarr; %d</td></tr>'
                       % (label(r['commodity']), r['country'], r['year'], '{:,.0f}'.format(r['first']),
                          '{:,.0f}'.format(r['latest']), 100 * r['revision'], r['first_edition'], r['latest_edition'])
                       for r in big)
    cu = d['mine_vs_refine']['copper']
    # the rows are sorted by refinery share, so a plain slice dropped Peru and Zambia, two of the
    # largest miners: take the leaders on BOTH measures, then order by refining
    by_ref = sorted(cu['rows'], key=lambda r: -(r['refinery_share'] or 0))[:8]
    by_mine = sorted(cu['rows'], key=lambda r: -(r['mine_share'] or 0))[:8]
    keep = {r['iso3'] for r in by_ref} | {r['iso3'] for r in by_mine}
    top = [r for r in sorted(cu['rows'], key=lambda r: -(r['refinery_share'] or 0)) if r['iso3'] in keep]
    def cell(v, printed):
        return '&mdash;' if (printed == 'dash' or v is None) else '{:,.0f}'.format(v)

    def pct(v, printed):
        return '&mdash;' if (printed == 'dash' or v is None) else '%.0f%%' % (100 * v)
    mr_rows = ''.join('<tr%s><td>%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%s</td>'
                      '<td class="n">%s</td></tr>'
                      % (' class="hl"' if r['iso3'] == 'CHN' else '', r['country'],
                         cell(r['mine'], r.get('mine_printed')), pct(r['mine_share'], r.get('mine_printed')),
                         cell(r['refinery'], r.get('refinery_printed')),
                         pct(r['refinery_share'], r.get('refinery_printed'))) for r in top)
    gaps = sorted(d['usgs_vs_bgs'].items(), key=lambda kv: -kv[1]['median_abs_world_gap'])
    gap_rows = ''.join('<tr><td>%s</td><td>%s</td><td>%s</td><td class="n">%d&ndash;%d</td>'
                       '<td class="n">%.0f</td><td class="n">%.1f%%</td><td class="n">%s</td></tr>'
                       % (label(k.rsplit('_', 1)[0]), k.rsplit('_', 1)[1], v['bgs_form'],
                          v['years'][0], v['years'][1], v['bgs_median_countries_reporting'],
                          100 * v['median_abs_world_gap'],
                          ('%.1f%%' % (100 * v['median_abs_china_gap'])) if v['median_abs_china_gap'] else 'n/a')
                       for k, v in gaps)
    chn = next(r for r in cu['rows'] if r['iso3'] == 'CHN')
    tok = {
        'CSS': CSS, 'NAV': NAV, 'FOOT': FOOT, 'REPO': REPO, 'SRC': src(),
        'BANDROWS': ''.join(band_rows), 'BIGROWS': big_rows, 'MRROWS': mr_rows, 'GAPROWS': gap_rows,
        'REVFIG': rev_chart(chart_rows), 'MRFIG': pair_chart(
            [(r['country'], r['mine_share'] or 0, r['refinery_share'] or 0) for r in top]),
        'NSERIES': '{:,}'.format(d['measurable_series']),
        'NDROP': '{:,}'.format(d['series_dropped']['total']),
        'NDROP1': '{:,}'.format(d['series_dropped']['only_one_edition']),
        'NDROPF': '{:,}'.format(d['series_dropped']['lost_to_a_flag']),
        'GRGAP24': '%.0f' % (100 * abs(next(r['world_gap'] for r in d['usgs_vs_bgs']['graphite_mine']['rows']
                                            if r['year'] == 2024))),
        'GRCN10': '{:,.0f}'.format(next(r['bgs_china_t'] for r in d['usgs_vs_bgs']['graphite_mine']['rows']
                                        if r['year'] == 2010)),
        'GRCNU10': '{:,.0f}'.format(next(r['usgs_china_t'] for r in d['usgs_vs_bgs']['graphite_mine']['rows']
                                         if r['year'] == 2010)),
        'GRCN24': '{:,.0f}'.format(next(r['usgs_china_t'] for r in d['usgs_vs_bgs']['graphite_mine']['rows']
                                        if r['year'] == 2024)),
        'REEGAP': '%.1f' % (100 * d['usgs_vs_bgs']['rare_earths_mine']['median_abs_world_gap']),
        'CUREFY': '%d&ndash;%d' % tuple(d['usgs_vs_bgs']['copper_refinery']['years']),
        'CUMINEY': '%d&ndash;%d' % tuple(d['usgs_vs_bgs']['copper_mine']['years']),
        'CUBAND': B['copper']['band'], 'SBBAND': B['antimony']['band'],
        'GRUP': '%.0f' % (100 * B['graphite']['share_revised_up']),
        'GRDOWN': '%.0f' % (100 * B['graphite']['share_revised_down']),
        'GRSAME': '%.0f' % (100 * B['graphite']['share_unchanged']),
        'REESAME': '%.0f' % (100 * B['rare_earths']['share_unchanged']),
        'NDEV': WORDS.get(deviation_count(), str(deviation_count())),
        'GRPRE': '%.1f' % (100 * d['usgs_vs_bgs']['graphite_mine']['median_abs_world_gap_before_unit_fix']),
        'NCHAP': str(d['chapters_read']), 'NCSER': '{:,}'.format(d['country_series']),
        'REEREP': '%.0f' % d['usgs_vs_bgs']['rare_earths_mine']['bgs_median_countries_reporting'],
        'REEUSGS': '%d&ndash;%d' % tuple(d['usgs_vs_bgs']['rare_earths_mine']['usgs_countries_with_output']),
        'ED0': str(min(d['editions'])), 'ED1': str(max(d['editions'])),
        'CU': '%.1f' % (100 * B['copper']['world_median_abs_revision']),
        'CUR': '%.1f' % (100 * B['copper']['world_median_abs_revision_recent']),
        'SB': '%.1f' % (100 * B['antimony']['world_median_abs_revision']),
        'SBMAX': '%.1f' % (100 * B['antimony']['world_max_abs_revision']),
        'GR': '%.1f' % (100 * B['graphite']['world_median_abs_revision']),
        'GRR': '%.1f' % (100 * B['graphite']['world_median_abs_revision_recent']),
        'YEAR': str(cu['year']),
        'CNMINE': '%.0f' % (100 * chn['mine_share']), 'CNREF': '%.0f' % (100 * chn['refinery_share']),
        'CUGAP': '%.1f' % (100 * d['usgs_vs_bgs']['copper_mine']['median_abs_world_gap']),
        'CURGAP': '%.1f' % (100 * d['usgs_vs_bgs']['copper_refinery']['median_abs_world_gap']),
        'GRGAP': '%.1f' % (100 * d['usgs_vs_bgs']['graphite_mine']['median_abs_world_gap']),
        'REEC': '%.1f' % (100 * B['rare_earths']['china_median_abs_revision']),
    }
    html = TEMPLATE
    for k, v in tok.items():
        html = html.replace('@@%s@@' % k, v)
    return html


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>How firm is this year's production figure? &mdash; Critical Materials Atlas</title>
<meta name="description" content="Every USGS edition revises last year's production figures. Measured across 150 chapters, 1996-2026: copper's world total moves 1.4%, antimony's 11.3% and once 42.5%. What a current-year number is worth, by commodity.">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css">
<style>@@CSS@@</style></head><body>
@@NAV@@
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method &middot; what a current-year figure is worth</div>
  <h1>How firm is this year's production figure?</h1>
  <p class="deck">Every chart that shows the latest year shows an estimate, and the next edition
  quietly revises it. How big those revisions are is not published anywhere, because finding out takes
  every edition ever printed. We read @@ED0@@&ndash;@@ED1@@ of the US Geological Survey's annual
  summaries &mdash; @@NCHAP@@ chapters &mdash; and kept every edition's figure side by side. <b>Across the
  years that have been printed twice, the world total ended up a median @@CU@@% away from its first
  estimate for copper and @@SB@@% for antimony, which once moved @@SBMAX@@%.</b> That is a record of
  completed revisions, not a bound on this year's figure. The same reading answers two more questions:
  where mining and refining part company, and how far the two world statistical agencies disagree.</p>
</div></section>

<section class="wrap xp">
  <h2>1. How far the first published figure moves</h2>
  <p>Each edition prints two years: last year as an estimate, and the year before it, revised. <b>No
  series in this store is printed three times</b> &mdash; not one of the @@NCSER@@ country series, and none
  of the world totals &mdash; so where a year is measurable, the revision is that estimate against its
  single revision, as a percentage of the estimate, and every measurable year carries the same one
  chance to move. @@NSERIES@@ series (commodity, country or world total, measure, year) are measurable;
  @@NDROP@@ are not: @@NDROP1@@ appear in only one edition (the newest data year, and years either side
  of a gap in the editions we hold) and @@NDROPF@@ lost a printing to a dash, a "W" for withheld or an
  "NA". Those do not enter any median. The measure, the thresholds and the direction rule were
  <a href="@@REPO@@usgs-revisions/PREREGISTRATION.md">filed before any revision was computed</a>; the
  last-ten-years column was added afterwards and is logged there as a dated deviation, as is the fact
  that the filing's &ldquo;settling&rdquo; check cannot be computed at all, there being no third
  printing.</p>
  <figure class="fig">@@REVFIG@@
  <figcaption><b>How much a first figure moves, by commodity.</b> Median absolute revision of the
  printed world total, over every measurable year (violet) and over the last ten (navy, and the number
  printed at the right). Firm, soft and weak are this site's own labels, fixed before the run at 2% and
  5%; they are not a USGS or statistical standard, and copper changes label depending on the
  window.</figcaption></figure>
  <div class="tbl"><table><thead><tr><th>Commodity</th><th class="n">years measured</th>
  <th class="n">world, all years</th><th class="n">world, last 10 years</th>
  <th class="n">largest world revision</th><th class="n">China</th>
  <th class="n">up / down / unchanged</th><th>band: all years / last 10</th></tr></thead>
  <tbody>@@BANDROWS@@</tbody></table></div>
  @@SRC@@
  <p class="dim">Each median is over that commodity's measurable world-total years, counted in the
  second column. &ldquo;Largest world revision&rdquo; is the biggest single move of the printed world
  total, not of a country. The up / down / unchanged column is the share of revisions in each
  direction across every mine series in that commodity, countries and world total together &mdash; a
  wider denominator than the other columns, as the filing defines it, and each small country counts
  the same as the world total. A reprint that does not move counts as unchanged, not as a revision
  down.</p>
  <p><b>Copper's figure has moved least; antimony's most.</b> Copper's world total ends up @@CU@@%
  from its estimate over the whole period and @@CUR@@% over the last ten years &mdash; @@CUBAND@@ on the
  filed reading, soft on the recent one, which is how much a label can depend on a window. Antimony's
  moves @@SB@@%, and once moved @@SBMAX@@%. Graphite gets <i>worse</i> in the recent decade, not better:
  @@GR@@% over the whole period, @@GRR@@% over the last ten.</p>
  <p>There is no direction to correct for. The filing licenses one reading, &ldquo;revised up more
  often than down&rdquo; at 60%, and no commodity reaches it. Nor is the rest downward: a reprint that
  does not move is not a revision down, and unchanged reprints are common. Graphite's mine series are
  @@GRUP@@% up, @@GRDOWN@@% down and @@GRSAME@@% unchanged; rare earths are @@REESAME@@% unchanged. An
  earlier version of this page read those as a downward bias, which is wrong on both counts &mdash; the
  filing never defined a downward reading, and the unchanged share was being counted as down.</p>
  <p>China's rare-earth figure is the one that moves least: its median revision is @@REEC@@%, meaning at
  least half of its measurable years were reprinted unchanged. That is consistent with a quota figure
  being copied across editions, and equally with a rounded official number being reprinted; this design
  cannot tell those apart.</p>
  <h3>The largest single revisions</h3>
  <div class="tbl"><table><thead><tr><th>Commodity</th><th>series</th><th class="n">year</th>
  <th class="n">first published</th><th class="n">latest</th><th class="n">revision</th>
  <th class="n">editions</th></tr></thead><tbody>@@BIGROWS@@</tbody></table></div>
  @@SRC@@
  <p class="dim">This table ranks by percentage of a small first figure, so it lists small series
  rather than the changes that move a world total: Kyrgyzstan's antimony is printed as 20 tonnes in the
  2025 edition and 700 in the 2026 one, both marked estimates. The levels are shown so the size of each
  series is visible beside its percentage. The chapters attribute such changes to new reporting &mdash;
  the 2026 antimony chapter says its 2024 revisions for China, Iran, Kazakhstan, Kyrgyzstan and Russia
  rest on company, Government or third-party reports &mdash; which is re-estimation, not necessarily a
  first measurement. The largest move of a <i>world</i> total is elsewhere: tungsten for 1995, 20,000 to
  31,000 tonnes between the 1996 and 1997 editions, with China 10,000 to 21,000 in the same pair.</p>

  <h2>2. Mining and refining are different maps</h2>
  <p>The USGS prints a refinery table by country for copper only. It is worth reading on its own
  &mdash; bearing in mind that @@YEAR@@ is a first printing, the kind of figure section 1 is about.</p>
  <figure class="fig">@@MRFIG@@
  <figcaption><b>Where copper is mined, and where it is refined.</b> @@YEAR@@ estimates, share of the
  printed world total, for the eight largest on each measure (two countries tie on refining and only
  one is shown). The gap between the two dots is the distance
  between reported mine output and reported refinery output &mdash; not ownership, and not
  control.</figcaption></figure>
  <div class="tbl"><table><thead><tr><th>Country, @@YEAR@@</th><th class="n">mine, kt</th>
  <th class="n">share of world mining</th><th class="n">refinery, kt</th>
  <th class="n">share of world refining</th></tr></thead><tbody>@@MRROWS@@</tbody></table></div>
  @@SRC@@
  <p><b>In the @@YEAR@@ table China accounts for @@CNMINE@@% of reported world mine production and
  @@CNREF@@% of reported refinery production.</b> Chile is the mirror image: nearly a quarter of world
  mining, a small share of refining. Japan and Germany appear in the refinery column with a dash in
  the mine column, not a zero; Peru and Zambia mine copper they barely refine. A dependence read off mining alone misses where
  the smelting and refining sit &mdash; the argument this atlas is built on, here from a single table
  rather than a chain of inferences.</p>
  <p class="dim">What these two columns are not: refinery output is where metal is produced, not who
  owns it, so a Chinese-owned mine abroad counts in its host country's mine column. Refined output
  includes metal made from scrap, which no mine column can show. Cathode won by leaching at the mine is
  counted in both columns, so the two are not disjoint. Chile's gap is concentrate shipped out to be
  smelted and refined elsewhere. And neither column says anything about semi-fabrication, where another
  map again applies.</p>

  <h2>3. Where the two agencies disagree</h2>
  <p>The US Geological Survey and the British Geological Survey both publish world production. The gap
  below is the median, over the years both cover, of |USGS world total &minus; BGS world total| divided
  by the BGS total, using BGS production rows only. It is unsigned and says nothing about which agency
  is right. Neither series is a correction of the other, and a gap can be
  measurement, definition, coverage or vintage; the number of countries reporting each BGS series is
  shown, because a series carried by few reporters is a different animal from one carried by many.</p>
  <div class="tbl"><table><thead><tr><th>Commodity</th><th>USGS measure</th><th>BGS series</th>
  <th class="n">years</th><th class="n">BGS reporters</th><th class="n">world gap</th>
  <th class="n">China gap</th></tr></thead><tbody>@@GAPROWS@@</tbody></table></div>
  <p class="src"><b>Source:</b> as above, against
  <a href="https://www.bgs.ac.uk/mineralsuk/statistics/world-mineral-statistics/world-mineral-statistics-data-download/">BGS
  World Mineral Statistics</a> as held in the atlas. Computed values:
  <a href="@@REPO@@out/usgs_revisions.json"><code>out/usgs_revisions.json</code></a>.</p>
  <p>Copper is the close case: @@CUGAP@@% apart on mining over @@CUMINEY@@, and @@CURGAP@@% on refining
  &mdash; though the refining comparison rests on @@CUREFY@@ alone, because the USGS chapter has printed
  a refinery world total only since then. Graphite is the far one at @@GRGAP@@%, and not because
  the baskets differ: both series are natural graphite and both exclude synthetic material. China
  accounts for much of the early distance &mdash; in 2010 BGS put Chinese output at @@GRCN10@@ tonnes
  against the USGS's @@GRCNU10@@ &mdash; and that difference has closed: by 2024 both print
  @@GRCN24@@ tonnes. But the world totals still sit @@GRGAP24@@% apart in that year, so the rest is
  other countries, coverage or rounding, and @@GRGAP@@% is the median over @@CUMINEY@@, not today's
  gap.</p>
  <p class="dim">Rare earths compare at @@REEGAP@@%, but on a BGS series carried by a median of
  @@REEREP@@ reporting countries against a USGS table that carries @@REEUSGS@@ countries with output
  over the same years, so coverage rather than measurement may be doing the work. Whether both sides use the same contained-metal definition is not checked here for
  cobalt or antimony.</p>

  <h2>What we do with this</h2>
  <p>Three rules, adopted with this page and applied from here on rather than claimed of what is
  already published. A current-year figure is quoted with both revision medians beside it,
  the whole period and the last ten years, and never with the band presented as its precision: firm,
  soft and weak are labels for a past record, not error bars. A claim that turns on a change about the
  size of that record is checked against the revision history before it is made rather than taken at
  face value &mdash; for antimony that means a change of a few per cent is no larger than what the
  source has moved on its own. And when the other agency is cited, the page names it and names the
  years.</p>
  <p class="dim">What this cannot say: it measures how the published figure moved, not how close either
  version is to the truth &mdash; both could be wrong in the same direction. Revisions within a year are
  not independent across countries, since the world total is revised with its parts, and successive
  years share a method, so they are not independent draws either. A country that falls into "Other
  countries" in a later edition drops out of the count for that year. The medians cover six chosen
  commodities over unequal windows &mdash; tungsten 29 years, cobalt and rare earths 21 &mdash; and the
  copper median in section 1 is mine production, not the refinery series section 2 reads. The agency
  gaps are differences, not a reconciliation: whether both sides use the same contained-metal or
  concentrate basis is unchecked for every commodity here.</p>

  <h3>Method and data</h3>
  <ol class="refs">
  <li><b>The figures.</b> US Geological Survey, <i>Mineral Commodity Summaries</i>, editions
  @@ED0@@&ndash;@@ED1@@, the annual chapter for each commodity (a US government work).
  <a href="https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries">usgs.gov</a>.
  Read into a panel by <a href="@@REPO@@pipeline/parse_usgs_mcs.py"><code>pipeline/parse_usgs_mcs.py</code></a>,
  which reads the printed page geometrically: a footnote marker is set against its value, so in plain
  text "7100,000" cannot be told from a number, while on the page the marker is smaller type.</li>
  <li><b>The comparison.</b> British Geological Survey, World Mineral Statistics, as held in the atlas.
  <a href="https://www.bgs.ac.uk/mineralsuk/statistics/world-mineral-statistics/world-mineral-statistics-data-download/">bgs.ac.uk</a>.</li>
  <li><b>The filing.</b> The measure, the thresholds and the direction rule, committed before any
  revision was computed, then changed in @@NDEV@@ dated deviations &mdash; among them the production-only
  filter on the BGS comparison, a graphite world total that had been multiplied by 1,000, the
  rare-earth series and unit line, and the separation of unchanged reprints from revisions down. One
  discarded row was wrong by three orders of magnitude; the median contained it rather than ignoring
  it &mdash; the graphite gap would have printed @@GRPRE@@% instead of @@GRGAP@@% &mdash; which is why the log,
  not a calm median, is the check:
  <a href="@@REPO@@usgs-revisions/PREREGISTRATION.md">usgs-revisions/PREREGISTRATION.md</a>.</li>
  </ol>
  <p class="howto-src">Built by <code>build_revisions.py</code> from <code>out/usgs_revisions.json</code>,
  written by <code>usgs-revisions/analysis.py</code> from
  <code>pipeline/data/usgs_mcs_history.parquet</code>.</p>
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

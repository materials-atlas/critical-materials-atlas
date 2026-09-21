# -*- coding: utf-8 -*-
"""Did China's export controls bite? The pre-registered export-controls study as a page.

Reads out/export_controls.json, written by export-controls/analysis.py. Every figure on the page comes
from that file. Writes export-controls.html.  Usage: python build_export_controls.py
"""
import io
import json
import math
import os

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
OUT_HTML = os.path.join(ROOT, 'export-controls.html')
REPO = 'https://github.com/materials-atlas/critical-materials-atlas/blob/main/'
THR = math.log(0.70)                                   # the filing's 30% fall

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
        '<div><h4>Sources</h4>Eurostat Comext &middot; US Census Bureau<br>MOFCOM announcements</div>'
        '<div class="fineprint">Independent public-data research; figures approximate and '
        'rounded.</div></div></footer>')
CSS = """
.xp{max-width:60rem}
.xp table{border-collapse:collapse;width:100%;font-size:.9rem;margin:.6rem 0}
.xp th,.xp td{padding:.38rem .55rem;border-bottom:1px solid #e5e7eb;text-align:left;vertical-align:top}
.xp td.n,.xp th.n{text-align:right;font-variant-numeric:tabular-nums}
.tbl{overflow-x:auto}
.note{background:#f7f7f5;border-left:3px solid #0e7c74;padding:.7rem 1rem;margin:1rem 0;font-size:.93rem}
.dim{color:#6b675f}
.src{font-size:.78rem;color:#6b7478;margin:-.1rem 0 1rem;line-height:1.5}.src code{font-size:.74rem}
.fig{margin:1.2rem 0}.fig svg{width:100%;height:auto;display:block}
.fig figcaption{font-size:.86rem;color:#5a6468;margin-top:.4rem;max-width:44rem}
.fig .grid{stroke:#e3e6e5;stroke-width:1}.fig .zero{stroke:#8b9396;stroke-width:1}
.fig .thr{stroke:#b3384b;stroke-width:1;stroke-dasharray:3 3}.fig .thrlab{fill:#b3384b}
.fig .reach{stroke:#e8e6e1;stroke-width:12;stroke-linecap:round}
.fig .ci{stroke-width:2.5;opacity:.55}.fig .dot{stroke:#fcfcfb;stroke-width:2}
.fig .ax{font:11px Inter,system-ui,sans-serif;fill:#5a6468}
.fig .ax.row{font-size:12px;fill:#15323a}.fig .val{font-weight:600;fill:#15323a}
.fig .ln{fill:none;stroke:#15323a;stroke-width:2;stroke-linejoin:round}
.fig .pre{stroke:#8b9396;stroke-width:1;stroke-dasharray:4 3}
.fig .post{fill:#009287;opacity:.10}.fig .ev{stroke:#b3384b;stroke-width:1}
.fig .hit{fill:transparent}.fig .hit:hover{fill:#15323a}
.fig .link{stroke:#c9ccc9;stroke-width:2}
.small2{display:grid;grid-template-columns:repeat(auto-fit,minmax(18rem,1fr));gap:1rem}
.cite{font-size:.72rem}.cite a{text-decoration:none}
.refs{max-width:46rem;padding-left:1.1rem}.refs a{overflow-wrap:anywhere}.refs li{margin:.45rem 0;font-size:.9rem;line-height:1.55}
.xp h3{margin-top:1.6rem;font-size:1.02rem}
.verdict{display:inline-block;background:#15323a;color:#fff;font-weight:700;letter-spacing:.08em;
 padding:.15rem .6rem;border-radius:4px;font-size:.8rem}
.verdict.x{background:#7d5ba6}
.xp tr.hl td{background:#f1f6f5}
"""

# Every source opened before use (21 Sep 2026). The MOFCOM texts are the official Chinese originals.
REFS = [
    ('M23', 'Ministry of Commerce and General Administration of Customs of China (2023). Announcement '
     '2023 No. 23 on export controls on gallium- and germanium-related items (in Chinese).',
     'http://www.mofcom.gov.cn/zcfb/dwmygl/art/2023/art_52b9a321087f402bb3d310d18b07967e.html'),
    ('M39', 'Ministry of Commerce and General Administration of Customs of China (2023). Announcement '
     '2023 No. 39 on optimising the temporary export controls on graphite items (in Chinese; text as '
     'republished on the Ministry&rsquo;s export-control information site).',
     'http://exportcontrol.mofcom.gov.cn/article/zcfg/gnzcfg/zcfggzqd/202310/912.html'),
    ('M33', 'Ministry of Commerce and General Administration of Customs of China (2024). Announcement '
     '2024 No. 33 on export controls on antimony and other items (in Chinese).',
     'https://www.mofcom.gov.cn/zwgk/zcfb/art/2024/art_a4711acb06364199a3c5a06d7f2be6d8.html'),
    ('M46', 'Ministry of Commerce of China (2024). Announcement 2024 No. 46 on strengthening export '
     'controls on dual-use items to the United States (in Chinese).',
     'https://exportcontrol.mofcom.gov.cn/article/zcfg/gnzcfg/zcfggzqd/202412/1072.html'),
    ('M72', 'Ministry of Commerce of China (2025). Announcement 2025 No. 72, suspending clause 2 of '
     'Announcement 2024 No. 46 until 27 November 2026 (in Chinese).',
     'https://www.mofcom.gov.cn/zcfb/blgg/gg/2025/art/2025/art_bc4513421bb24faaa84e44c2e4f36dc5.html'),
    ('M10', 'Ministry of Commerce and General Administration of Customs of China (2025). Announcement '
     '2025 No. 10 on export controls on tungsten-, tellurium-, bismuth-, molybdenum- and indium-related '
     'items (in Chinese).',
     'https://www.mofcom.gov.cn/zwgk/zcfb/art/2025/art_e623090907fc4e1092f0a4db72f57b95.html'),
    ('M18', 'Ministry of Commerce and General Administration of Customs of China (2025). Announcement '
     '2025 No. 18 on export controls on certain medium and heavy rare-earth items (in Chinese).',
     'https://www.mofcom.gov.cn/zwgk/zcfb/art/2025/art_9c2108ccaf754f22a34abab2fedaa944.html'),
    ('M70', 'Ministry of Commerce and General Administration of Customs of China (2025). Announcement '
     '2025 No. 70, suspending Announcements 2025 Nos. 55-58, 61 and 62 until 10 November 2026 (in Chinese).',
     'https://www.mofcom.gov.cn/zwgk/zcfb/art/2025/art_b1ec77dd3f0d4762952904df7cdaadec.html'),
    ('M57', 'Ministry of Commerce and General Administration of Customs of China (2025). Announcement '
     '2025 No. 57 on export controls on certain further medium and heavy rare-earth items (in Chinese).',
     'https://www.mofcom.gov.cn/zcfb/blgg/gg/2025/art/2025/art_9510f263c3c246d8936fbfa684a58ca8.html'),
    ('M58', 'Ministry of Commerce and General Administration of Customs of China (2025). Announcement '
     '2025 No. 58 on export controls on lithium batteries and artificial-graphite anode materials (in '
     'Chinese).', 'https://www.mofcom.gov.cn/zcfb/blgg/gg/2025/art/2025/art_8ef8c6bf57e3437e826fcdf1c469aff8.html'),
    ('SED2026', 'Seoul Economic Daily (2026). "Korea Zinc\'s Onsan smelter produces 10 tons daily of '
     'defense-critical antimony," 8 March 2026.',
     'https://en.sedaily.com/finance/2026/03/08/korea-zincs-onsan-smelter-produces-10-tons-daily-of-defense'),
    ('NW1987', 'Newey, W. K. and West, K. D. (1987). "A simple, positive semi-definite, heteroskedasticity '
     'and autocorrelation consistent covariance matrix." <i>Econometrica</i> 55(3): 703&ndash;708.',
     'https://doi.org/10.2307/1913610'),
    ('BW2020', 'Bellemare, M. F. and Wichman, C. J. (2020). "Elasticities and the inverse hyperbolic sine '
     'transformation." <i>Oxford Bulletin of Economics and Statistics</i> 82(1): 50&ndash;61.',
     'https://doi.org/10.1111/obes.12325'),
    ('CR2024', 'Chen, J. and Roth, J. (2024). "Logs with zeros? Some problems and solutions." '
     '<i>The Quarterly Journal of Economics</i> 139(2): 891&ndash;936.',
     'https://doi.org/10.1093/qje/qjad054'),
]
REFNUM = {k: i + 1 for i, (k, _, _) in enumerate(REFS)}


def cite(*keys):
    return ('<sup class="cite">[%s]</sup>'
            % ','.join('<a href="#ref-%s">%d</a>' % (k, REFNUM[k]) for k in keys))


COMEXT = ('Eurostat Comext, monthly detailed trade (CN8)',
          'https://ec.europa.eu/eurostat/api/dissemination/files?dir=comext%2FCOMEXT_DATA%2FPRODUCTS')
CENSUS = ('US Census Bureau, international trade API (HS10)',
          'https://www.census.gov/data/developers/data-sets/international-trade.html')
RESULT = 'out/export_controls.json'
ORIGINS = 'out/export_controls_origins.json'
COMTRADE = ('UN Comtrade, monthly, as reported by the importer', 'https://comtradeplus.un.org/')
BGSSRC = ('BGS World Mineral Statistics', 'https://www.bgs.ac.uk/mineralsuk/statistics/world-mineral-statistics/world-mineral-statistics-data-download/')


def src2(extra, note=''):
    a = ' &middot; '.join('<a href="%s">%s</a>' % (u, t) for t, u in ([COMEXT] + extra))
    return ('<p class="src"><b>Source:</b> %s. Computed values: <a href="%s%s"><code>%s</code></a>.%s</p>'
            % (a, REPO, ORIGINS, ORIGINS, (' ' + note) if note else ''))


def src(us=False, note=''):
    a = ' &middot; '.join('<a href="%s">%s</a>' % (u, t) for t, u in ([COMEXT] + ([CENSUS] if us else [])))
    return ('<p class="src"><b>Source:</b> %s. Computed values: <a href="%s%s"><code>%s</code></a>.%s</p>'
            % (a, REPO, RESULT, RESULT, (' ' + note) if note else ''))


# Validated for colour-vision separation against the page surface (dataviz validator, 20 Sep 2026).
TEAL, VIOLET = '#009287', '#7d5ba6'
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def ym_label(ym):
    return '%s %s' % (MONTHS[int(ym[4:]) - 1], ym[:4])


def shift(ym, k):
    y, m = int(ym[:4]), int(ym[4:]) + k
    while m > 12:
        y, m = y + 1, m - 12
    while m < 1:
        y, m = y - 1, m + 12
    return '%04d%02d' % (y, m)


def month_chart(r, title, W=460, H=230):
    """Monthly EU imports from China of one treated good: the pre-period mean, the control, months 7-12."""
    L, R, T, B = 48, 12, 16, 34
    ms = r['monthly']
    vals = [m['china_t'] for m in ms]
    hi = max(vals) * 1.1 or 1.0
    step = 10 ** math.floor(math.log10(hi / 2.0))
    ticks = [k * step for k in range(0, int(hi / step) + 1)]
    while len(ticks) > 6:
        step *= 2
        ticks = [k * step for k in range(0, int(hi / step) + 1)]
    n = len(ms)

    def x(i):
        return L + i / float(n - 1) * (W - L - R)

    def y(v):
        return T + (hi - v) / hi * (H - T - B)
    idx = {m['ym']: i for i, m in enumerate(ms)}
    g = []
    for t in ticks:
        g.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" class="%s"/>' % (L, W - R, y(t), y(t), 'zero' if t == 0 else 'grid'))
        g.append('<text x="%d" y="%.1f" class="ax" text-anchor="end">%s</text>' % (L - 6, y(t) + 4, '{:,.0f}'.format(t)))
    eff = r['in_force']
    p0, p1 = shift(eff, 7), shift(eff, 12)
    if p0 in idx:
        a, b = idx[p0], idx.get(p1, n - 1)
        g.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" class="post"/>' % (x(a) - 3, T, x(b) - x(a) + 6, H - T - B))
        g.append('<text x="%.1f" y="%d" class="ax" text-anchor="middle">months 7&ndash;12</text>' % ((x(a) + x(b)) / 2, T + 10))
    if eff in idx:
        g.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" class="ev"/>' % (x(idx[eff]), x(idx[eff]), T, H - B))
        g.append('<text x="%.1f" y="%d" class="ax thrlab" text-anchor="end">in force</text>' % (x(idx[eff]) - 4, T + 10))
    pre = r['levels']['treated']['pre']['china_t_per_month']
    ann = r['announced']
    if ann in idx:
        g.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="pre"/>' % (x(0), x(idx[ann]), y(pre), y(pre)))
    pts = ' '.join('%.1f,%.1f' % (x(i), y(v)) for i, v in enumerate(vals))
    g.append('<polyline points="%s" class="ln"/>' % pts)
    for i, m in enumerate(ms):
        g.append('<circle cx="%.1f" cy="%.1f" r="4" class="hit"><title>%s: %s t from China</title></circle>'
                 % (x(i), y(m['china_t']), ym_label(m['ym']), '{:,.1f}'.format(m['china_t'])))
    for i, m in enumerate(ms):
        if m['ym'].endswith('01'):
            g.append('<text x="%.1f" y="%d" class="ax" text-anchor="middle">%s</text>' % (x(i), H - B + 18, m['ym'][:4]))
    return '<svg viewBox="0 0 %d %d" role="img" aria-label="%s">%s</svg>' % (W, H, title, ''.join(g))


def forest(rows, title, lo=-5.2, hi=1.6, W=720, rh=34):
    """China-origin quantity against the comparison, 95% interval, the band the design could not see."""
    L, R, T = 230, 20, 40
    H = T + rh * len(rows) + 34

    def x(v):
        return L + (min(max(v, lo), hi) - lo) / float(hi - lo) * (W - L - R)
    g = []
    t = math.ceil(lo)
    while t <= hi + 1e-9:
        g.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%.1f" class="%s"/>'
                 % (x(t), x(t), T - 10, H - 30, 'zero' if t == 0 else 'grid'))
        g.append('<text x="%.1f" y="%d" class="ax" text-anchor="middle">%s</text>' % (x(t), H - 12, ('%+d' % t) if t else '0'))
        t += 1
    g.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%.1f" class="thr"/>' % (x(THR), x(THR), T - 10, H - 30))
    g.append('<text x="%.1f" y="%d" class="ax thrlab" text-anchor="middle">a 30%% fall (filed)</text>' % (x(THR), T - 16))
    for i, (label, est, clo, chi, mde) in enumerate(rows):
        yy = T + rh * i + 10
        can = mde <= abs(THR)
        col = TEAL if can else VIOLET
        g.append('<text x="0" y="%.1f" class="ax row">%s</text>' % (yy + 4, label))
        g.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="reach"/>' % (x(-mde), x(mde), yy, yy))
        g.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="ci" stroke="%s"/>' % (x(clo), x(chi), yy, yy, col))
        g.append('<circle cx="%.1f" cy="%.1f" r="5" class="dot" fill="%s"><title>%s: %+.2f (%+.2f to %+.2f); the design '
                 'could reliably see only effects beyond %.2f</title></circle>' % (x(est), yy, col, label, est, clo, chi, mde))
    leg = ('<circle cx="6" cy="12" r="5" fill="%s"/><text x="16" y="16" class="ax">could see a 30%% fall</text>'
           '<circle cx="160" cy="12" r="5" fill="%s"/><text x="170" y="16" class="ax">could not</text>'
           '<line x1="250" x2="280" y1="12" y2="12" class="reach"/><text x="288" y="16" class="ax">not detectable with 80%% certainty</text>'
           % (TEAL, VIOLET))
    return '<svg viewBox="0 0 %d %d" role="img" aria-label="%s">%s%s</svg>' % (W, H, title, leg, ''.join(g))


def price_chart(rows, title, W=720, rh=32):
    """Unit value, months 7-12 over the pre-period: the treated good and its comparison, raw."""
    L, R, T = 230, 70, 34
    H = T + rh * len(rows) + 30
    lo, hi = math.log(0.5), math.log(5.0)

    def x(v):
        return L + (math.log(v) - lo) / (hi - lo) * (W - L - R)
    g = []
    for t in (0.5, 1, 2, 3, 4, 5):
        g.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%.1f" class="%s"/>' % (x(t), x(t), T - 8, H - 26, 'zero' if t == 1 else 'grid'))
        g.append('<text x="%.1f" y="%d" class="ax" text-anchor="middle">&times;%s</text>' % (x(t), H - 8, ('%g' % t)))
    for i, (label, tr, cp) in enumerate(rows):
        yy = T + rh * i + 8
        g.append('<text x="0" y="%.1f" class="ax row">%s</text>' % (yy + 4, label))
        g.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" class="link"/>' % (x(tr), x(cp), yy, yy))
        g.append('<circle cx="%.1f" cy="%.1f" r="5" class="dot" fill="%s"><title>comparison: &times;%.2f</title></circle>' % (x(cp), yy, VIOLET, cp))
        g.append('<circle cx="%.1f" cy="%.1f" r="6" class="dot" fill="%s"><title>%s: &times;%.2f</title></circle>' % (x(tr), yy, TEAL, label, tr))
        g.append('<text x="%d" y="%.1f" class="ax val" text-anchor="end">&times;%.1f</text>' % (W - 4, yy + 4, tr))
    leg = ('<circle cx="6" cy="12" r="5" fill="%s"/><text x="16" y="16" class="ax">controlled good</text>'
           '<circle cx="130" cy="12" r="5" fill="%s"/><text x="140" y="16" class="ax">its comparison</text>' % (TEAL, VIOLET))
    return '<svg viewBox="0 0 %d %d" role="img" aria-label="%s">%s%s</svg>' % (W, H, title, leg, ''.join(g))


def gap_chart(rows, title, W=720, rh=28):
    """Change in EU imports by origin, tonnes a month, months 7-12 against the pre-period."""
    L, R, T = 250, 60, 12
    H = T + rh * len(rows) + 30
    lo = min(0.0, min(v for _, v, _ in rows)) * 1.1
    hi = max(0.0, max(v for _, v, _ in rows)) * 1.1
    step = 50 if hi - lo > 200 else 20 if hi - lo > 60 else 10

    def x(v):
        return L + (v - lo) / (hi - lo) * (W - L - R)
    g = []
    k = math.ceil(lo / step) * step
    while k <= hi:
        g.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" class="%s"/>' % (x(k), x(k), T, H - 24, 'zero' if k == 0 else 'grid'))
        g.append('<text x="%.1f" y="%d" class="ax" text-anchor="middle">%+d</text>' % (x(k), H - 8, k) if k else
                 '<text x="%.1f" y="%d" class="ax" text-anchor="middle">0</text>' % (x(k), H - 8))
        k += step
    for i, (lab, v, kind) in enumerate(rows):
        y = T + rh * i
        col = {'china': VIOLET, 'gain': TEAL, 'net': '#9aa3a6', 'total': '#15323a'}[kind]
        a, b = sorted((x(0), x(v)))
        g.append('<text x="0" y="%.1f" class="ax row">%s</text>' % (y + 14, lab))
        g.append('<rect x="%.1f" y="%.1f" width="%.1f" height="14" rx="3" fill="%s"><title>%s: %+.1f t a month</title></rect>'
                 % (a, y + 3, max(b - a, 1), col, lab, v))
        g.append('<text x="%.1f" y="%.1f" class="ax val" text-anchor="%s">%+.0f</text>'
                 % (b + 5 if v >= 0 else a - 5, y + 14, 'start' if v >= 0 else 'end', v))
    return '<svg viewBox="0 0 %d %d" role="img" aria-label="%s">%s</svg>' % (W, H, title, ''.join(g))


def load_origins():
    with io.open(os.path.join(ROOT, ORIGINS), encoding='utf-8') as f:
        return json.load(f)


def load():
    with io.open(os.path.join(ROOT, RESULT), encoding='utf-8') as f:
        return json.load(f)


READ = {'untestable at a 30% fall': 'untestable', 'no visible effect': 'no visible fall', 'bit': 'bit',
        'diverted': 'diverted', 'inconclusive': 'inconclusive'}
LABEL = {'C1': 'Gallium and germanium', 'C2': 'Natural graphite', 'C4': 'Rare-earth magnets',
         'C4r': 'Gd, Tb, Dy metals and compounds', 'C5': 'Antimony', 'C6': 'Bismuth'}
CMP = {'magnesium': 'unwrought magnesium', 'talc_baryte': 'talc and baryte', 'ferrite': 'ferrite magnets',
       'lree': 'lanthanum and cerium compounds'}


def iv(x):
    return '%+.2f <span class="dim">(%+.2f to %+.2f)</span>' % (x['estimate'], x['ci95'][0], x['ci95'][1])


def tn(v):
    return '{:,.1f}'.format(v) if v < 100 else '{:,.0f}'.format(v)


def page():
    e = load()
    eu = [r for r in e['results'] if r['importer'] == 'EU']
    R = {r['control']: r for r in eu}
    sb, bi = R['C5'], R['C6']

    def lv(r, side, per, k):
        return r['levels'][side][per][k]

    def mult(r, side='treated'):
        return lv(r, side, 'post', 'unit_value_per_kg') / lv(r, side, 'pre', 'unit_value_per_kg')

    rows_est, rows_lv, forest_rows, price_rows = [], [], [], []
    for r in eu:
        oc = r['outcomes']
        c, t, p = oc['y_china'], oc['y_total'], oc['y_price']
        rows_est.append('<tr><td>%s</td><td>%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%s</td>'
                        '<td class="n">%.2f</td><td>%s</td><td>%s</td></tr>' % (
                            LABEL[r['control']], CMP[r['comparison']], iv(c), iv(t),
                            iv(p) + ' <span class="dim">%+.0f%%</span>' % p['pct'], c['mde_80'],
                            READ[r['reading_as_filed']], READ[r['reading_corrected_precedence']]))
        rows_lv.append('<tr><td>%s</td><td class="n">%s &rarr; %s</td><td class="n">%s &rarr; %s</td>'
                       '<td class="n">%s &rarr; %s</td><td class="n">&times;%.1f</td><td class="n">&times;%.2f</td></tr>' % (
                           LABEL[r['control']], tn(lv(r, 'treated', 'pre', 'china_t_per_month')),
                           tn(lv(r, 'treated', 'post', 'china_t_per_month')),
                           tn(lv(r, 'treated', 'pre', 'total_t_per_month')), tn(lv(r, 'treated', 'post', 'total_t_per_month')),
                           '{:,.1f}'.format(lv(r, 'treated', 'pre', 'unit_value_per_kg')),
                           '{:,.1f}'.format(lv(r, 'treated', 'post', 'unit_value_per_kg')), mult(r), mult(r, 'comparison')))
        forest_rows.append((LABEL[r['control']], c['estimate'], c['ci95'][0], c['ci95'][1], c['mde_80']))
        price_rows.append((LABEL[r['control']], mult(r), mult(r, 'comparison')))

    n_untest = sum(1 for r in eu if r['reading_as_filed'].startswith('untestable'))
    O = load_origins()
    NAME = {'MM': 'Myanmar', 'VN': 'Viet Nam', 'MY': 'Malaysia', 'TH': 'Thailand', 'KR': 'South Korea',
            'KZ': 'Kazakhstan'}

    def gap_rows(cid):
        c = O['controls'][cid]
        rows = [('China', c['china_t_month'][1] - c['china_t_month'][0], 'china')]
        named = 0.0
        for r in c['origins']:
            tag = ' (candidate)' if r['transit_candidate'] else '' if r['class'] == 'producer' else ' (refiner?)'
            rows.append((NAME.get(r['origin'], r['name']) + tag, r['change_t_month'], 'gain'))
            named += r['change_t_month']
        rows.append(('all other origins, net', (c['others_t_month'][1] - c['others_t_month'][0]) - named, 'net'))
        tot = (c['china_t_month'][1] + c['others_t_month'][1]) - (c['china_t_month'][0] + c['others_t_month'][0])
        rows.append(('total EU imports', tot, 'total'))
        return rows

    cmp_rows = []
    for cid in ('C1', 'C2', 'C4', 'C4r', 'C5', 'C6'):
        cp = O['controls'][cid]['comparison']
        ws = cp['china_share_world_production']
        cmp_rows.append('<tr%s><td>%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%.0f%%</td>'
                        '<td class="n">%.2f</td><td class="n">&times;%.1f</td></tr>' % (
                            ' class="hl"' if cid in ('C5', 'C6') else '', LABEL[cid],
                            ' / '.join('%.0f%%' % (100 * v) for v in ws.values()),
                            ' / '.join(str(v) for v in cp['other_countries_5pct'].values()),
                            100 * cp['china_share_eu_imports_pre'], cp['china_tonnes_after_over_before'],
                            cp['unit_value_multiple']))
    B = O['part_b']
    kr, my = B['C6_KR'], B['C5_MY']
    kr_o = [r for r in O['controls']['C6']['origins'] if r['origin'] == 'KR'][0]
    my_o = [r for r in O['controls']['C5']['origins'] if r['origin'] == 'MY'][0]
    sbo = O['controls']['C5']

    def win(r, a, b):
        # mean China tonnes and all-origin unit value over months a..b (inclusive), from the monthly series
        ms = [m for m in r['monthly'] if a <= m['ym'] <= b]
        tot = sum(m['total_t'] for m in ms)
        val = sum(m['total_t'] * m['uv'] for m in ms if m['uv'] is not None)
        return sum(m['china_t'] for m in ms) / len(ms), val / tot
    sb_ann, bi_eff = sb['announced'], bi['in_force']
    sb_late = win(sb, shift(sb_ann, -4), shift(sb_ann, -1))
    sb_early = win(sb, sb['window'][0], shift(sb_ann, -5))
    bi_a = win(bi, shift(bi_eff, 4), shift(bi_eff, 8))
    bi_b = win(bi, shift(bi_eff, 9), shift(bi_eff, 12))
    spike = max(sb['monthly'], key=lambda m: m['china_t'] if m['ym'] >= sb['in_force'] else -1)
    tok = {
        'CSS': CSS, 'NAV': NAV, 'FOOT': FOOT, 'REPO': REPO,
        'FIG_SB': month_chart(sb, 'EU imports of antimony from China, tonnes a month'),
        'FIG_BI': month_chart(bi, 'EU imports of bismuth from China, tonnes a month'),
        'FOREST': forest(forest_rows, 'China-origin imports against the comparison, by control'),
        'PRICE': price_chart(price_rows, 'Unit value after the control, as a multiple of before'),
        'ESTROWS': ''.join(rows_est), 'LVROWS': ''.join(rows_lv),
        'NUNT': {5: 'Five', 4: 'Four', 6: 'All six', 3: 'Three'}.get(n_untest, str(n_untest)),
        'NUNTL': {5: 'five', 4: 'four', 6: 'all six', 3: 'three'}.get(n_untest, str(n_untest)),
        'SB_PRE': tn(lv(sb, 'treated', 'pre', 'china_t_per_month')), 'SB_POST': tn(lv(sb, 'treated', 'post', 'china_t_per_month')),
        'SB_TPRE': '{:,.0f}'.format(lv(sb, 'treated', 'pre', 'total_t_per_month')),
        'SB_TPOST': '{:,.0f}'.format(lv(sb, 'treated', 'post', 'total_t_per_month')),
        'SB_UV0': '%.1f' % lv(sb, 'treated', 'pre', 'unit_value_per_kg'), 'SB_UV1': '%.1f' % lv(sb, 'treated', 'post', 'unit_value_per_kg'),
        'SB_M': '%.1f' % mult(sb), 'BI_M': '%.1f' % mult(bi),
        'SB_TOT': iv(sb['outcomes']['y_total']),
        'BI_PRE': tn(lv(bi, 'treated', 'pre', 'china_t_per_month')), 'BI_POST': tn(lv(bi, 'treated', 'post', 'china_t_per_month')),
        'BI_FALL': '%.0f' % (100 * (1 - lv(bi, 'treated', 'post', 'china_t_per_month') / lv(bi, 'treated', 'pre', 'china_t_per_month'))),
        'BI_TPRE': '{:,.0f}'.format(lv(bi, 'treated', 'pre', 'total_t_per_month')),
        'BI_TPOST': '{:,.0f}'.format(lv(bi, 'treated', 'post', 'total_t_per_month')),
        'SB_REL': '%.1f' % math.exp(sb['outcomes']['y_price']['estimate']),
        'BI_REL': '%.1f' % math.exp(bi['outcomes']['y_price']['estimate']),
        'MG_SB': '%.2f' % mult(sb, 'comparison'),
        'HR_M': '%.1f' % mult(R['C4r']),
        'GA_M': '%.1f' % mult(R['C1']), 'GA_REL': '%+.0f' % R['C1']['outcomes']['y_price']['pct'],
        'SRC': src(), 'SRC_US': src(us=True),
        'LAST': ym_label(e['last_month']),
        'GAP_SB': gap_chart(gap_rows('C5'), 'Change in EU antimony imports by origin'),
        'GAP_BI': gap_chart(gap_rows('C6'), 'Change in EU bismuth imports by origin'),
        'CMPROWS': ''.join(cmp_rows), 'SRC_O': src2([BGSSRC]), 'SRC_B': src2([COMTRADE]),
        'SRC_C': src2([BGSSRC]),
        'SB_PRODSH': '%.0f' % (100 * sbo['replacement_share_from_producers']),
        'SB_FALLS': ', '.join('%s (%+.0f tonnes a month)' % (f['name'].replace('Türkiye', 'T&uuml;rkiye'), f['change_t_month'])
                              for f in sbo['largest_falls']),
        'MY_POST': '%.0f' % my_o['post_t_month'], 'MY_CN0': '%.2f' % my['imports_from_china_t_month_pre'],
        'MY_CN1': '%.2f' % my['imports_from_china_t_month_0_12'],
        'KR_PRE': '%.1f' % kr_o['pre_t_month'], 'KR_POST': '%.0f' % kr_o['post_t_month'],
        'KR_CN0': '%.1f' % kr['imports_from_china_t_month_pre'], 'KR_CN1': '%.1f' % kr['imports_from_china_t_month_0_12'],
        'KR_MON': '%d of %d' % (kr['post_months_available'], kr['post_months_filed']),
        'SB_WS': '%.0f' % (100 * O['controls']['C5']['comparison']['china_share_world_production']['antimony']),
        'BI_WS': '%.0f' % (100 * O['controls']['C6']['comparison']['china_share_world_production']['bismuth']),
        'SB_CNSH': '%.0f' % (100 * lv(sb, 'treated', 'pre', 'china_t_per_month') / lv(sb, 'treated', 'pre', 'total_t_per_month')),
        'BI_OTH0': '%.0f' % (lv(bi, 'treated', 'pre', 'total_t_per_month') - lv(bi, 'treated', 'pre', 'china_t_per_month')),
        'BI_OTH1': '%.0f' % (lv(bi, 'treated', 'post', 'total_t_per_month') - lv(bi, 'treated', 'post', 'china_t_per_month')),
        'SB_LATE': '%.0f' % sb_late[0], 'SB_LATE_UV': '%.0f' % sb_late[1], 'SB_EARLY': '%.0f' % sb_early[0],
        'SB_EARLY_UV': '%.0f' % sb_early[1], 'SB_LATE_FROM': ym_label(shift(sb_ann, -4)),
        'SB_LATE_TO': ym_label(shift(sb_ann, -1)),
        'SPIKE_M': ym_label(spike['ym']), 'SPIKE_T': '%.0f' % spike['china_t'],
        'BI_A': '%.0f' % bi_a[0], 'BI_A_UV': '%.0f' % bi_a[1], 'BI_B': '%.0f' % bi_b[0], 'BI_B_UV': '%.0f' % bi_b[1],
        'BI_A_FROM': ym_label(shift(bi_eff, 4)), 'BI_A_TO': ym_label(shift(bi_eff, 8)),
        'BI_B_FROM': ym_label(shift(bi_eff, 9)), 'BI_B_TO': ym_label(shift(bi_eff, 12)),
    }
    for k in REFNUM:
        tok['C_' + k] = cite(k)
    tok['REFLIST'] = ''.join('<li id="ref-%s">%s <a href="%s">%s</a></li>' % (k, t, u, u.replace('https://', '').replace('http://', ''))
                             for k, t, u in REFS)
    html = TEMPLATE
    for k, v in tok.items():
        html = html.replace('@@%s@@' % k, v)
    return html


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Did China's export controls bite? &mdash; Critical Materials Atlas</title>
<meta name="description" content="A pre-registered test of six Chinese export controls, 2023-2025, in the EU's and the United States' monthly import records: as filed, none is shown to bite; antimony and bismuth imports from China collapsed and their prices rose, an exploratory reading.">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css">
<style>@@CSS@@</style></head><body>
@@NAV@@
<section class="hero"><div class="wrap">
  <div class="eyebrow">Export controls &middot; a pre-registered test</div>
  <h1>Did China's export controls bite?</h1>
  <p class="deck">Between 2023 and 2025 China put export licences on gallium and germanium, graphite,
  antimony, bismuth and seven rare earths. We filed a test before pulling the data: in the EU's and the
  United States' own monthly import records, did less arrive from China, did the price rise, did less
  arrive in total? <b>As filed, no control is shown to bite.</b> In the EU, @@NUNTL@@ of the six series are
  too thin for the test to have reliably seen the 30% fall it asked for, and rare-earth magnets, the one
  series that could have seen it, show none; in the United States the filed comparisons fail and there
  is no reading. Two EU series show large movements in the raw record. <b>EU imports of antimony from China fell from @@SB_PRE@@ to @@SB_POST@@ tonnes a month and the
  unit value of all antimony imports rose @@SB_M@@-fold; bismuth from China fell by @@BI_FALL@@% and the
  unit value of all bismuth imports rose @@BI_M@@-fold.</b> Antimony's fall had begun months before the
  control was announced, and reading either as a bite comes from a rule corrected after the data, so
  both are exploratory.</p>
</div></section>

<section class="wrap xp">
  <div class="small2">
  <figure class="fig">@@FIG_SB@@<figcaption><b>Antimony from China, tonnes a month.</b> EU imports from
  outside the EU. Red line: the control took effect (15 Sep 2024)@@C_M33@@; dashed: the mean before it
  was announced; shaded: months 7&ndash;12, the period the test reads. The fall had started by spring
  2024, before the announcement. The @@SPIKE_M@@ peak (@@SPIKE_T@@ t, all unwrought antimony, into four
  member states) came after the control took effect, most likely the first licensed or contracted
  shipments; it lies outside both periods the test compares.</figcaption></figure>
  <figure class="fig">@@FIG_BI@@<figcaption><b>Bismuth from China, tonnes a month.</b> The control took
  effect on announcement (4 Feb 2025)@@C_M10@@; same marks. A burst of shipments in the first months,
  a trough from mid-2025, and a partial recovery by early 2026.</figcaption></figure>
  </div>
  @@SRC@@

  <h2>1. The six controls</h2>
  <p>Each was checked against the announcement itself, in the Chinese original. The October 2025
  expansions were suspended on 7 November 2025 and are not tested. The import data end in @@LAST@@.</p>
  <div class="tbl"><table><thead><tr><th></th><th>Control</th><th>Announced</th><th>In force</th>
  <th>Tested in the EU as</th></tr></thead><tbody>
  <tr><td>C1</td><td>Gallium and germanium@@C_M23@@</td><td>3 Jul 2023</td><td>1 Aug 2023</td><td>unwrought gallium and germanium, and their powders</td></tr>
  <tr><td>C2</td><td>Graphite: natural flake and its products, including spherical; high-specification artificial graphite@@C_M39@@</td><td>20 Oct 2023</td><td>1 Dec 2023</td><td>natural graphite in powder or flakes only</td></tr>
  <tr><td>C3</td><td>Ban in principle on gallium, germanium and antimony to the United States@@C_M46@@</td><td>3 Dec 2024</td><td>3 Dec 2024; suspended 9 Nov 2025@@C_M72@@</td><td>(US only)</td></tr>
  <tr><td>C4</td><td>Seven medium and heavy rare earths, including samarium-cobalt and terbium- or dysprosium-containing NdFeB magnets@@C_M18@@</td><td>4 Apr 2025</td><td>4 Apr 2025</td><td>metal magnets of Nd, Pr, Dy or Sm; and Gd, Tb, Dy metals and compounds</td></tr>
  <tr><td>C5</td><td>Antimony@@C_M33@@</td><td>15 Aug 2024</td><td>15 Sep 2024</td><td>ores and concentrates, unwrought metal and powder, waste and scrap, articles</td></tr>
  <tr><td>C6</td><td>Bismuth metal, with tungsten, tellurium, molybdenum and indium items@@C_M10@@</td><td>4 Feb 2025</td><td>4 Feb 2025</td><td>bismuth unwrought, powder, waste and scrap, and articles</td></tr>
  </tbody></table></div>
  <p class="src"><b>Source:</b> the Ministry of Commerce announcements listed under References. The
  customs codes for each line are in the <a href="@@REPO@@export-controls/PREREGISTRATION.md">filing</a>.</p>

  <h2>2. The test, as filed</h2>
  <p><span class="verdict">NO CONTROL SHOWN TO BITE, AS FILED</span></p>
  <p>Each controlled good was set against a comparison good that China also dominates and that no
  control we found covers &mdash; unwrought magnesium for the metals, talc and baryte for graphite,
  ferrite magnets for rare-earth magnets, lanthanum and cerium compounds for the heavy rare earths. These
  are coarse comparisons: each has its own market and can move for its own reasons (magnesium's price
  swung widely in 2021&ndash;2022), and a comparison bought almost entirely from China, like magnesium,
  also nets out anything that hit all Chinese exports at once, which pushes towards finding no effect.
  Ferrite magnets are a substitute for rare-earth magnets, so a switch between them moves both sides. The monthly gap between the two was compared before and after, with an
  anticipation window between announcement and entry into force, errors robust to
  autocorrelation@@C_NW1987@@, and a correction for running six tests at once (Holm&rsquo;s). The filing read months 7&ndash;12 after entry into force. A control
  <i>bit</i> if imports from China fell by at least 30% against the comparison and either the total fell
  by 20% or the price rose by 20%. And the filing said to check first whether the design could have
  seen a 30% fall at all: if not, the control is <i>untestable</i>, not a null.</p>
  <p><b>@@NUNT@@ of the six EU controls are untestable by that rule, and rare-earth magnets show no
  visible fall.</b> The quantities are thin and jumpy month to month; only the magnet series is steady enough to see a
  30% fall.</p>
  <figure class="fig">@@FOREST@@
  <figcaption><b>Imports from China against the comparison, months 7&ndash;12.</b> Each dot is the
  estimate with its 95% interval; the faint band is what the series could not have told from zero with
  80% certainty. Teal: the design could see the filed 30% fall. Violet: it could not. The scale is the
  difference in the inverse hyperbolic sine of kilograms, not a percentage (see below).</figcaption></figure>
  <div class="tbl"><table><thead><tr><th>Control</th><th>compared with</th><th class="n">from China</th>
  <th class="n">all origins</th><th class="n">unit value</th><th class="n">could see (80%)</th>
  <th>reading as filed</th><th>corrected order (exploratory)</th></tr></thead>
  <tbody>@@ESTROWS@@</tbody></table></div>
  @@SRC@@
  <p class="dim">Quantities are differences of the inverse hyperbolic sine of kilograms, which keeps the
  months when nothing arrived from China; such a difference is not a percentage, and when a series
  approaches zero it is not a log change either@@C_BW2020@@@@C_CR2024@@. The unit value is a true log
  difference and its percentage is shown. The last column reverses the order of the filed rule so that
  an interval already beyond the threshold decides the reading whatever the power; that correction was
  made after the estimates were seen, and it is reported beside the filed reading, not in place of it.
  It also reads the quantity gaps against a 30% line drawn for logs, which is least valid for antimony,
  whose China series has months with almost nothing arriving.</p>

  <h2>3. What the series show</h2>
  <p>Leave the comparison aside and look at the tonnes and the prices themselves: the mean month in the
  two years before each announcement against the mean month in months 7&ndash;12 after the control.</p>
  <div class="tbl"><table><thead><tr><th>Control</th><th class="n">from China, t a month</th>
  <th class="n">all origins, t a month</th><th class="n">unit value, &euro;/kg</th>
  <th class="n">price multiple</th><th class="n">comparison's price multiple</th></tr></thead>
  <tbody>@@LVROWS@@</tbody></table></div>
  @@SRC@@
  <p class="dim">These are before-and-after means, not effects. Buyers can stock up before a control and
  draw down afterwards, and a customs unit value moves with the mix of grades shipped as well as with the
  price.</p>
  <figure class="fig">@@PRICE@@
  <figcaption><b>Prices after the controls, as a multiple of before.</b> Unit value of all EU imports of
  each controlled good, and of its comparison, months 7&ndash;12 against the pre-period. Log scale.
  Antimony and bismuth more than doubled, and so did the heavy rare earths, whose monthly unit value is
  too erratic (small, mixed shipments) to read; the comparisons fell or, for lanthanum and cerium
  compounds, rose far less. Customs unit values, not transaction prices.</figcaption></figure>
  @@SRC@@

  <h3>Antimony: imports from China all but stopped; total imports did not fall</h3>
  <p><span class="verdict x">EXPLORATORY</span></p>
  <p>EU imports of antimony from China fell from @@SB_PRE@@ tonnes a month to @@SB_POST@@, while antimony
  from all origins went from @@SB_TPRE@@ to @@SB_TPOST@@ tonnes a month: imports from other origins made up
  the difference. China supplied only about @@SB_CNSH@@% of EU antimony tonnes even
  before, so the price below is mostly that of antimony from elsewhere. The unit value of all EU antimony
  imports rose from &euro;@@SB_UV0@@ to &euro;@@SB_UV1@@ a kilogram, @@SB_M@@-fold, and not because the mix
  changed: unwrought antimony, most of the tonnage, rose about as much on its own, and ores and
  concentrates rose too. The estimate against magnesium (&times;@@SB_REL@@) is larger
  because magnesium itself got cheaper over the same months (&times;@@MG_SB@@).</p>
  <p><b>Much of this began before the control.</b> Imports from China averaged @@SB_EARLY@@ tonnes a
  month at a unit value of &euro;@@SB_EARLY_UV@@ over most of the pre-period, but only @@SB_LATE@@ tonnes a
  month at &euro;@@SB_LATE_UV@@ in the four months before the announcement (@@SB_LATE_FROM@@ to
  @@SB_LATE_TO@@). The squeeze was under way before August 2024, and the announcement formalised it; this
  design cannot separate the two, nor the EU price from China's December 2024 ban on antimony exports to
  the United States, which fell inside the same window. If there was a bite in Europe, it shows in imports from China and in
  the price, not in total import volume.</p>
  <h3>Bismuth: less from China and less in total, at a higher unit value</h3>
  <p><span class="verdict x">EXPLORATORY</span></p>
  <p>Bismuth from China fell from @@BI_PRE@@ to @@BI_POST@@ tonnes a month in months 7&ndash;12, and total
  imports from @@BI_TPRE@@ to @@BI_TPOST@@. Bismuth from other origins rose, from about @@BI_OTH0@@ to
  @@BI_OTH1@@ tonnes a month, and filled part of the gap, not all of it. The unit value of all
  bismuth imports rose @@BI_M@@-fold (&times;@@BI_REL@@ against magnesium). Of the six, bismuth is the only
  one where all three outcomes &mdash; imports from China, total imports and the unit value &mdash;
  passed the filed thresholds against its comparison, each with its interval excluding zero. The squeeze eased late in the window:
  imports from China averaged @@BI_A@@ tonnes a month at &euro;@@BI_A_UV@@ a kilogram from @@BI_A_FROM@@ to
  @@BI_A_TO@@, and @@BI_B@@ tonnes at &euro;@@BI_B_UV@@ from @@BI_B_FROM@@ to @@BI_B_TO@@.</p>
  <h3>The rest</h3>
  <p><b>Gallium and germanium</b> are too thin to test: a few tonnes a month, with the unit value up
  @@GA_M@@-fold (@@GA_REL@@% against magnesium, more than half of which is magnesium getting cheaper). The
  customs lines cover the unwrought metals and powders, not the oxides and other compounds the control
  also covers.
  <b>Natural graphite</b> from China rose in tonnes, and as filed the reading is untestable; the synthetic
  and spherical graphite the control also covers is not in the customs lines the filing locked, so this
  says nothing about them. The 2023 announcement also revised controls on graphite in place since 2006,
  so the years before it are not an uncontrolled baseline. <b>Rare-earth
  magnet</b> imports from China rose relative to ferrite magnets, which rules out a 30% fall against
  ferrite, not any effect; the customs line holds every neodymium, praseodymium, dysprosium and samarium
  magnet, while the control covers only samarium-cobalt and terbium- or dysprosium-containing magnets, so
  an effect on those would be diluted. <b>The heavy rare earths</b> &mdash; gadolinium, terbium,
  dysprosium metals and compounds &mdash; halved in total, but the China-origin series is a few tonnes a
  month and the unit value jumps by factors of ten from month to month, so neither says whose supply
  moved.</p>

  <h2>4. Who replaced China?</h2>
  <p>A follow-up, filed as an amendment before its data were read, asked where the replacement came from:
  from countries that produce the metal, or from countries that might be passing Chinese material on.
  Each origin that added to EU imports was classed as a <i>producer</i> if its own output, in the British
  Geological Survey's world statistics, covers at least a year of what it now ships to the EU, and
  otherwise a <i>non-producer</i>. A non-producer whose shipments at least tripled, by 10 tonnes a month
  or more, became a <i>transit candidate</i>, and its own imports from China were then checked in the
  UN Comtrade records it reports.</p>
  <figure class="fig">@@GAP_SB@@
  <figcaption><b>Antimony: who filled the gap.</b> Change in EU imports, tonnes a month, months 7&ndash;12
  after the control against the two years before announcement. Violet: China. Teal: the origins that
  together supplied at least 80% of the increase. &ldquo;Refiner?&rdquo; marks a non-producer on the
  screen, which counts only mine output.</figcaption></figure>
  @@SRC_O@@
  <p><b>Antimony: re-sourced, mostly from South-East Asia.</b> The reshuffle ran both ways: @@SB_FALLS@@
  also shipped less. Myanmar, which mines antimony, supplied the largest part of the increase; Viet Nam and Thailand, which the screen reads as non-producers but which may refine ore
  mined elsewhere, and Malaysia, which had shipped none before, supplied most of the rest. Only
  @@SB_PRODSH@@% of the increase came from countries whose own mines cover it. Malaysia is the one
  transit candidate (0 to @@MY_POST@@ tonnes a month), but its own records show almost no unwrought
  antimony from China, before or after (@@MY_CN0@@ and @@MY_CN1@@ tonnes a month): <b>not consistent with
  rerouting</b>. In the three months checked, what Malaysia imported was antimony ore, from Myanmar,
  T&uuml;rkiye, Thailand and elsewhere.</p>
  <figure class="fig">@@GAP_BI@@
  <figcaption><b>Bismuth: who filled the gap.</b> Same measure. Other origins made up less than half of what
  China stopped sending, and total imports fell.</figcaption></figure>
  @@SRC_O@@
  <p><b>Bismuth: South Korea, from its own smelters.</b> Korea's shipments to the EU rose from
  @@KR_PRE@@ to @@KR_POST@@ tonnes a month, which made it a transit candidate, since it mines no bismuth.
  But its own imports of bismuth from China <i>fell</i>, from @@KR_CN0@@ to @@KR_CN1@@ tonnes a month
  (@@KR_MON@@ months reported): <b>not consistent with rerouting</b>. Korea Zinc recovers bismuth, with
  antimony and indium, from the by-products of its zinc, lead and copper smelting@@C_SED2026@@, so the rise
  is most plausibly Korean refined output that a mine-based screen cannot see.</p>
  @@SRC_B@@
  <p class="dim">Neither check is proof: material can be processed in a third country, declared under
  another customs line, or come from stocks. What the records show is that neither candidate was buying
  more from China.</p>

  <h2>5. Why these two?</h2>
  <p>If controls bite where China matters most, antimony and bismuth should stand out on China's share of
  world production, on the scarcity of other producers, or on Europe's reliance on China before the
  control. The same amendment set the question before reading the production figures, and said the
  answer would be reported whichever way it fell. With six controls it is a description, not a test.</p>
  <div class="tbl"><table><thead><tr><th>Control</th><th class="n">China's share of world production,
  2021&ndash;23</th><th class="n">other countries with 5%+</th><th class="n">China's share of EU imports
  before</th><th class="n">tonnes from China, after &divide; before</th><th class="n">unit value
  multiple</th></tr></thead><tbody>@@CMPROWS@@</tbody></table></div>
  @@SRC_C@@
  <p><b>They stand out on none of the three.</b> Antimony (@@SB_WS@@%) and bismuth (@@BI_WS@@%) have the
  <i>lowest</i> Chinese share of world mine production of the six; every series but gallium and germanium
  has three other producers above 5%; and Europe's reliance on China before the control was the lowest
  of the six for antimony and among the highest for bismuth. The measure may be at the wrong stage: the
  British statistics record where antimony and bismuth are <i>mined</i>, but China's controls cover the
  refined metal, and the open data do not give a clean world series for refining. A rule of thumb of
  the form &ldquo;controls bite where China mines most&rdquo; does not survive this table.</p>

  <h2>6. The United States: no answer</h2>
  <p>The same test was filed for US imports, and the comparisons filed for it do not support a reading.
  US imports of magnesium from China fell by about 90% between 2021 and 2025, so any good compared with it
  looks as if its China imports rose; US talc imports jumped six-fold in recorded kilograms in 2023 with
  their value flat, which looks like a change in recording; and US ferrite magnets are counted in pieces,
  not kilograms.
  Magnesium was found after the first run and the other two after the second, each logged in the
  filing. There is no clean US customs line for the heavy rare earths, and US general imports include
  goods later re-exported. No replacement
  comparisons were chosen after seeing the data, so the US half has no reading, including the outright
  ban on gallium, germanium and antimony to the United States (C3)@@C_M46@@.</p>
  <p class="src"><b>Source:</b> <a href="@@REPO@@export-controls/PREREGISTRATION.md">filing,
  deviations 3 and 7</a>; <a href="https://www.census.gov/data/developers/data-sets/international-trade.html">US
  Census Bureau, international trade API (HS10)</a>.</p>
</section>

<section class="wrap xp">
  <h2>What to watch</h2>
  <p>Two suspensions end within weeks of this page. China's October 2025 announcements &mdash; among them
  further medium and heavy rare earths@@C_M57@@ and lithium batteries and artificial-graphite anode
  material@@C_M58@@ &mdash; are suspended until <b>10 November 2026</b>@@C_M70@@, and the ban in principle
  on gallium, germanium and antimony to the United States until <b>27 November 2026</b>@@C_M72@@. If they
  return, the EU record will show it first in the lines this page follows: a fall in tonnes from China,
  a rise in the unit value of all imports, and new origins whose own imports should be checked. Eurostat's
  monthly figures run about two months behind (July 2026 was the latest month available on 21 September),
  so a change in November 2026 would show in the data in early 2027.</p>
  <p>Three things this study suggests for anyone who buys these metals. <b>Price moved more reliably than
  supply</b>: in both cases where something happened, the unit value of all imports rose two- to
  four-fold, while total tonnes held for antimony. <b>Replacement did not come only from mines</b>:
  much of the gap was filled by countries that mine little or none of the metal &mdash; South Korea
  recovers bismuth at its smelters, and Malaysia imports antimony ore &mdash; which a mine-based view of
  supply misses. <b>The public record cannot certify a bite month by month</b> for
  thin, lumpy trade: a filed test built to avoid reading noise as an effect could not confirm what the
  raw series show, and a buyer watching for the next control should watch the series themselves.</p>
</section>

<section class="wrap xp">
  <h2>What this can and cannot say</h2>
  <p>It is the EU's import record, to @@LAST@@, against coarse comparison goods, not a causal estimate.
  Magnesium is bought almost entirely from China, and its EU unit value roughly tripled between early
  2021 and mid-2022 before falling back; the years the test uses as &ldquo;before&rdquo; contain parts of
  that swing, so every price estimate against it carries some of it, which is why the raw multiples are
  shown beside it. Customs value is not a
  contract price, and a unit value of a small-volume good can move with the mix of what was shipped.
  Material shipped ahead of a control shows up as anticipation, licences granted are not observed, and
  routing through a third country is inferred from the pattern, not seen.</p>
  <p>What it does say: in Europe's customs record, antimony and bismuth show large movements around
  their controls &mdash; imports from China fell, antimony's to almost nothing, and the unit value of
  all imports rose several-fold &mdash; while the filed test, built to guard against reading noise as
  effects, could not certify either as a bite. For antimony the fall began before the control, so the
  record cannot say how much of it the control caused. Both readings are reported because a
  pre-registered test that cannot see what the raw series show is a finding about the test as much as
  about the controls.</p>

  <h3>References</h3>
  <ol class="refs">@@REFLIST@@</ol>

  <h3>Data</h3>
  <ol class="refs">
  <li><b>EU imports.</b> Eurostat Comext, monthly detailed trade by CN8 code, imports of the EU27 from
  outside the EU, the United Kingdom excluded throughout; January 2021 to @@LAST@@. Reused under the
  Commission&rsquo;s reuse policy (CC BY 4.0). <a href="https://ec.europa.eu/eurostat/api/dissemination/files?dir=comext%2FCOMEXT_DATA%2FPRODUCTS">Bulk download</a>.</li>
  <li><b>Transit candidates' imports.</b> UN Comtrade, monthly imports as reported by Malaysia and the
  Republic of Korea, partner China; derived figures only, not redistributed.
  <a href="https://comtradeplus.un.org/">comtradeplus.un.org</a>.</li>
  <li><b>World production.</b> British Geological Survey, World Mineral Statistics, as held in the atlas,
  mean 2021&ndash;2023. <a href="https://www.bgs.ac.uk/mineralsuk/statistics/world-mineral-statistics/world-mineral-statistics-data-download/">bgs.ac.uk</a>.</li>
  <li><b>US imports.</b> US Census Bureau international trade API, general imports by HS10 code (a US
  government work). <a href="https://www.census.gov/data/developers/data-sets/international-trade.html">census.gov</a>.</li>
  </ol>
  <p class="howto-src"><b>Filing and code.</b> The design was committed before any trade value was
  pulled, and every change after it is logged with its date:
  <a href="@@REPO@@export-controls/PREREGISTRATION.md">export-controls/PREREGISTRATION.md</a>, and the
  follow-up on origins, <a href="@@REPO@@export-controls/AMENDMENT_A.md">Amendment A</a>.
  Built by <code>build_export_controls.py</code> from <code>out/export_controls.json</code>, written by
  <code>export-controls/analysis.py</code>.</p>
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

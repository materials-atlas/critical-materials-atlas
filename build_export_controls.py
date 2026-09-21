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
    tok = {
        'CSS': CSS, 'NAV': NAV, 'FOOT': FOOT, 'REPO': REPO,
        'FIG_SB': month_chart(sb, 'EU imports of antimony from China, tonnes a month'),
        'FIG_BI': month_chart(bi, 'EU imports of bismuth from China, tonnes a month'),
        'FOREST': forest(forest_rows, 'China-origin imports against the comparison, by control'),
        'PRICE': price_chart(price_rows, 'Unit value after the control, as a multiple of before'),
        'ESTROWS': ''.join(rows_est), 'LVROWS': ''.join(rows_lv),
        'NUNT': {5: 'Five', 4: 'Four', 6: 'All six', 3: 'Three'}.get(n_untest, str(n_untest)),
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
  arrive in total? <b>As filed, none of the six is shown to bite</b>: the monthly series are too thin
  for the test to have reliably seen the 30% fall it asked for. Two did not need a test to be seen.
  <b>EU imports of antimony from China fell from @@SB_PRE@@ to @@SB_POST@@ tonnes a month and its
  price rose @@SB_M@@-fold; bismuth from China fell by @@BI_FALL@@% and its price rose @@BI_M@@-fold.</b>
  Reading those as a bite came from a rule corrected after the data, so it is exploratory.</p>
</div></section>

<section class="wrap xp">
  <div class="small2">
  <figure class="fig">@@FIG_SB@@<figcaption><b>Antimony from China, tonnes a month.</b> EU imports from
  outside the EU. Red line: the control took effect (15 Sep 2024)@@C_M33@@; dashed: the mean before it
  was announced; shaded: months 7&ndash;12, the period the test reads.</figcaption></figure>
  <figure class="fig">@@FIG_BI@@<figcaption><b>Bismuth from China, tonnes a month.</b> The control took
  effect on announcement (4 Feb 2025)@@C_M10@@; same marks.</figcaption></figure>
  </div>
  @@SRC@@

  <h2>1. The six controls</h2>
  <p>Each was checked against the announcement itself, in the Chinese original. The October 2025
  expansions were suspended within a month and are not tested; nor is anything announced since.</p>
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
  <p><span class="verdict">NONE SHOWN TO BITE</span></p>
  <p>Each controlled good was set against a comparison good that China also dominates but did not
  control &mdash; unwrought magnesium for the metals, talc and baryte for graphite, ferrite magnets for
  rare-earth magnets, lanthanum and cerium compounds for the heavy rare earths &mdash; and the monthly
  gap between the two was compared before and after, with an anticipation window between announcement
  and entry into force, errors robust to autocorrelation@@C_NW1987@@, and a correction for testing six
  controls at once (Holm&rsquo;s). The filing read months 7&ndash;12 after entry into force. A control
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
  inverse hyperbolic sine of tonnes, not a percentage (see below).</figcaption></figure>
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
  made after the estimates were seen, and it is reported beside the filed reading, not in place of it.</p>

  <h2>3. What the series show</h2>
  <p>Leave the comparison aside and look at the tonnes and the prices themselves: the mean month in the
  two years before each announcement against the mean month in months 7&ndash;12 after the control.</p>
  <div class="tbl"><table><thead><tr><th>Control</th><th class="n">from China, t a month</th>
  <th class="n">all origins, t a month</th><th class="n">unit value, &euro;/kg</th>
  <th class="n">price multiple</th><th class="n">comparison's price multiple</th></tr></thead>
  <tbody>@@LVROWS@@</tbody></table></div>
  @@SRC@@
  <figure class="fig">@@PRICE@@
  <figcaption><b>Prices after the controls, as a multiple of before.</b> Unit value of all EU imports of
  each controlled good, and of its comparison, months 7&ndash;12 against the pre-period. Log scale.
  Antimony, bismuth and the heavy rare earths more than doubled; the comparisons barely moved or fell.</figcaption></figure>
  @@SRC@@

  <h3>Antimony: China's supply went, Europe's did not</h3>
  <p><span class="verdict x">EXPLORATORY</span></p>
  <p>EU imports of antimony from China fell from @@SB_PRE@@ tonnes a month to @@SB_POST@@ &mdash; they
  all but stopped &mdash; while antimony from all origins went from @@SB_TPRE@@ to @@SB_TPOST@@ tonnes a
  month: other suppliers replaced China. What changed was the price. The unit value of EU antimony
  imports rose from &euro;@@SB_UV0@@ to &euro;@@SB_UV1@@ a kilogram, @@SB_M@@-fold. The estimate against
  magnesium (&times;@@SB_REL@@) is larger because magnesium itself got cheaper over the same months
  (&times;@@MG_SB@@). So if the control bit in Europe, it bit on price, not on quantity.</p>
  <h3>Bismuth: less from China, less in total, dearer</h3>
  <p><span class="verdict x">EXPLORATORY</span></p>
  <p>Bismuth from China fell from @@BI_PRE@@ to @@BI_POST@@ tonnes a month, and in total from
  @@BI_TPRE@@ to @@BI_TPOST@@: here other origins did not fill the gap. The unit value rose @@BI_M@@-fold
  (&times;@@BI_REL@@ against magnesium). Of the six, bismuth is the one where the tonnes, the total and
  the price all moved the way a bite would move them.</p>
  <h3>The rest</h3>
  <p><b>Gallium and germanium</b> are too thin to test: a few tonnes a month, with the unit value up
  @@GA_M@@-fold (@@GA_REL@@% against magnesium, about half of which is magnesium getting cheaper).
  <b>Natural graphite</b> from China did not fall; the synthetic and spherical graphite the control also
  covers is not in the customs lines the filing locked, so this says nothing about them. <b>Rare-earth
  magnet</b> imports from China rose relative to ferrite magnets, which rules out a 30% fall against
  ferrite, not any effect. <b>The heavy rare earths</b> &mdash; gadolinium, terbium, dysprosium metals
  and compounds &mdash; halved in total and their unit value rose @@HR_M@@-fold, but the China-origin
  series is too small to say whose supply moved.</p>

  <h2>4. The United States: no answer</h2>
  <p>The same test was filed for US imports, and it does not work. US imports of magnesium from China
  fell by about 90% over the window, so any good compared with it looks as if its China imports rose; US
  talc changed how it is recorded in 2023; and US ferrite magnets are counted in pieces, not kilograms.
  Each of these was found in the data after the first run and is logged in the filing. No replacement
  comparisons were chosen after seeing the data, so the US half has no reading, including the outright
  ban on gallium, germanium and antimony to the United States (C3)@@C_M46@@.</p>
  <p class="src"><b>Source:</b> <a href="@@REPO@@export-controls/PREREGISTRATION.md">filing,
  deviations 3 and 7</a>; <a href="https://www.census.gov/data/developers/data-sets/international-trade.html">US
  Census Bureau, international trade API (HS10)</a>.</p>
</section>

<section class="wrap xp">
  <h2>What this can and cannot say</h2>
  <p>It is the EU's import record, to @@LAST@@, against coarse comparison goods, not a causal estimate.
  Magnesium is bought almost entirely from China, and its EU price tripled in 2021&ndash;2022 before
  falling back, inside the years the test uses as &ldquo;before&rdquo;; every price estimate against it
  carries that slide, which is why the raw multiples are shown beside it. Customs value is not a
  contract price, and a unit value of a small-volume good can move with the mix of what was shipped.
  Material shipped ahead of a control shows up as anticipation, licences granted are not observed, and
  routing through a third country is inferred from the pattern, not seen.</p>
  <p>What it does say: in Europe's own customs record, China's controls on antimony and bismuth are
  visible to the naked eye &mdash; in the tonnes that stopped coming from China and in the price paid
  for what came instead &mdash; while the filed test, built to guard against reading noise as effects,
  could not certify either. The two readings are both reported because a pre-registered test that
  cannot see what the raw series show is a finding about the test as much as about the controls.</p>

  <h3>References</h3>
  <ol class="refs">@@REFLIST@@</ol>

  <h3>Data</h3>
  <ol class="refs">
  <li><b>EU imports.</b> Eurostat Comext, monthly detailed trade by CN8 code, imports of the EU27 from
  outside the EU, the United Kingdom excluded throughout; January 2021 to @@LAST@@. Reused under the
  Commission&rsquo;s reuse policy (CC BY 4.0). <a href="https://ec.europa.eu/eurostat/api/dissemination/files?dir=comext%2FCOMEXT_DATA%2FPRODUCTS">Bulk download</a>.</li>
  <li><b>US imports.</b> US Census Bureau international trade API, general imports by HS10 code (a US
  government work). <a href="https://www.census.gov/data/developers/data-sets/international-trade.html">census.gov</a>.</li>
  </ol>
  <p class="howto-src"><b>Filing and code.</b> The design was committed before any trade value was
  pulled, and every change after it is logged with its date:
  <a href="@@REPO@@export-controls/PREREGISTRATION.md">export-controls/PREREGISTRATION.md</a>.
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

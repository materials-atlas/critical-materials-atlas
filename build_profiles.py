#!/usr/bin/env python3
"""
Generate one static profile page per critical material from the committed public data
(out/data.json + out/flows_<year>.json). Every number on every page is computed from those files —
no hand-entered figures, no model-written prose — so the pages regenerate exactly when the data updates.

Output: profile-<label>.html (x32) + profiles.html (the index). Styling via assets/site.css.
Run:  python build_profiles.py        (reads ./out, writes ./)
"""
import json, os, html, glob

ROOT = os.path.dirname(os.path.abspath(__file__))
YEAR = os.environ.get('PROFILE_YEAR', '2024')
SHARED_HS6 = {'gallium', 'germanium', 'hafnium'}

data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
flows = json.load(open(os.path.join(ROOT, 'out', f'flows_{YEAR}.json'), encoding='utf8'))
NAMES = flows.get('names', {})
MATS = data['materials']
STAMP = data.get('dataUpdated', '')

# all MEASURED years (skip provisional/nowcast) for the time-series sparklines
FLOW_BY_YEAR = {}
for _p in glob.glob(os.path.join(ROOT, 'out', 'flows_20*.json')):
    _y = int(os.path.basename(_p)[6:10])
    _d = json.load(open(_p, encoding='utf8'))
    if not (_d.get('provisional') or _d.get('nowcast_kind')):
        FLOW_BY_YEAR[_y] = _d
MEAS_YEARS = sorted(FLOW_BY_YEAR)

try:   # supply-risk scores (build_risk.py must run first)
    RISK = {r['label']: r for r in json.load(open(os.path.join(ROOT, 'out', 'risk.json'), encoding='utf8'))['materials']}
except Exception:
    RISK = {}

def shareOfIn(d, label, key, iso):
    a = (d.get('materials', {}).get(label)) or []
    o = tot = 0.0
    for f in a:
        if f[key] == iso:
            o += f['value']
        tot += f['value']
    return (o / tot * 100) if tot else None

def sparkline(vals, w=160, h=34, pad=3):
    vs = [v for v in vals if v is not None]
    if len(vs) < 3:
        return ''
    mx = max(vs + [1]) * 1.18
    n = len(vals)
    pts = []
    for i, v in enumerate(vals):
        if v is None:
            continue
        x = pad + (w - 2 * pad) * i / (n - 1)
        y = h - pad - (h - 2 * pad) * (v / mx)
        pts.append((x, y))
    line = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    area = f'M{pts[0][0]:.1f},{h-pad} L' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts) + f' L{pts[-1][0]:.1f},{h-pad} Z'
    ex, ey = pts[-1]
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="vertical-align:middle;margin-left:.5rem" aria-hidden="true">'
            f'<path d="{area}" fill="#0e7c74" fill-opacity=".12"/>'
            f'<polyline points="{line}" fill="none" stroke="#0e7c74" stroke-width="1.7"/>'
            f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="2.5" fill="#0e7c74"/></svg>')

def cname(iso):
    return NAMES.get(iso) or iso or '—'

def flag(iso):
    if not iso or len(iso) != 2 or not iso.isalpha():
        return ''
    return ''.join(chr(0x1F1E6 + ord(c.upper()) - 65) for c in iso)

def fmtV(v):
    v = float(v or 0)
    if v >= 1e9: return f'${v/1e9:.1f}B'
    if v >= 1e6: return f'${v/1e6:.0f}M'
    return f'${max(1, round(v/1e3))}k'

def e(s):
    return html.escape(str(s), quote=True)

def strip(t):
    return str(t).split(' (')[0]   # drop the "(HS code)" suffix

def side(label, key):
    a = (flows.get('materials', {}).get(label)) or []
    o, tot = {}, 0.0
    for fl in a:
        o[fl[key]] = o.get(fl[key], 0.0) + fl['value']
        tot += fl['value']
    if not tot:
        return None, [], 0.0, tot
    ranked = sorted(o.items(), key=lambda kv: kv[1], reverse=True)
    hhi = sum((v / tot) ** 2 for v in o.values())
    return ranked[0], ranked, hhi, tot   # (top (iso,val)), full ranked, hhi, total

def stat(label, m):
    rv = (m.get('reserves') or [None])[0]
    mi = (m.get('mined') or [None])[0]
    re = (m.get('refined') or [None])[0]
    (te, ev), exp_ranked, ehhi, etot = side(label, 'from') if side(label, 'from')[0] else (None, [], 0, 0)
    return rv, mi, re

MOTIF = ('<svg class="hero-motif" viewBox="0 0 560 560" fill="none" aria-hidden="true">'
 '<g stroke="#7fd2c8" stroke-opacity=".15" stroke-width="1.1"><circle cx="280" cy="280" r="232"/>'
 '<ellipse cx="280" cy="280" rx="232" ry="62"/><ellipse cx="280" cy="280" rx="232" ry="132"/>'
 '<ellipse cx="280" cy="280" rx="232" ry="196"/><ellipse cx="280" cy="280" rx="62" ry="232"/>'
 '<ellipse cx="280" cy="280" rx="132" ry="232"/><ellipse cx="280" cy="280" rx="196" ry="232"/>'
 '<line x1="280" y1="48" x2="280" y2="512"/><line x1="48" y1="280" x2="512" y2="280"/></g>'
 '<g stroke="#9be3da" stroke-opacity=".26" stroke-width="1.4" fill="none"><path d="M120 360 Q 300 110 472 248"/>'
 '<path d="M158 196 Q 322 300 442 422"/><path d="M120 360 Q 268 430 442 422"/></g>'
 '<g fill="#bff0e8" fill-opacity=".55"><circle cx="120" cy="360" r="4.2"/><circle cx="472" cy="248" r="4.2"/>'
 '<circle cx="158" cy="196" r="4.2"/><circle cx="442" cy="422" r="4.2"/></g></svg>')

def topbar(active=''):
    def a(href, label, cls=''):
        c = 'active' if label.lower() == active else cls
        cattr = (' class="' + c + '"') if c else ''
        return '<a href="' + href + '"' + cattr + '>' + label + '</a>'
    return ('<header class="topbar"><div class="wrap">'
            '<a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>'
            '<nav class="topnav">'
            f'{a("./","Atlas")}{a("methodology.html","Methodology")}{a("findings.html","Findings")}'
            f'{a("profiles.html","Profiles")}{a("technical-note.html","Note","hideable")}'
            '<a href="https://github.com/materials-atlas/comtrade-reconcile" class="hideable">Engine</a>'
            '</nav></div></header>')

FOOTER = ('<footer class="siteftr"><div class="wrap">'
 '<div><h4>Critical Materials Atlas</h4>An independent demonstration from public data: where 32 critical raw '
 'materials are mined, refined, traded and held in reserve — and why import-origin statistics misidentify the '
 'real source. Not affiliated with, nor representing, any institution.</div>'
 '<div><h4>Navigate</h4><a href="./">Interactive atlas</a><br><a href="insights.html">State of supply</a><br>'
 '<a href="profiles.html">Material profiles</a><br><a href="countries.html">By country</a><br>'
 '<a href="findings.html">The origin gap</a><br>'
 '<a href="risk.html">Supply-risk index</a><br><a href="scenarios.html">Supply-shock scenarios</a><br>'
 '<a href="methodology.html">Methodology</a><br><a href="data.html">Data &amp; API</a></div>'
 '<div><h4>Sources</h4>USGS Mineral Commodity Summaries<br>IEA Critical Minerals Outlook<br>'
 'UN Comtrade · CEPII BACI<br>Eurostat Comext · World Bank</div>'
 f'<div class="fineprint">Figures computed from public data (trade year {YEAR}, reconciled CEPII BACI; '
 'mine/refine/reserves USGS &amp; IEA, approximate). An overlay of distinct measures, not one observed pipeline. '
 f'Data updated {e(STAMP)}.</div></div></footer>')

def bars(items, cls, n=12):
    if not items:
        return '<p class="note">not available</p>'
    out = []
    shown = 0.0
    for x in items[:n]:
        c, v = x['c'], x['v']
        if v <= 1:          # only countries ABOVE 1% get their own row; smaller ones fold into "Rest of world"
            continue
        shown += v
        out.append(f'<div class="barrow"><span class="bc">{flag(c)} {e(cname(c))}</span>'
                   f'<span class="bw"><span class="bf {cls}" style="width:{max(2,min(100,v)):.0f}%"></span></span>'
                   f'<span class="bv">{v:.0f}%</span></div>')
    rest = round(100 - shown)   # everything not shown — so it reads to 100
    if rest >= 1:
        # our source data lists only the TOP FEW countries, so the remainder is NOT verified to be all small.
        # Say so honestly ("not detailed") rather than "Rest of world", which would imply we know it's all tiny.
        rlabel = '🌍 Others (not detailed)'
        out.append(f'<div class="barrow"><span class="bc" style="color:var(--faint)">{rlabel}</span>'
                   f'<span class="bw"><span class="bf" style="width:{max(2,min(100,rest)):.0f}%;background:#39414b"></span></span>'
                   f'<span class="bv" style="color:var(--faint)">{rest:.0f}%</span></div>')
    return ''.join(out)

def qty_by(label, key):
    """Per country: (tonnes, value ON THOSE SAME edges) — so $/t is a price of the tonnage we actually have,
    not total-value / partial-tonnes. Quantity is 'where BACI reports it' (sparse for high-value metals)."""
    o = {}
    for fl in (flows.get('materials', {}).get(label) or []):
        if fl.get('qty'):
            t, v = o.get(fl[key], (0.0, 0.0))
            o[fl[key]] = (t + fl['qty'], v + fl['value'])
    return o

def fmtT(t):
    if not t:
        return '—'
    if t >= 1e6:
        return f'{t/1e6:.2f} Mt'
    if t >= 1e3:
        return f'{t/1e3:.1f} kt'
    return f'{t:.0f} t'

def fmtUPT(x):
    """$/tonne, compact: $31.7M/t for precious metals, $9,000/t for base, $100/t for bulk."""
    if x >= 1e6:
        return f'${x/1e6:.1f}M/t'
    return f'${x:,.0f}/t'

def trade_table(ranked, tot, kind, qmap):
    rows = []
    for iso, val in ranked[:6]:
        t, vq = qmap.get(iso, (0.0, 0.0))
        upt = fmtUPT(vq / t) if t else '—'
        rows.append(f'<tr><td>{flag(iso)} {e(cname(iso))}</td><td class="n">{val/tot*100:.0f}%</td>'
                    f'<td class="n">{fmtV(val)}</td><td class="n">{fmtT(t)}</td><td class="n">{upt}</td></tr>')
    return (f'<table><caption>Top {kind} — reconciled trade, {YEAR}</caption>'
            f'<thead><tr><th>Country</th><th class="n">share</th><th class="n">value</th>'
            f'<th class="n">tonnes</th><th class="n">$/t</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>')

def origin_gap(m, label):
    top = side(label, 'from')[0]
    if not top:
        return None
    te = top[0]
    te_share = top[1] / side(label, 'from')[3] * 100
    mined = {x['c']: x['v'] for x in (m.get('mined') or [])}
    return te, te_share, te_share - mined.get(te, 0.0), mined

def page(m):
    label = m['label']
    title = m['title'].split(' (')[0]
    code = (m['title'].split('(')[-1].rstrip(')')) if '(' in m['title'] else ''
    shared = label in SHARED_HS6
    rv = (m.get('reserves') or [None])[0]
    mi = (m.get('mined') or [None])[0]
    re = (m.get('refined') or [None])[0]
    (texp, texp_ranked, ehhi, etot) = (side(label, 'from')[0], side(label, 'from')[1], side(label, 'from')[2], side(label, 'from')[3])
    (timp, timp_ranked, ihhi, itot) = (side(label, 'to')[0], side(label, 'to')[1], side(label, 'to')[2], side(label, 'to')[3])
    og = origin_gap(m, label)

    # data-derived hook (the deck) — gated FIRST on whether the top exporter is also the top miner,
    # then on its own mine share, so we never claim "leads both" for a country that isn't the lead miner.
    if og:
        te, tes, gap, mined = og
        te_mine = mined.get(te, 0.0)
        tm = mi['c'] if mi else None
        if tm and te == tm:                       # exporter IS the lead miner — genuine concentration
            deck = f'{e(cname(te))} leads both the mining and the export of {e(title.lower())} — a genuine, not an accounting, concentration.'
        elif tm and te_mine < 8:                   # refiner/hub: exports a lot, mines ~none
            deck = (f'Exported mainly by {e(cname(te))} ({tes:.0f}% of world trade), which mines almost none of it — '
                    f'the source is {e(cname(tm))} ({mi["v"]:.0f}% of mine output). The origin gap: +{gap:.0f} points.')
        elif tm:                                   # exporter is a real producer, just not the largest miner
            deck = (f'{e(cname(te))} leads exports of {e(title.lower())} ({tes:.0f}% of trade) and is itself a major miner '
                    f'({te_mine:.0f}% of output); the largest miner, {e(cname(tm))} ({mi["v"]:.0f}%), exports far less.')
        else:
            deck = f'Exported mainly by {e(cname(te))} ({tes:.0f}% of world trade).'
    else:
        deck = f'Where {e(title.lower())} is mined, refined, and traded — from public data.'

    # at-a-glance stats
    stats = []
    if RISK.get(label): stats.append((f'{RISK[label]["score"]}<span style="color:var(--faint);font-weight:600">/100</span>', 'supply-risk index'))
    if m.get('reserve_life'): stats.append((f'{m["reserve_life"]}<span style="color:var(--faint);font-weight:600"> yr</span>', 'reserve life (reserves ÷ mining)'))
    if m.get('export_control'): stats.append(('<span style="color:#e0703c">⚠ controlled</span>', e(m['export_control'])))
    if m.get('net_import_reliance'): stats.append((e(m['net_import_reliance']), 'US import reliance'))
    if rv: stats.append((f'{flag(rv["c"])} {cname(rv["c"])}', f'lead reserves · {rv["v"]:.0f}%'))
    if mi: stats.append((f'{flag(mi["c"])} {cname(mi["c"])}', f'lead miner · {mi["v"]:.0f}%'))
    if re: stats.append((f'{flag(re["c"])} {cname(re["c"])}', f'lead refiner · {re["v"]:.0f}%'))
    if texp: stats.append((f'{flag(texp[0])} {cname(texp[0])}', f'top exporter · {texp[1]/etot*100:.0f}%'))
    if texp: stats.append((f'{ehhi:.2f}', 'export concentration (HHI)'))
    stat_html = ''.join(f'<div class="stat"><div class="n">{s[0]}</div><div class="l">{e(s[1])}</div></div>' for s in stats)

    gap_callout = ''
    if og and mi and og[0] != mi['c'] and og[2] > 8:
        te, tes, gap, mined = og
        te_mine = mined.get(te, 0.0)
        if te_mine < 8:
            gap_callout = (f'<div class="callout hot"><b>The origin gap.</b> {e(title)} is exported mainly by '
                f'<b>{flag(te)} {e(cname(te))}</b> ({tes:.0f}% of world trade) but mined mainly in '
                f'<b>{flag(mi["c"])} {e(cname(mi["c"]))}</b> ({mi["v"]:.0f}%), while {e(cname(te))} mines almost none of it. '
                f'Taken at face value, import-origin statistics point to {e(cname(te))} as the source; one layer upstream, '
                f'the real dependence is on {e(cname(mi["c"]))}. Gap: <b>+{gap:.0f} points</b>.</div>')
        else:
            gap_callout = (f'<div class="callout"><b>Exporter ≠ largest miner.</b> {e(title)} is exported mainly by '
                f'<b>{flag(te)} {e(cname(te))}</b> ({tes:.0f}% of trade), which is itself a major miner ({te_mine:.0f}% of output). '
                f'The largest miner, <b>{flag(mi["c"])} {e(cname(mi["c"]))}</b> ({mi["v"]:.0f}%), exports far less — so the trade '
                f'ledger still overstates {e(cname(te))}\'s share of the underlying <i>source</i>. Gap: <b>+{gap:.0f} points</b>.</div>')

    trend_block = ''
    te_t = og[0] if og else None
    if te_t and len(MEAS_YEARS) >= 3:
        series = [shareOfIn(FLOW_BY_YEAR[y], label, 'from', te_t) for y in MEAS_YEARS]
        if all(v is not None for v in series):
            arrow = '↑' if series[-1] - series[0] > 2 else '↓' if series[0] - series[-1] > 2 else '→'
            trend_block = (f'<div class="callout"><b>{e(cname(te_t))}</b>’s share of world {e(title.lower())} exports, '
                f'{MEAS_YEARS[0]}–{MEAS_YEARS[-1]}: <b>{series[0]:.0f}% {arrow} {series[-1]:.0f}%</b>{sparkline(series)}</div>')

    shared_note = ('<p class="note">⛓ Gallium, germanium and hafnium share one HS6 code (811292); their trade columns '
                   'are identical and cannot be separated. The mine/refine/reserve layers still differ.</p>') if shared else ''

    note = e(m.get('note') or '').strip()
    note_block = f'<h2>Context</h2><p>{note}</p>' if note else ''

    trade_block = ''
    if texp:
        trade_block += trade_table(texp_ranked, etot, 'exporters', qty_by(label, 'from'))
    if timp:
        trade_block += trade_table(timp_ranked, itot, 'importers', qty_by(label, 'to'))

    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} — Critical Materials Atlas</title>
<meta name="description" content="{e(title)}: where it is mined, refined, traded and held in reserve. {e(deck)}">
<meta property="og:title" content="{e(title)} — where it really comes from">
<meta property="og:description" content="{e(deck)}">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
</head><body>
{topbar()}
<section class="hero">{MOTIF}<div class="wrap">
  <div class="eyebrow">Critical material · profile{(' · ' + e(code)) if code else ''}</div>
  <h1>{e(title)}</h1>
  <p class="deck">{deck}</p>
  <p class="byline">Trade year {YEAR} · reconciled CEPII BACI · mine/refine/reserves USGS &amp; IEA (approx.)</p>
</div></section>
<section class="stats"><div class="wrap">{stat_html}</div></section>
<article>
  {('<p style="font-size:.96rem;color:var(--ink-soft)"><b>Primary uses.</b> ' + e(m.get("uses")) + '.</p>') if m.get('uses') else ''}
  {gap_callout}
  {trend_block}
  <h2>The five layers</h2>
  <h3>● Reserves — where it could come from (USGS, economically recoverable)</h3>{bars(m.get('reserves'), 'res')}
  <h3>● Mined — where it is produced today (USGS)</h3>{bars(m.get('mined'), 'ore')}
  <h3>● Refined / processed (IEA)</h3>{bars(m.get('refined'), 'ref')}
  <h3>● Recycling &amp; substitutability — the mitigants (EU CRM)</h3>
  <p>{(f'<b>{m.get("recycling")}%</b> of supply comes from recycling end-of-life products' + (' — a meaningful secondary source that lowers the supply-risk score.' if (m.get("recycling") or 0) >= 15 else ('.' if (m.get("recycling") or 0) > 0 else ' — there is essentially no end-of-life recycling, so a disruption has no secondary cushion.'))) if m.get('recycling') is not None else 'No reliable recycling figure.'} {('Substitutability is <b>' + str(m.get('substitutability')) + '</b>' + (' — few or no alternatives, so a disruption bites hard.' if m.get('substitutability')=='high' else (' — good alternatives exist.' if m.get('substitutability')=='low' else ' — partial substitutes exist.')) ) if m.get('substitutability') else ''}</p>
  <h2>Who trades it ({YEAR})</h2>
  {trade_block}
  {shared_note}
  {note_block}
  <div class="btnrow">
    <a class="btn primary" href="./#view=map&amp;mat={e(label)}">Explore {e(title.split(",")[0].lower())} in the atlas →</a>
    <a class="btn ghost" href="findings.html">The origin gap</a>
    <a class="btn ghost" href="methodology.html">Methodology</a>
  </div>
  <p class="note">Every figure on this page is computed from <a href="out/data.json">out/data.json</a> and
  <a href="out/flows_{YEAR}.json">out/flows_{YEAR}.json</a> by <a href="https://github.com/materials-atlas/critical-materials-atlas/blob/main/build_profiles.py">build_profiles.py</a> — no hand-entered numbers.</p>
</article>
{FOOTER}
</body></html>'''

def index_page():
    cards = []
    rows = []
    for m in MATS:
        label = m['label']
        og = origin_gap(m, label)
        mi = (m.get('mined') or [None])[0]
        gaptxt = ''
        gv = -1
        if og and mi and og[0] != mi['c']:
            te, tes, gap, mined = og
            gv = gap
            gaptxt = f'exporter {flag(te)} {cname(te)} · miner {flag(mi["c"])} {cname(mi["c"])} · gap <b>+{gap:.0f}pp</b>'
        elif og:
            gaptxt = f'top exporter {flag(og[0])} {cname(og[0])} ({og[1]:.0f}%)'
        rows.append((gv, m['title'].split(' (')[0], label, gaptxt))
    rows.sort(key=lambda r: r[0], reverse=True)
    for gv, title, label, gaptxt in rows:
        cards.append(f'<a class="card" href="profile-{e(label)}.html"><div class="ct">{e(title)}</div>'
                     f'<div class="cg">{gaptxt}</div></a>')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Material profiles — Critical Materials Atlas</title>
<meta name="description" content="A profile for each of 32 critical raw materials: mined, refined, traded, reserves, and the origin gap.">
<meta property="og:title" content="Critical material profiles — where each really comes from">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
</head><body>
{topbar('profiles')}
<section class="hero">{MOTIF}<div class="wrap">
  <div class="eyebrow">Reference · {len(MATS)} critical materials</div>
  <h1>Material profiles</h1>
  <p class="deck">One page per material — where it is mined, refined, traded and held in reserve, and how far its trade origin sits from its mine. Sorted by origin gap.</p>
</div></section>
<article style="max-width:1100px">
  <p style="color:#667179"><a href="countries.html">Browse by country →</a></p>
  <div class="cards">{''.join(cards)}</div>
</article>
{FOOTER}
</body></html>'''

HUBS = {'HK', 'SG', 'AE', 'PA', 'MO', 'GI'}   # re-export entrepots — exclude (import = trans-shipment)

def country_imports(iso):
    rows = []
    for m in MATS:
        a = (flows.get('materials', {}).get(m['label'])) or []
        o, tot = {}, 0.0
        for fl in a:
            if fl['to'] == iso and fl['from'] != iso:
                o[fl['from']] = o.get(fl['from'], 0.0) + fl['value']
                tot += fl['value']
        if not tot:
            continue
        top = max(o, key=o.get)
        ml = (m.get('mined') or [None])[0]
        rows.append({'m': m, 'top': top, 'topshare': o[top] / tot * 100,
                     'hhi': sum((v / tot) ** 2 for v in o.values()),
                     'cn': o.get('CN', 0.0) / tot * 100, 'n': len(o), 'tot': tot, 'ml': ml,
                     'risk': RISK.get(m['label'], {}).get('score', 0)})
    rows.sort(key=lambda r: r['topshare'], reverse=True)
    return rows

def country_vuln(rows):
    # value-weighted average of (material supply-risk x this country's single-supplier reliance), 0-100
    den = sum(r['tot'] for r in rows)
    if not den:
        return 0
    return round(sum(r['tot'] * (r['risk'] / 100) * (r['topshare'] / 100) for r in rows) / den * 100)

def country_china_series(iso):
    out = []
    for y in MEAS_YEARS:
        d = FLOW_BY_YEAR[y]
        cn = tot = 0.0
        for m in MATS:
            for f in (d.get('materials', {}).get(m['label']) or []):
                if f['to'] == iso and f['from'] != iso:
                    tot += f['value']
                    if f['from'] == 'CN':
                        cn += f['value']
        out.append(cn / tot * 100 if tot else None)
    return out

def country_page(iso, rows):
    name = cname(iso)
    total = sum(r['tot'] for r in rows)
    china_dom = sum(1 for r in rows if r['top'] == 'CN' or r['cn'] > 45)
    gap_exposed = sum(1 for r in rows if r['ml'] and r['top'] != r['ml']['c'])
    mean_hhi = sum(r['hhi'] for r in rows) / len(rows) if rows else 0
    worst = rows[0] if rows else None
    deck = (f'{e(name)} imports {len(rows)} of the {len(MATS)} critical materials this atlas tracks '
            f'({fmtV(total)}). Its most supplier-concentrated dependence is {e(strip(worst["m"]["title"]).lower())} '
            f'({worst["topshare"]:.0f}% from {e(cname(worst["top"]))})' if worst else f'{e(name)} import profile')
    if china_dom:
        deck += f'; {china_dom} of those imports come mainly from China.'
    vuln = country_vuln(rows)
    stats = [
        (f'{vuln}/100', 'import-vulnerability index'),
        (str(len(rows)), 'critical materials imported'),
        (fmtV(total), f'total imports ({YEAR})'),
        (f'{china_dom}', 'mainly-from-China dependencies'),
        (f'{gap_exposed}', 'supplier ≠ the lead miner'),
    ]
    stat_html = ''.join(f'<div class="stat"><div class="n">{e(s[0])}</div><div class="l">{e(s[1])}</div></div>' for s in stats)
    body = []
    for r in rows:
        m = r['m']; ismine = r['ml'] and r['top'] == r['ml']['c']
        hcol = '#c0392b' if r['hhi'] > 0.45 else '#b35e16' if r['hhi'] > 0.25 else '#3f9b46'
        body.append(
            f'<tr><td><a href="profile-{e(m["label"])}.html">{e(strip(m["title"]))}</a></td>'
            f'<td>{flag(r["top"])} {e(cname(r["top"]))}'
            + (' <span title="this source is also the lead miner — a genuine origin" style="color:#3f9b46">⛏</span>' if ismine else '')
            + f'</td><td class="n">{r["topshare"]:.0f}%</td>'
            f'<td class="n" style="color:{hcol};font-weight:600">{r["hhi"]:.2f}</td>'
            + f'<td class="n" style="color:{"#c0392b" if r["risk"]>=60 else "#b35e16" if r["risk"]>=40 else "#888"};font-weight:600">{r["risk"]}</td>'
            + f'<td class="n">{r["cn"]:.0f}%</td><td class="n">{r["n"]}</td>'
            f'<td class="n">{fmtV(r["tot"])}</td></tr>')
    ctrend = ''
    if len(MEAS_YEARS) >= 3:
        cs = country_china_series(iso)
        if all(v is not None for v in cs):
            arrow = '↑' if cs[-1] - cs[0] > 2 else '↓' if cs[0] - cs[-1] > 2 else '→'
            ctrend = (f'<div class="callout"><b>China</b>’s share of {e(name)}’s critical-material imports, '
                f'{MEAS_YEARS[0]}–{MEAS_YEARS[-1]}: <b>{cs[0]:.0f}% {arrow} {cs[-1]:.0f}%</b>{sparkline(cs)}</div>')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(name)} — critical-material dependency · Critical Materials Atlas</title>
<meta name="description" content="{e(name)}'s import dependency across {len(rows)} critical raw materials: top source, concentration, China exposure, and where the supplier is not the mine.">
<meta property="og:title" content="{e(name)} — critical-material dependency">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
</head><body>
{topbar()}
<section class="hero">{MOTIF}<div class="wrap">
  <div class="eyebrow">Country profile · import dependency</div>
  <h1>{e(name)} — critical-material dependency</h1>
  <p class="deck">{deck}</p>
  <p class="byline">Reconciled bilateral trade, {YEAR} (CEPII BACI) · mine layer USGS (approx.)</p>
</div></section>
<section class="stats"><div class="wrap">{stat_html}</div></section>
<article style="max-width:960px">
  <div class="callout"><b>How to read this.</b> Each row is where {e(name)} <i>imports</i> a material from — the
  immediate customs origin, sorted by single-supplier concentration. <b>⛏</b> marks a top source that is also
  the material's lead miner (a genuine origin); without it, the supplier is a refiner or hub and the real
  mine sits further upstream (open the material's profile to see where).</p></div>
  <div class="callout"><b>Import-vulnerability index ({vuln}/100).</b> A value-weighted average, across {e(name)}’s
  imports, of each material’s <a href="risk.html">supply-risk index</a> &times; how concentrated {e(name)}’s
  own sourcing of it is. High when it buys intrinsically risky materials from a single supplier; lower when
  it diversifies. The <b>risk</b> column below is the material’s own score — multiply it by the country’s
  share to see where {e(name)} is most exposed.</div>
  {ctrend}
  <table>
    <caption>{e(name)} — import sources by material ({YEAR})</caption>
    <thead><tr><th>Material</th><th>Top source</th><th class="n">share</th><th class="n" title="Herfindahl of import sources">import HHI</th><th class="n" title="the material's supply-risk index (0-100)">risk</th><th class="n">China</th><th class="n"># sources</th><th class="n">imports</th></tr></thead>
    <tbody>{''.join(body)}</tbody>
  </table>
  <div class="btnrow">
    <a class="btn primary" href="./#view=map&amp;dest={e(iso)}">See {e(name)}'s trade on the map →</a>
    <a class="btn ghost" href="countries.html">All countries</a>
    <a class="btn ghost" href="findings.html">The origin gap</a>
  </div>
  <p class="note">Computed from <a href="out/flows_{YEAR}.json">out/flows_{YEAR}.json</a> + <a href="out/data.json">out/data.json</a> by build_profiles.py. Customs records the immediate shipper, not the mine — see <a href="methodology.html">methodology</a>.</p>
</article>
{FOOTER}
</body></html>'''

def countries_index(items):
    items.sort(key=lambda t: t[3], reverse=True)   # by import-vulnerability index
    cards = []
    for iso, rows, total, score in items:
        cd = sum(1 for r in rows if r['top'] == 'CN' or r['cn'] > 45)
        scol = '#c0392b' if score >= 35 else '#b35e16' if score >= 25 else '#3f9b46'
        cards.append(f'<a class="card" href="profile-country-{e(iso)}.html"><div class="ct">{flag(iso)} {e(cname(iso))} '
                     f'<span style="float:right;color:{scol};font-weight:800">{score}</span></div>'
                     f'<div class="cg">vulnerability {score}/100 · {len(rows)} materials · {fmtV(total)}' + (f' · <b>China-led {cd}</b>' if cd else '') + '</div></a>')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Country dependency profiles — Critical Materials Atlas</title>
<meta name="description" content="Critical-material import-dependency profiles for the major importing economies.">
<meta property="og:title" content="Critical-material dependency by country">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
</head><body>
{topbar()}
<section class="hero">{MOTIF}<div class="wrap">
  <div class="eyebrow">Reference · by country</div>
  <h1>Dependency by country</h1>
  <p class="deck">Where each major economy sources its critical materials — and how exposed it is. The <b>import-vulnerability index</b> (0–100) value-weights each material’s supply-risk by how concentrated the country’s sourcing of it is. Ranked most-exposed first.</p>
</div></section>
<article style="max-width:1100px">
  <p style="color:#667179"><a href="profiles.html">← Browse by material instead</a></p>
  <p class="note">The index measures the <i>vulnerability of a country's sourcing</i> — risky materials bought from few suppliers — not its economic size or systemic importance. A small economy buying from single suppliers can therefore rank above a large, diversified one.</p>
  <div class="cards">{''.join(cards)}</div>
</article>
{FOOTER}
</body></html>'''

def main():
    n = 0
    for m in MATS:
        open(os.path.join(ROOT, f'profile-{m["label"]}.html'), 'w', encoding='utf8', newline='\n').write(page(m))
        n += 1
    open(os.path.join(ROOT, 'profiles.html'), 'w', encoding='utf8', newline='\n').write(index_page())
    # country pages — real consuming economies only (>= $1B imports, excluding re-export hubs)
    isos = set()
    for mm in MATS:
        for fl in (flows.get('materials', {}).get(mm['label']) or []):
            isos.add(fl['to'])
    citems = []
    for iso in isos:
        if iso in HUBS:
            continue
        rows = country_imports(iso)
        total = sum(r['tot'] for r in rows)
        if total >= 1e9 and len(rows) >= 8:
            open(os.path.join(ROOT, f'profile-country-{iso}.html'), 'w', encoding='utf8', newline='\n').write(country_page(iso, rows))
            citems.append((iso, rows, total, country_vuln(rows)))
    open(os.path.join(ROOT, 'countries.html'), 'w', encoding='utf8', newline='\n').write(countries_index(citems))
    json.dump(sorted(t[0] for t in citems),
              open(os.path.join(ROOT, 'out', 'country_pages.json'), 'w', encoding='utf8'))   # manifest for the atlas
    print(f'wrote {n} material profiles + profiles.html + {len(citems)} country profiles + countries.html  (year {YEAR})')

if __name__ == '__main__':
    main()

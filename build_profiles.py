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
SHARED_HS6 = {'gallium', 'germanium'}

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

# ALL years incl. nowcast/scenario (2025*/2026**) — used by the in-page trade year switcher only
FLOW_ALL = {}
for _p in glob.glob(os.path.join(ROOT, 'out', 'flows_20*.json')):
    FLOW_ALL[int(os.path.basename(_p)[6:10])] = json.load(open(_p, encoding='utf8'))

# historical USGS series (editions 2020–2024) for the Mined / Reserves layer year sliders; optional
MINED_YEARS = {}
_myp = os.path.join(ROOT, 'out', 'mined_years.json')
if os.path.exists(_myp):
    MINED_YEARS = json.load(open(_myp, encoding='utf8'))
RESERVES_YEARS = {}
_ryp = os.path.join(ROOT, 'out', 'reserves_years.json')
if os.path.exists(_ryp):
    RESERVES_YEARS = json.load(open(_ryp, encoding='utf8'))
REFINED_YEARS = {}
_fyp = os.path.join(ROOT, 'out', 'refined_years.json')
if os.path.exists(_fyp):
    REFINED_YEARS = json.load(open(_fyp, encoding='utf8'))
MINED_SRC = {}  # materials whose mined series is BGS long-run (vs USGS 5-yr) -> source string
_msp = os.path.join(ROOT, 'out', 'mined_years_src.json')
if os.path.exists(_msp):
    MINED_SRC = json.load(open(_msp, encoding='utf8'))

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
            # The SAME six items as the other 192 pages. These 61 carried an older menu
            # (Methodology/Findings/Profiles/Note/Engine) that nothing else on the site
            # used any more. Checked before dropping the Profiles link: explorer.html links
            # to profiles.html and to individual profiles, so the index stays one click away
            # via Explore and nothing becomes unreachable.
            '<nav class="topnav">'
            f'{a("./","Atlas")}{a("explorer","Explore")}{a("value-chains","Value Chains")}'
            f'{a("analysis","Analysis")}{a("reports","Reports")}{a("method","Method")}'
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

def bars(items, cls, n=12, source=None):
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
        n_src = len([x for x in items if x['v'] > 0])
        if source == 'refined' and n_src < 3:
            # IEA only details refining for the 6 energy-transition minerals; for the rest the source
            # reports only the leading refiner, so the remainder is genuinely NOT published — say so.
            rlabel = '🌍 Rest — not separately reported'
        elif source == 'refined':
            # we have a real multi-country breakdown (IEA / copper / bauxite); the remainder is a small tail
            rlabel = '🌍 Other countries'
        else:
            # USGS mine/reserve layers list the top producers; the remainder is not verified to be all small
            rlabel = '🌍 Others (not detailed)'
        out.append(f'<div class="barrow"><span class="bc" style="color:var(--faint)">{rlabel}</span>'
                   f'<span class="bw"><span class="bf" style="width:{max(2,min(100,rest)):.0f}%;background:#39414b"></span></span>'
                   f'<span class="bv" style="color:var(--faint)">{rest:.0f}%</span></div>')
    return ''.join(out)

def _cc(x): return f"{flag(x['c'])} {e(cname(x['c']))}"
def _conc(arr):
    """Herfindahl-based concentration read on a share list."""
    h = sum((x['v'] / 100.0) ** 2 for x in arr)
    return ('broadly diversified' if h < 0.20 else 'moderately concentrated' if h < 0.35
            else 'concentrated' if h < 0.55 else 'highly concentrated')
def _share(arr, code):
    for x in arr:
        if x['c'] == code: return x['v']
    return 0

def layer_para(m, layer, nm):
    """A heavier analytical paragraph per layer — concept + a reading of THIS material's numbers and their
    supply-chain implications. Every figure is computed from data.json (concentration, reserve life,
    cross-stage mismatches, export controls, import reliance, recycling/substitutability); no hand-entered
    per-material prose."""
    Nm = nm[:1].upper() + nm[1:]
    reserves, mined, refined = (m.get('reserves') or []), (m.get('mined') or []), (m.get('refined') or [])
    rl, nir, ec = m.get('reserve_life'), m.get('net_import_reliance'), m.get('export_control')
    rec, sub = m.get('recycling'), m.get('substitutability')
    mined_src = ('BGS World Mineral Statistics · mine production, 2000–2024 (USGS-validated)'
                 if m.get('label') in MINED_SRC else 'USGS 2024 · 2023 production')
    src = {'reserves': 'USGS 2024 · reserves as of 2023',
           'mined': mined_src,
           'refined': (e(m['refined_source']) if m.get('refined_source') else 'leading refiner only — fuller breakdown not publicly reported')}[layer]

    if layer == 'reserves':
        b = ("<b>Reserves</b> are the deposits known to exist and economically worth mining — the long-run ceiling on "
             "supply, distinct from what is actually produced today.")
        if not reserves:
            b += f" USGS does not publish country-level reserves for {nm} — typically because it is a by-product of another ore or is drawn from an effectively unlimited source (e.g. quartz, seawater), so a national reserve map does not apply."
        else:
            b += f" {Nm}'s reserves are {_conc(reserves)}: {_cc(reserves[0])} holds the most ({reserves[0]['v']}%)"
            b += f", ahead of {_cc(reserves[1])} ({reserves[1]['v']}%)" if len(reserves) > 1 else ""
            b += f" and {_cc(reserves[2])} ({reserves[2]['v']}%)." if len(reserves) > 2 else "."
            if rl:
                fr = ('scarcity is not the binding constraint — access, capital and processing capacity are' if rl >= 40
                      else 'the horizon is genuinely finite, so recycling and new discoveries will decide long-run supply' if rl < 25
                      else 'there is only a moderate runway before fresh capacity must come online')
                b += f" At today's extraction rate the known reserves would last roughly {rl} years, so {fr}."
            if mined and reserves[0]['c'] != mined[0]['c']:
                b += (f" Tellingly, the country sitting on the most ore ({_cc(reserves[0])}) is not the one extracting it "
                      f"({_cc(mined[0])}) — geology sets the ceiling, but capacity and policy decide who actually supplies the market.")
    elif layer == 'mined':
        b = ("<b>Mining</b> is where ore leaves the ground — the stage most people equate with &ldquo;the source&rdquo;, "
             "though it is rarely where the supply risk actually concentrates.")
        if not mined:
            b += f" Mine-production shares are not separately reported for {nm}."
        else:
            b += f" Output is {_conc(mined)}: {_cc(mined[0])} supplies {mined[0]['v']}%"
            b += f", with {_cc(mined[1])} ({mined[1]['v']}%) next." if len(mined) > 1 else "."
            if m.get('label') == 'tantalum' and any(x['c'] == 'RW' for x in mined[:3]):
                b += (" Note: much of Rwanda&rsquo;s <i>reported</i> mine output is widely assessed (UN Group of Experts and "
                      "others) as Congolese coltan re-exported across the border, so DRC&rsquo;s true share is higher and part "
                      "of Rwanda&rsquo;s &ldquo;mine production&rdquo; is an origin artefact rather than a measured mine.")
            if mined[0]['v'] >= 50:
                b += " That is effectively a single-country dependence — one government's policy or one region's disruption can move the entire upstream."
            if reserves and mined[0]['c'] != reserves[0]['c']:
                rs = _share(reserves, mined[0]['c'])
                b += (f" It out-produces reserve-richer {_cc(reserves[0])}" + (f" while holding just {rs}% of reserves itself" if rs else "")
                      + " — supply power at this stage is built on installed capacity, not geology.")
            if ec:
                b += f" And the tap is politically live: {e(ec)}."
    else:  # refined
        b = ("<b>Refining / processing</b> converts ore into the metal or compound buyers actually purchase; it concentrates "
             "in fewer hands than mining and sits at the buyer's doorstep, which is why it is usually the true chokepoint.")
        if not refined:
            b += f" A country-level processing breakdown is not publicly reported for {nm} — only the leading refiner is known, which itself signals how opaque this stage is."
        else:
            b += f" {_cc(refined[0])} processes {refined[0]['v']}% — {_conc(refined)}."
            if mined and refined[0]['c'] != mined[0]['c']:
                b += (f" So although {_cc(mined[0])} mines the most, {e(cname(refined[0]['c']))} controls processing: the dependency "
                      "the mine map hides, and the reason import-origin statistics misread the real source.")
            elif mined and refined[0]['c'] == mined[0]['c']:
                b += f" {e(cname(refined[0]['c']))} leads both mining and refining, so its grip is structural rather than a pure processing gate."
            if ec:
                b += f" This leverage is not hypothetical — {e(ec)}."
            if rec is not None or sub or nir:
                subw = 'scarce' if sub == 'high' else 'readily available' if sub == 'low' else 'only partial'
                mit = f" On the buffers: {rec}% of supply is recovered from end-of-life recycling and substitutes are {subw}" if rec is not None else f" Substitutes are {subw}"
                mit += f", while the US imports {e(nir)} of what it consumes." if nir else "."
                b += mit
    return (f'<p class="note" style="margin:.15rem 0 .7rem;line-height:1.55">{b} '
            f'<span style="color:var(--faint);font-weight:600;white-space:nowrap">{src}</span></p>')

def year_slider(uid, items, default_i, accent='#2f6f4f'):
    """A clean year slider: drag the range to scrub years; a bold label shows the current year and the
    matching panel is shown. `items` = list of (label_str, panel_html). Reused by trade / mined / reserves.
    Each slider is namespaced by `uid`; one shared `yslide` fn (defined once) toggles panels by index."""
    n = len(items)
    labels = [lab for lab, _ in items]
    panels = ''.join(f'<div data-yc="{uid}" data-yi="{i}"{"" if i == default_i else " hidden"}>{h}</div>'
                     for i, (lab, h) in enumerate(items))
    return (
        f'<div style="display:flex;align-items:center;gap:.7rem;margin:.35rem 0 .55rem">'
        f'<span style="font-size:.8rem;color:var(--faint);font-weight:600">year</span>'
        f'<input type="range" min="0" max="{n - 1}" value="{default_i}" step="1" aria-label="year"'
        f' oninput="yslide(&quot;{uid}&quot;,this.value)"'
        f' style="flex:1;max-width:300px;accent-color:{accent};cursor:pointer;height:4px">'
        f'<b id="{uid}-lab" style="font-variant-numeric:tabular-nums;min-width:3.4em;font-size:1.02rem">{labels[default_i]}</b>'
        f'</div>{panels}'
        f'<script>window.YL=window.YL||{{}};window.YL["{uid}"]={labels!r}.map(String);'
        'if(!window.yslide){window.yslide=function(u,i){'
        'document.querySelectorAll(\'[data-yc="\'+u+\'"]\').forEach(function(p){p.hidden=(+p.dataset.yi!==+i);});'
        'var l=document.getElementById(u+"-lab");if(l)l.textContent=window.YL[u][i];};}</script>')

def layer_year_slider(label, series_map, cls, default_bars):
    """Wrap a layer's bars in a year slider if a validated multi-year series exists; else single-vintage bars."""
    ser = series_map.get(label)
    if not ser:
        return default_bars
    yrs = sorted(int(y) for y in ser)
    dft = 2023 if 2023 in yrs else max(yrs)
    items = [(str(y), bars(ser[str(y)], cls)) for y in yrs]
    return year_slider(f'{cls}-{label}', items, yrs.index(dft))

def qty_by(label, key, _fl=None):
    """Per country: (tonnes, value ON THOSE SAME edges) — so $/t is a price of the tonnage we actually have,
    not total-value / partial-tonnes. Quantity is 'where BACI reports it' (sparse for high-value metals)."""
    o = {}
    for fl in ((_fl or flows).get('materials', {}).get(label) or []):
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

def trade_table(ranked, tot, kind, qmap, yr=YEAR):
    rows = []
    for iso, val in ranked[:6]:
        t, vq = qmap.get(iso, (0.0, 0.0))
        upt = fmtUPT(vq / t) if t else '—'
        rows.append(f'<tr><td>{flag(iso)} {e(cname(iso))}</td><td class="n">{val/tot*100:.0f}%</td>'
                    f'<td class="n">{fmtV(val)}</td><td class="n">{fmtT(t)}</td><td class="n">{upt}</td></tr>')
    return (f'<table><caption>Top {kind} — reconciled trade, {yr}</caption>'
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

def share_stat(kind, pt, src, basis, rng):
    """Render a lead-miner / lead-refiner tile so the number cannot be read as a measured world
    share when it is not one. An estimate shows its RANGE rather than a false point; a BGS figure
    shows how many countries actually reported. Full provenance rides in the tooltip."""
    import re as _re
    if basis == 'unsourced':
        # a figure we inherited and cannot source: say so on the face of the page, not only in
        # the tooltip, and keep the number visible so a reader can challenge it
        return (f'{kind} · {pt:.0f}% <span style="color:var(--faint);font-weight:600">'
                f'(unsourced)</span>')
    if basis == 'estimate':
        core = f'{rng[0]}–{rng[1]}%' if rng else f'~{pt:.0f}%'
        label, note = f'{kind} · {core}', 'estimate'
    else:
        rep = _re.search(r'share of (\d+) reporting', src or '')
        label = f'{kind} · {pt:.0f}%'
        if rep:
            note = f'of {rep.group(1)} reporters'
        elif not src:
            # No recorded provenance. Say so rather than let a bare number read as measured -
            # an unlabelled share is exactly the failure this whole pass exists to remove.
            note = 'source not recorded'
        else:
            note = ''
    if note:
        label += f' <span style="color:var(--faint);font-weight:600">({note})</span>'
    return label


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
    if m.get('host'): stats.append(('<span style="color:#7a5cff">⚗ by-product</span>', f'of {e(m["host"])}'))
    if m.get('export_control'): stats.append(('<span style="color:#e0703c">⚠ controlled</span>', e(m['export_control'])))
    if m.get('net_import_reliance'): stats.append((e(m['net_import_reliance']), 'US import reliance'))
    if rv: stats.append((f'{flag(rv["c"])} {cname(rv["c"])}', f'lead reserves · {rv["v"]:.0f}%'))
    if mi: stats.append((f'{flag(mi["c"])} {cname(mi["c"])}',
                         share_stat('lead miner', mi['v'], m.get('mined_source'),
                                    m.get('mined_basis'), m.get('mined_range')),
                         m.get('mined_source')))
    if re: stats.append((f'{flag(re["c"])} {cname(re["c"])}',
                         share_stat('lead refiner', re['v'], m.get('refined_source'),
                                    m.get('refined_basis'), m.get('refined_range')),
                         m.get('refined_source')))
    if texp: stats.append((f'{flag(texp[0])} {cname(texp[0])}', f'top exporter · {texp[1]/etot*100:.0f}%'))
    if texp: stats.append((f'{ehhi:.2f}', 'export concentration (HHI)'))
    def _stat(s):
        # s = (value, label, [provenance tooltip]); label may carry safe markup from share_stat
        tip = f' title="{e(s[2])}"' if len(s) > 2 and s[2] else ''
        cue = '<span style="color:var(--faint);cursor:help"> ⓘ</span>' if len(s) > 2 and s[2] else ''
        lab = s[1] if '<span' in str(s[1]) else e(s[1])
        return f'<div class="stat"{tip}><div class="n">{s[0]}</div><div class="l">{lab}{cue}</div></div>'
    stat_html = ''.join(_stat(s) for s in stats)

    host_callout = ''
    if m.get('host'):
        h = e(m['host'])
        host_callout = (f'<div class="callout" style="border-color:#7a5cff55"><b>⚗ A by-product, not a primary metal.</b> '
                        f'{e(title)} is not mined for its own sake — it is recovered as a by-product of <b>{h}</b>. '
                        f'So its supply tracks the <b>{h}</b> market, not its own price: a shortage can’t quickly pull more '
                        f'out of the ground, because miners dig for {h}, not for this. That inelastic supply is a core, often-missed supply-risk driver.</div>')

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

    shared_flag = ('<div class="callout" style="border-color:#c08a2b66"><b>⛓ Trade shown under HS 811292 — a shared code.</b> '
                   'Gallium and germanium both clear customs under this one 6-digit line, so their trade columns are '
                   '<b>identical and cannot be separated</b> (the code is a catch-all that also nominally covers hafnium, indium, '
                   'niobium, rhenium and vanadium; here only gallium and germanium are drawn from it). Any trade-based '
                   'concentration figure for this material is really measuring <b>two supply chains at once</b> — it can only be '
                   'split at 8-digit national tariff lines. The mine, refine and reserve layers above <i>are</i> material-specific.</div>') if shared else ''

    note = e(m.get('note') or '').strip()
    note_block = f'<h2>Context</h2><p>{note}</p>' if note else ''

    # trade tables with an in-page YEAR SWITCHER: render exporters+importers for every year 2018–2026,
    # embed all, show one; a tiny script toggles panels. Uses each year's own flows (via side/qty_by on
    # a swapped global) — measured 2018–2024, 2025* nowcast, 2026** scenario.
    global flows
    _saved_flows = flows
    sw_years = [y for y in sorted(FLOW_ALL) if y >= 2018]
    default_y = int(YEAR) if int(YEAR) in sw_years else (max([y for y in sw_years if y <= 2024]) if sw_years else None)
    year_blocks = {}
    for y in sw_years:
        flows = FLOW_ALL[y]
        te_y, ti_y = side(label, 'from'), side(label, 'to')
        tb = ''
        if te_y[0]: tb += trade_table(te_y[1], te_y[3], 'exporters', qty_by(label, 'from', flows), y)
        if ti_y[0]: tb += trade_table(ti_y[1], ti_y[3], 'importers', qty_by(label, 'to', flows), y)
        year_blocks[y] = tb or '<p class="note">No reconciled trade recorded for this year.</p>'
    flows = _saved_flows

    def _ylab(y): return f'{y}*' if y == 2025 else f'{y}**' if y == 2026 else str(y)
    if sw_years:
        items = [(_ylab(y), year_blocks[y]) for y in sw_years]
        trade_block = year_slider(f'tr-{label}', items, sw_years.index(default_y))
    else:
        trade_block = ''

    nm = e(title.split(",")[0]).lower()
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
  {host_callout}
  {gap_callout}
  {trend_block}
  <h2>The chain — from the ground to the buyer</h2>
  <p class="note" style="margin-top:-.3rem">A critical material passes through distinct stages, and the country that leads each stage is often <i>different</i> — that gap is what this atlas exists to show. Each layer comes from a different public source with its own vintage, labelled below; shares are % of the world total.</p>
  <h3>● Reserves — where it could come from</h3>
  {layer_para(m, 'reserves', nm)}{layer_year_slider(m['label'], RESERVES_YEARS, 'res', bars(m.get('reserves'), 'res'))}
  <h3>● Mined — where it is dug up today</h3>
  {layer_para(m, 'mined', nm)}{layer_year_slider(m['label'], MINED_YEARS, 'ore', bars(m.get('mined'), 'ore'))}
  <h3>● Refined / processed — where it becomes usable metal</h3>
  {layer_para(m, 'refined', nm)}{layer_year_slider(m['label'], REFINED_YEARS, 'ref', bars(m.get('refined'), 'ref', source='refined'))}
  <h3>● Recycling &amp; substitutability — the mitigants (EU CRM)</h3>
  <p>{(f'<b>{m.get("recycling")}%</b> of supply comes from recycling end-of-life products' + (' — a meaningful secondary source that lowers the supply-risk score.' if (m.get("recycling") or 0) >= 15 else ('.' if (m.get("recycling") or 0) > 0 else ' — there is essentially no end-of-life recycling, so a disruption has no secondary cushion.'))) if m.get('recycling') is not None else 'No reliable recycling figure.'} {('Substitutability is <b>' + str(m.get('substitutability')) + '</b>' + (' — few or no alternatives, so a disruption bites hard.' if m.get('substitutability')=='high' else (' — good alternatives exist.' if m.get('substitutability')=='low' else ' — partial substitutes exist.')) ) if m.get('substitutability') else ''}</p>
  <h2>● Traded — who ships it</h2>
  {shared_flag}
  <p class="note" style="margin:.15rem 0 .5rem">Actual bilateral trade of the traded form, reconciled from UN Comtrade / CEPII BACI. Pick a year below — <span style="color:var(--faint);font-weight:600">2018–2024 measured, 2025* nowcast, 2026** directional scenario</span>. The full 2002–2026 range is on the <a href="./#view=flow&amp;mat={e(label)}">interactive atlas</a>.</p>
  {trade_block}
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

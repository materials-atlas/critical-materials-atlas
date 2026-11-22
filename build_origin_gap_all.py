#!/usr/bin/env python3
"""Origin gap across every material we hold: is the top exporter the top miner?

The original test ran on the atlas's own materials (out/data.json, out/flows_2024.json). This widens
it to every other material for which we hold both world mine output and world customs trade. The
customs code for each new material, and the mine source rule, were frozen in origin-gap-all/codes.json
(commit fc3cf1ff) before any result was computed.

Trade is read through baci.py (HS17, misclassified flows dropped there).
Writes out/origin_gap_all.json and origin-gap-all.html. Public data; deterministic.
Run: python build_origin_gap_all.py
"""
import html, json, os

import pandas as pd

import baci
import mine_shares as MS

ROOT = os.path.dirname(os.path.abspath(__file__))
YEAR = 2024
spec = json.load(open(os.path.join(ROOT, 'origin-gap-all', 'codes.json'), encoding='utf8'))
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
flows = json.load(open(os.path.join(ROOT, 'out', f'flows_{YEAR}.json'), encoding='utf8'))

import shared_code
# Left out, on top of the frozen list in codes.json (not edited: it is the filed spec): the materials
# the world trade file reads from ONE shared code. Their "top exporter" is the top exporter of a
# basket of several metals, so setting it against one metal's mine shares tests nothing. Until
# Nov 2026 hafnium sat in the table with the basket's exporter against hafnium's own miners.
EXCLUDED = dict(spec['excluded'])
EXCLUDED[', '.join(sorted(shared_code.SHARED))] = ('read from one customs code in the world trade file '
                                                    '(HS 811292), so they cannot be tested one by one')

cc = baci.countries()   # the one door: Taiwan and Namibia ("NA") overrides applied there
I3TO2 = {r.iso3: r.iso2 for r in cc.itertuples() if r.iso3 and r.iso2}
NAMES = {r.iso2: r.name for r in cc.itertuples() if r.iso2 and r.name}
NAMES.update(flows.get('names', {}))
HUBS = {'AE', 'SG', 'HK', 'NL', 'BE', 'PA', 'MO', 'GI'}   # re-export hubs: named on the page
USGS = {'zinc', 'lead', 'tin', 'chromium', 'molybdenum', 'rare_earths'}
TITLE = {'zinc': 'Zinc', 'lead': 'Lead', 'tin': 'Tin', 'silver': 'Silver', 'gold': 'Gold',
         'rhodium': 'Rhodium', 'cadmium': 'Cadmium', 'bismuth': 'Bismuth', 'selenium': 'Selenium',
         'mercury': 'Mercury', 'chromium': 'Chromium', 'molybdenum': 'Molybdenum',
         'zirconium': 'Zirconium', 'iron': 'Iron ore', 'rare_earths': 'Rare earths', 'salt': 'Salt',
         'gypsum': 'Gypsum', 'kaolin': 'Kaolin', 'bentonite': 'Bentonite', 'talc': 'Talc',
         'diatomite': 'Diatomite', 'perlite_vermiculite': 'Perlite and vermiculite',
         'potash': 'Potash', 'sulphur': 'Sulphur', 'diamond': 'Diamonds (rough, gem)',
         'bromine': 'Bromine', 'sillimanite': 'Sillimanite minerals', 'asbestos': 'Asbestos'}


def top(pairs):
    o, tot = {}, 0.0
    for c, v in pairs:
        v = float(v or 0)
        if v != v:
            continue
        if not isinstance(c, str):   # exporter BACI cannot map to a country: in the world total, never the top
            tot += v
            continue
        o[c] = o.get(c, 0.0) + v
        tot += v
    if not tot:
        return None, 0.0
    c = max(o, key=o.get)
    return c, o[c] / tot * 100


def share_of(pairs, c):
    """Country c's percent of the total, or None if there is no total."""
    mine, tot = 0.0, 0.0
    for k, v in pairs:
        v = float(v or 0)
        if v != v:
            continue
        tot += v
        if k == c:
            mine += v
    return round(mine / tot * 100, 1) if tot else None


rows = []


def own_share(c, listed, src, full, full_src):
    """What country c itself mines -> (percent or None, source).
    USGS names the larger producers and lumps the rest as 'Other countries', so a country a USGS
    table does not name is not zero: ask a source that names every country (World Mining Data,
    else BGS). With none, the answer is unknown (None), never 0."""
    if c in listed:
        return float(listed[c]), src
    if not src.startswith('USGS'):
        return 0.0, src
    if full:
        return float(full.get(c, 0)), full_src
    return None, None


MINED = json.load(open(os.path.join(ROOT, 'out', 'mined_shares.json'), encoding='utf8'))

# ---- the atlas's own materials: the original test, unchanged ----
for m in data['materials']:
    if m['label'] in shared_code.SHARED:
        continue
    a = flows.get('materials', {}).get(m['label']) or []
    mi = (m.get('mined') or [None])[0]
    if not a or not mi:
        continue
    tev, tevs = top((f['from'], f['value']) for f in a)
    teq, _ = top((f['from'], f.get('qty')) for f in a)
    tev_q = share_of(((f['from'], f.get('qty')) for f in a), tev)
    t = m['title']
    # What the top exporter itself mines. From the full country list where a source gives one;
    # for the few materials kept by hand only the listed producers are known, so a country not
    # listed is None (unknown), never 0.
    ms_rec = MINED['materials'].get(m['label'])
    if ms_rec:
        msrc = ms_rec['source']
        own, own_src = own_share(tev, ms_rec['shares'], msrc, ms_rec.get('shares_all_countries'),
                                 ms_rec.get('shares_all_countries_source'))
    else:
        own = next((float(x['v']) for x in m['mined'] if x['c'] == tev), None)
        msrc = own_src = 'atlas mined list, kept by hand (no mine-production source covers it)'
    rows.append({'material': m['label'], 'title': t.split(' (')[0], 'form': t[t.find('(') + 1:-1] if '(' in t else '',
                 'set': 'atlas', 'mine_source': msrc,
                 'top_miner': mi['c'], 'top_miner_share': float(mi['v']),
                 'top_exporter': tev, 'top_exporter_share': round(tevs, 1),
                 'top_exporter_tonnes': teq, 'top_exporter_share_tonnes': tev_q,
                 'top_exporter_mine_share': own, 'top_exporter_mine_share_source': own_src,
                 'gap_value': tev != mi['c'], 'gap_tonnes': teq is not None and teq != mi['c']})

# ---- every other material with mine and trade data: codes frozen in codes.json ----
MATS = spec['materials']
want = {v['hs'] for v in MATS.values()}
b = baci.year(YEAR, codes=sorted(want), iso='iso2', nom='HS17').rename(columns={'i_iso': 'exp'})
def mine_shares(mat):     # the one rule, mine_shares.py (also used for the atlas's own materials)
    src, sh, _ = MS.shares(usgs=mat if mat in USGS else None, cube=MATS[mat].get('mine', [mat]), year=YEAR,
                           native_label='Diamonds (Gem)' if mat == 'diamond' else None)  # HS 710231 = gem
    return src, sh


for mat, d in MATS.items():
    src, ms = mine_shares(mat)
    t = b[b.k == d['hs']]
    tev, tevs = top(zip(t.exp, t.v))
    teq, _ = top(zip(t.exp, t.q))
    tev_q = share_of(zip(t.exp, t.q), tev)
    if not ms or tev is None:
        continue
    tm3 = max(ms, key=ms.get)
    tm = I3TO2.get(tm3, tm3)
    listed = {}
    for k, v in ms.items():
        listed[I3TO2.get(k, k)] = listed.get(I3TO2.get(k, k), 0.0) + v
    full, full_src = None, None
    if src.startswith('USGS') and tev not in listed:
        full_src, f3, _ = MS.shares(usgs=None, cube=d.get('mine', [mat]), year=YEAR,
                                    native_label='Diamonds (Gem)' if mat == 'diamond' else None)
        full = {}
        for k, v in f3.items():
            full[I3TO2.get(k, k)] = full.get(I3TO2.get(k, k), 0.0) + v
    own, own_src = own_share(tev, listed, src, full, full_src)
    rows.append({'material': mat, 'title': TITLE.get(mat, mat), 'form': f"{d['form']}, HS {d['hs']}",
                 'set': 'widened', 'mine_source': src,
                 'top_miner': tm, 'top_miner_share': round(ms[tm3], 1),
                 'top_exporter': tev, 'top_exporter_share': round(tevs, 1),
                 'top_exporter_tonnes': teq, 'top_exporter_share_tonnes': tev_q,
                 'top_exporter_mine_share': None if own is None else round(own, 1),
                 'top_exporter_mine_share_source': own_src,
                 'gap_value': tev != tm, 'gap_tonnes': teq is not None and teq != tm})

n_gap = sum(r['gap_value'] for r in rows)
n_gap_t = sum(r['gap_tonnes'] for r in rows)
def is_hub(r):   # a re-export hub that mines (almost) none of the material itself
    return r['gap_value'] and r['top_exporter'] in HUBS and (r.get('top_exporter_mine_share') or 0) < 5
hub_rows = [r for r in rows if is_hub(r)]
n_gap_hub = len(hub_rows)
# The site says "most materials" in words, on this page AND on hand-written pages (index, explorer, analysis,
# confidence, findings, three dated update notes). If that stops being true, stop the build loudly.
if not (2 * n_gap > len(rows) and 2 * n_gap_t > len(rows)):
    raise SystemExit('origin gap is no longer a majority (%d value, %d tonnes, of %d measured): the "most materials" '
                     'wording on the site is now false - rewrite it on every page that carries it' % (n_gap, n_gap_t, len(rows)))
out = {'year': YEAR, 'spec': 'origin-gap-all/codes.json', 'excluded': EXCLUDED,
       'n_gap_value': n_gap, 'n_gap_tonnes': n_gap_t, 'n_gap_value_hub_exporter': n_gap_hub,
       'n_atlas_gap': sum(r['gap_value'] for r in rows if r['set'] == 'atlas'),
       'n_widened_gap': sum(r['gap_value'] for r in rows if r['set'] == 'widened'),
       'rows': rows}
with open(os.path.join(ROOT, 'out', 'origin_gap_all.json'), 'w', encoding='utf8', newline='\n') as fh:
    json.dump(out, fh, indent=1)

# ---- page ----
def e(s): return html.escape(str(s), quote=True)
def cn(c): return e(NAMES.get(c, c))
def flag(iso):
    if not iso or len(iso) != 2 or not iso.isalpha(): return ''
    return ''.join(chr(0x1F1E6 + ord(ch.upper()) - 65) for ch in iso)

trs = []
for r in sorted(rows, key=lambda r: (not r['gap_value'], r['title'].lower())):
    name = (f'<a href="profile-{e(r["material"])}.html">{e(r["title"])}</a>' if r['set'] == 'atlas'
            else e(r['title']))
    hub = ' <span style="color:#9aa6ad;font-size:.85em">(re-export hub)</span>' if is_hub(r) else ''
    mark = ('<b style="color:#0e7c74">yes</b>' if r['gap_value'] else '<span style="color:#9aa6ad">no</span>')
    trs.append(f'<tr><td>{name}<br><span style="color:#9aa6ad;font-size:.85em">{e(r["form"])}</span></td>'
               f'<td>{flag(r["top_miner"])} {cn(r["top_miner"])} <span style="color:#9aa6ad">{r["top_miner_share"]:.0f}%</span></td>'
               f'<td>{flag(r["top_exporter"])} {cn(r["top_exporter"])} <span style="color:#9aa6ad">{r["top_exporter_share"]:.0f}%</span>{hub}</td>'
               f'<td class="n">{mark}</td></tr>')

kept = [r['title'].lower() for r in rows if r['mine_source'].startswith('atlas mined list')]
kept_sentence = ('No such source covers ' + ', '.join(e(x) for x in kept) + '; their mine shares are compiled by hand from the literature.') if kept else ''
hub_sentence = ('Only for ' + ', '.join(e(r['title'].lower()) for r in hub_rows) + ' is the top exporter a re-export hub that mines almost none of it.') if hub_rows else ''
excl = '; '.join(f'{e(k)}: {e(v)}' for k, v in EXCLUDED.items())
page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The origin gap, every material — Critical Materials Atlas</title>
<meta name="description" content="For every material with world mine and trade data: is the country that exports it the country that mines it? For most materials it is not.">
<meta property="og:title" content="The origin gap, every material">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="explorer">Explore</a><a href="value-chains">Value Chains</a><a href="analysis">Analysis</a><a href="reports">Reports</a><a href="method">Method</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Finding · every material</div>
  <h1>The origin gap, every material</h1>
  <p class="deck">Is the country that sells a material to the world the country that digs it up? For <b>most</b> materials it is not: a refinery, a smelter or a trading hub stands between the mine and the buyer.</p>
</div></section>
<article style="max-width:1000px">
  <div class="callout">The test is run on every material for which the atlas holds both world mine output and world customs trade, and it grows as the atlas does. Counted in tonnes instead of dollars the gap holds just as widely, so it is not an artifact of prices. {hub_sentence} In the others the top exporter is a country that refines, smelts or processes the material.</div>

  <table>
    <thead><tr><th>Material and traded form</th><th>Top miner, share of world output</th><th>Top exporter, share of world exports (US$)</th><th class="n">Gap</th></tr></thead>
    <tbody>{''.join(trs)}</tbody>
  </table>

  <details class="howto"><summary>How it is measured, and what it cannot show</summary>
  <p><b>One traded form per material.</b> Each material is measured on its main traded form: refined or unwrought metal, or a ferro-alloy, for metals; the crude mineral for industrial minerals. A material traded at several stages would show a different exporter at each one. The customs code for every material added beyond the atlas&rsquo;s own was fixed in <a href="origin-gap-all/codes.json">codes.json</a> before any result was computed.</p>
  <p><b>Mine and trade come from different sources.</b> Trade: CEPII BACI (HS 2017), {YEAR}, by value. Mine output, {YEAR}, by one rule for every material: the USGS Mineral Commodity Summaries where held, otherwise World Mining Data, otherwise BGS World Mineral Statistics. {kept_sentence} For by-products such as cadmium, selenium and bismuth, &ldquo;mine&rdquo; output is the refinery production these sources report, and for sulphur it is mostly sulphur recovered from oil and gas.</p>
  <p><b>Left out.</b> {excl}.</p>
  <p class="howto-src">Computed by <code>build_origin_gap_all.py</code> &rarr; <a href="out/origin_gap_all.json">origin_gap_all.json</a>. Shares rounded to whole percents.</p>
  </details>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="explorer">Explore</a><br><a href="value-chains">Value Chains</a><br><a href="analysis">Analysis</a><br><a href="reports">Reports</a><br><a href="method">Method</a></div>
  <div><h4>Sources</h4>CEPII BACI · USGS · IEA<br>World Mining Data · BGS</div>
  <div class="fineprint">Top exporter against top miner, one traded form per material, {YEAR}.</div>
</div></footer>
</body></html>'''
with open(os.path.join(ROOT, 'origin-gap-all.html'), 'w', encoding='utf8', newline='\n') as fh:
    fh.write(page)
print(f'wrote origin-gap-all.html + out/origin_gap_all.json: {len(rows)} materials measured, '
      f'{n_gap} gaps by value ({out["n_atlas_gap"]} atlas + {out["n_widened_gap"]} widened), {n_gap_t} in tonnes, '
      f'{n_gap_hub} with a hub exporter')

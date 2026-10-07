#!/usr/bin/env python3
"""
Origin trace, second layer: China's own imported feed.

build_origin.py keeps a supplier as the origin when it genuinely mines the material (world mine share >= 5%).
For China that rule always fires, so the trace stops at China. But China is both the leading miner and a large
importer of ores, concentrates and intermediates for several materials, and the trade records then name China
as the exporter of what it makes from them. This builder measures that imported feed: for every material where
China's world mine share is >= 5% and the feed has a clean (non-basket) HS 2017 code, it sums China's own
import declarations by partner (UN Comtrade annual, cached by fetch_origin_feed.py), 2017-2024, and records
CEPII BACI's reconciled figure beside it as a cross-check. China's own record is primary because BACI's
reconciliation drops most of Mozambique's titanium minerals and Australia's zircon (checked 7 Oct 2026).

Tonnages are gross weights of ores, concentrates or compounds, so they are not contained metal and are not
comparable with mine output; read them as the scale and the sources of the feed, not as a share of supply.
Basket codes (HS 2530.90, which holds spodumene, celestite and rare-earth ores among others) are excluded.

Writes out/origin_feed.json.  Public data; deterministic.
"""
import json, os, zipfile
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
BACI = os.path.join(ROOT, 'raw', 'baci', 'BACI_HS17_V202601.zip')
CACHE = os.path.join(ROOT, 'raw', 'comtrade', 'china_feed_imports.json')   # written by fetch_origin_feed.py
YEARS = list(range(2017, 2025))
CHINA = 156
MINER_MIN = 5.0

# material label -> (feed description, HS 2017 six-digit codes)
FEED = {
    'magnets':   ('Rare earths', 'rare-earth compounds and metals', ['284610', '284690', '280530']),
    'graphite':  ('Graphite', 'natural graphite', ['250410', '250490']),
    'tungsten':  ('Tungsten', 'tungsten ores and concentrates', ['261100']),
    'antimony':  ('Antimony', 'antimony ores and concentrates', ['261710']),
    'fluorspar': ('Fluorspar', 'fluorspar', ['252921', '252922']),
    'titanium':  ('Titanium', 'titanium ores and concentrates', ['261400']),
    'bauxite':   ('Aluminium', 'bauxite (aluminium ores)', ['260600']),
    'manganese': ('Manganese', 'manganese ores and concentrates', ['260200']),
    'copper':    ('Copper', 'copper ores and concentrates', ['260300']),
    'baryte':    ('Baryte', 'natural barium sulphate', ['251110']),
    'phosphate': ('Phosphate', 'natural phosphates', ['251010', '251020']),
    'hafnium':   ('Hafnium', 'zirconium ores (zircon, the hafnium source)', ['261510']),
    'feldspar':  ('Feldspar', 'feldspar', ['252910']),
}
# China a >=5% miner, but no clean feed code in HS 2017
NO_CODE = {
    'lithium': 'spodumene is in basket code HS 2530.90',
    'strontium': 'celestite is in basket code HS 2530.90',
    'vanadium': 'vanadium slag has no dedicated HS code',
    'cokingcoal': 'HS 2701.12 mixes coking and thermal coal',
    'arsenic': 'no dedicated ore code', 'beryllium': 'beryl is in a basket ore code',
    'magnesium': 'mined as magnesite/dolomite; metal made domestically',
    'germanium': 'recovered from zinc and coal; no ore trade', 'gallium': 'recovered from alumina; no ore trade',
    'silicon': 'quartz feed is not traded under a dedicated code', 'phosphorus': 'elemental phosphorus is made from phosphate rock (natural phosphates row)',
}

data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
TITLES = {m['label']: m['title'].split(' (')[0] for m in data['materials']}
CN_MINE = {m['label']: next((x['v'] for x in (m.get('mined') or []) if x['c'] == 'CN'), 0) for m in data['materials']}

z = zipfile.ZipFile(BACI)
cc = pd.read_csv(z.open(next(n for n in z.namelist() if 'country_codes' in n)), keep_default_na=False)   # Namibia's ISO2 is 'NA'
ISO2 = dict(zip(cc.country_code, cc.country_iso2))
I3_2 = dict(zip(cc.country_iso3, cc.country_iso2))
ATLAS_NAMES = json.load(open(os.path.join(ROOT, 'out', 'flows_2024.json'), encoding='utf8')).get('names', {})
codes = {c for _, _, cs in FEED.values() for c in cs}

# PRIMARY: China's own import declarations (UN Comtrade annual, cached by fetch_origin_feed.py)
cache = json.load(open(CACHE, encoding='utf8'))
cn = pd.DataFrame(cache['rows'])
cn['y'] = cn['period'].astype(int)
cn['t'] = pd.to_numeric(cn['netWgt'], errors='coerce').fillna(0) / 1000.0
cn['c'] = cn['partnerCode'].map(ISO2)          # Comtrade and BACI share the numeric country codes
unmapped = sorted(set(cn.loc[cn['c'].isna(), 'partnerCode']))
if unmapped:
    print('partner codes with no ISO2 in BACI (kept as numbers):', unmapped)
cn['c'] = cn['c'].fillna(cn['partnerCode'].astype(str))

# CROSS-CHECK: CEPII BACI (reconciled exporter/importer declarations)
frames = []
for y in YEARS:
    name = next(n for n in z.namelist() if f'_Y{y}_' in n)
    for ch in pd.read_csv(z.open(name), dtype={'k': str}, chunksize=2_000_000):
        ch = ch[(ch.j == CHINA) & (ch.k.isin(codes))]
        if len(ch):
            frames.append(ch[['t', 'i', 'k', 'v', 'q']])
bc = pd.concat(frames)
bc['q'] = pd.to_numeric(bc['q'], errors='coerce')
bc['c'] = bc['i'].map(ISO2)

def top(frame, col_c, col_q):
    g = frame.groupby(col_c)[col_q].sum().sort_values(ascending=False)
    tot = float(g.sum()) or 1.0
    return g, tot

out = {'source': 'UN Comtrade annual, China-reported imports (reporter 156), net weight; cross-checked against CEPII BACI HS17 V202601',
       'fetched': cache.get('fetched'), 'years': YEARS, 'miner_min': MINER_MIN,
       'note': 'Gross tonnes of ores, concentrates or compounds; not contained metal; not comparable with mine output.',
       'materials': [], 'no_code': NO_CODE}
for label, (fam, desc, cs) in FEED.items():
    if CN_MINE.get(label, 0) < MINER_MIN:
        continue
    d = cn[cn.cmdCode.isin(cs)]
    by_year = d.groupby('y').t.sum()
    series = [{'y': y, 't': round(float(by_year.get(y, 0.0)))} for y in YEARS]
    # a year below half of BOTH neighbours is flagged as suspect, not silently used
    suspect = [series[k]['y'] for k in range(1, len(series) - 1)
               if series[k]['t'] < 0.5 * series[k - 1]['t'] and series[k]['t'] < 0.5 * series[k + 1]['t']]
    est_share = {y: float(d[(d.y == y) & (d.isNetWgtEstimated == True)].t.sum()) / (float(d[d.y == y].t.sum()) or 1.0) for y in suspect}
    last, tot = top(d[d.y == YEARS[-1]], 'c', 't')
    origins = [{'c': c, 'name': ATLAS_NAMES.get(c, c), 't': round(float(q)), 'share': round(float(q) / tot * 100, 4)}
               for c, q in last.head(5).items()]
    b = bc[(bc.k.isin(cs)) & (bc.t == YEARS[-1])]
    bl, btot = top(b, 'c', 'q')
    out['materials'].append({'label': label, 'name': fam, 'title': TITLES.get(label, label), 'feed': desc, 'hs': cs,
                             'cn_mine_share': CN_MINE[label], 'series': series, 'origins_last': origins,
                             'n_suppliers_last': int((last > 0).sum()), 'suspect_years': suspect, 'suspect_mostly_estimated': [y for y in suspect if est_share[y] > 0.5],
                             'estimated_weight_rows_last': int(d[(d.y == YEARS[-1]) & (d.isNetWgtEstimated == True)].shape[0]),
                             'baci_last_t': round(btot), 'baci_gap_pct': round((btot / tot - 1) * 100, 1) if tot > 1 else None,
                             'baci_origins_last': [{'c': c, 'share': round(float(q) / btot * 100, 4)} for c, q in bl.head(3).items()]})
out['materials'].sort(key=lambda m: m['series'][-1]['t'], reverse=True)
json.dump(out, open(os.path.join(ROOT, 'out', 'origin_feed.json'), 'w', encoding='utf8'), indent=1, ensure_ascii=False)

print(f"wrote out/origin_feed.json - {len(out['materials'])} materials")
for m in out['materials']:
    s = m['series']
    print(f"  {m['label']:<10} CN mine {m['cn_mine_share']:>3}% | {s[0]['y']} {s[0]['t']:>12,} t -> {s[-1]['y']} {s[-1]['t']:>12,} t | "
          + ', '.join(f"{o['c']} {o['share']:.0f}%" for o in m['origins_last'][:3])
          + f" | BACI {m['baci_gap_pct'] if m['baci_gap_pct'] is None else format(m['baci_gap_pct'], '+.1f')}% | est rows {m['estimated_weight_rows_last']} | suspect {m['suspect_years']}")

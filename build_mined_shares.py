#!/usr/bin/env python3
"""Mine shares for the atlas's own materials, by the one rule in mine_shares.py.

Writes out/mined_shares.json: per material the top producers [{c: iso2, v: percent}], the source,
and the text the profile shows as provenance. out/data.json's `mined` must equal it - check.py's
`mined` check fails the build otherwise - and build_static.R reads it instead of a typed list.

Each material also carries `shares`, the full country list, for anything that asks what a country
outside the top six mines (the origin gap does).

Materials no source covers keep the value already in data.json and are listed as such.
Run: python build_mined_shares.py
"""
import json, os

import baci
import mine_shares as MS

ROOT = os.path.dirname(os.path.abspath(__file__))
YEAR = 2024
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))

# atlas label -> (USGS store commodity, cube material names). One line per material, nothing typed
# but the names. magnets = rare-earth mining; magnesium's only mine series is magnesite ore.
MAP = {
    'magnets': ('rare_earths', ['rare_earths']), 'magnesium': (None, ['magnesium']),
    'graphite': ('graphite', ['graphite']), 'tungsten': ('tungsten', ['tungsten']),
    'cobalt': ('cobalt', ['cobalt']), 'niobium': (None, ['niobium']), 'boron': (None, ['boron']),
    'lithium': ('lithium', ['lithium']), 'antimony': ('antimony', ['antimony']),
    'platinum': ('platinum', ['platinum']), 'palladium': ('palladium', ['palladium']),
    'fluorspar': ('fluorspar', ['fluorspar']), 'titanium': ('titanium', ['titanium']),
    'feldspar': ('feldspar', ['feldspar']), 'vanadium': ('vanadium', ['vanadium']),
    'manganese': ('manganese', ['manganese']), 'bauxite': (None, ['bauxite']),
    'phosphate': ('phosphate_rock', ['phosphate']), 'baryte': ('barite', ['baryte']),
    'arsenic': (None, ['arsenic']), 'beryllium': (None, ['beryllium']),
    'strontium': (None, ['strontium']), 'tantalum': (None, ['tantalum']),
    'cokingcoal': (None, ['cokingcoal']), 'copper': ('copper', ['copper']),
    'nickel': ('nickel', ['nickel']),
}
I2 = {r.iso3: r.iso2 for r in baci.countries().itertuples() if r.iso3 and r.iso2}
SHORT = {'USGS Mineral Commodity Summaries': 'USGS MCS', 'World Mining Data': 'World Mining Data',
         'BGS World Mineral Statistics': 'BGS World Mineral Statistics'}
NAME = {r.iso2: r.name for r in baci.countries().itertuples() if r.iso2 and r.name}

out = {'year': YEAR, 'rule': MS.__doc__.split('THE RULE')[1].split('Why it exists')[0].strip(),
       'materials': {}, 'kept_by_hand': {}}
for m in data['materials']:
    lab = m['label']
    if lab not in MAP:
        out['kept_by_hand'][lab] = {'mined': m.get('mined'), 'mined_source': m.get('mined_source'),
                                    'why': 'no mine-production source covers it'}
        continue
    usgs, cube = MAP[lab]
    src, sh, det = MS.shares(usgs=usgs, cube=cube, year=YEAR)
    if not sh:
        raise SystemExit(f'{lab}: no source returned shares - fix MAP, do not fall back to a typed list')
    top = sorted(((I2.get(k, k), v) for k, v in sh.items()), key=lambda x: -x[1])
    mined = [{'c': c, 'v': int(round(v))} for c, v in top[:6] if round(v) >= 1]
    lead = mined[0]
    where = f"{SHORT[src]} {det['edition']}" if 'edition' in det else SHORT[src]
    text = (f"{where} · {YEAR} mine production · {NAME.get(lead['c'], lead['c'])} {lead['v']}%"
            + (f" · measured as {det['measured_as']}" if det.get('measured_as') else ''))
    if src.startswith('BGS'):
        text += f" · share of {det['reporters']} reporting countries"
    # `shares` is every producing country, not the six shown: a country outside the top six still
    # mines, and a reader of this file must not take its absence from `mined` for zero.
    out['materials'][lab] = {'mined': mined, 'mined_source': text + ' [measured]', 'source': src,
                             'detail': det,
                             'shares': {c: round(v, 1) for c, v in top if round(v, 1) > 0}}
    # USGS names the larger producers and lumps the rest as "Other countries": a country it does
    # not name is NOT zero. So beside a USGS table, keep a list from a source that names every
    # country (World Mining Data, else BGS), for the question "does this country mine any".
    if src.startswith('USGS'):
        src2, sh2, _ = MS.shares(usgs=None, cube=cube, year=YEAR)
        if sh2:
            out['materials'][lab]['shares_all_countries'] = {
                I2.get(k, k): round(v, 1) for k, v in sh2.items() if round(v, 1) > 0}
            out['materials'][lab]['shares_all_countries_source'] = src2

with open(os.path.join(ROOT, 'out', 'mined_shares.json'), 'w', encoding='utf8', newline='\n') as fh:
    json.dump(out, fh, indent=1, ensure_ascii=False)
print(f"wrote out/mined_shares.json: {len(out['materials'])} by the rule, "
      f"{len(out['kept_by_hand'])} kept by hand ({', '.join(out['kept_by_hand'])})")
for lab, r in out['materials'].items():
    print(f"  {lab:11} {' '.join(x['c'] + str(x['v']) for x in r['mined'][:3]):20} {r['mined_source'][:70]}")

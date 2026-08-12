"""Capability map: fuse the trade FEEDSTOCK SIGNATURE with BGS/USGS physical output.

Turning the export map into a capability map. Two independent lenses, fused:

  TRADE SIGNATURE (from the BACI bilateral matrix) -- a positive, export-control-proof marker.
    For country x material we split four flows: ore imports/exports, refined imports/exports, then
      net_down          = (ref_exp - ref_imp)/(ref_exp + ref_imp)   >0 => net exporter of refined
      feedstock_import  = ore_imp/(ore_imp + ore_exp)               ~1 => sources ore by IMPORT
      ref_world_share   = country share of world refined exports     (magnitude / importance)
    trade_score = ref_world_share * max(net_down,0)   -- robust: penalises re-export (net_down<0) and
    is ~0 for a raw exporter whose refined flow is trivial (fixes the v1 sign-flip on tiny flows).

  PHYSICAL (BGS/USGS refined share already in data.json) -- catches the DOMESTIC-ABSORBING refiner
  (China refines ~40% of copper / most alumina / Ti sponge but CONSUMES it, so it never shows in
  refined EXPORTS and is invisible to any trade metric).

  cap = max(physical_share, trade_score)   -- a country is capable if EITHER lens sees it.
  basis: 'both' | 'physical (domestic-absorbing)' | 'trade'   -- which lens carried it.

Run:  python build_feedstock.py [year]   (default 2022)
"""
import os, sys, io, zipfile, json
import numpy as np, pandas as pd
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2022
BACI_ZIP = os.path.join(ROOT, 'raw', 'baci', 'BACI_HS17_V202601.zip')

CROSSWALK = {'copper': ('260300', '740311'), 'nickel': ('260400', '750210'), 'cobalt': ('260500', '282200'),
             'tungsten': ('261100', '810194'), 'titanium': ('261400', '810820'), 'antimony': ('261710', '811010'),
             'bauxite': ('260600', '281820')}
CODES = sorted({c for pair in CROSSWALK.values() for c in pair})
EPS = 1e-9
REF_FLOOR = 0.03      # >=3% of world refined capability to count as a refiner
ORE_FLOOR = 0.03      # >=3% of world ore exports to count as a raw exporter

print(f'reading BACI HS17 {YEAR} bilateral (ore+refined flows only) ...', flush=True)
with zipfile.ZipFile(BACI_ZIP) as z:
    raw = pd.read_csv(io.TextIOWrapper(z.open(f'BACI_HS17_Y{YEAR}_V202601.csv'), encoding='utf-8'),
                      dtype={'k': str}, usecols=['i', 'j', 'k', 'v'])
raw = raw[raw.k.isin(CODES)].copy()
raw['v'] = pd.to_numeric(raw['v'], errors='coerce').fillna(0.0)      # thousand USD
exp = raw.groupby(['i', 'k']).v.sum(); imp = raw.groupby(['j', 'k']).v.sum()
def flow(tbl, c, code): return float(tbl.get((c, code), 0.0))

cc = pd.read_csv(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'))
num2iso = dict(zip(cc.country_code, cc.country_iso2)); num2name = dict(zip(cc.country_code, cc.country_name))
countries = sorted(set(raw.i) | set(raw.j))

d = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf-8'))
cur_ref = {m['label']: {x['c']: x['v'] for x in (m.get('refined') or [])} for m in d['materials']}
cur_mine = {m['label']: {x['c']: x['v'] for x in (m.get('mined') or [])} for m in d['materials']}

def classify(cap, phys_ref, phys_mine, basis, feed_imp, ore_share):
    if cap >= REF_FLOOR:
        if phys_mine >= 0.05 and phys_ref >= 0.05:      return 'integrated (mine+refine)'
        if basis.startswith('physical'):                 return 'domestic-absorbing refiner'
        if feed_imp >= 0.5:                              return 'import-fed refiner'
        return 'mine-to-metal refiner'
    if ore_share >= ORE_FLOOR:                           return 'raw exporter'
    return 'minor'

capability = {}
for lab, (ore, ref) in CROSSWALK.items():
    world_ref = sum(flow(exp, c, ref) for c in countries) + EPS
    world_ore = sum(flow(exp, c, ore) for c in countries) + EPS
    rows = []
    for c in countries:
        iso = num2iso.get(int(c)) if str(c).lstrip('-').isdigit() else None
        if not isinstance(iso, str):
            continue
        oi, oe = flow(imp, c, ore), flow(exp, c, ore)
        di, de = flow(imp, c, ref), flow(exp, c, ref)
        phys_ref = cur_ref.get(lab, {}).get(iso, 0.0) / 100.0
        phys_mine = cur_mine.get(lab, {}).get(iso, 0.0) / 100.0
        if (oi + oe + di + de) < 200 and phys_ref == 0:
            continue
        net_down = (de - di) / (de + di + EPS)
        feed_imp = oi / (oi + oe + EPS)
        ref_share = de / world_ref
        ore_share = oe / world_ore
        trade_score = ref_share * max(net_down, 0.0)
        cap = max(phys_ref, trade_score)
        if phys_ref > 0 and trade_score > 0:            basis = 'both'
        elif phys_ref > 2 * trade_score + 0.02:         basis = 'physical (domestic-absorbing)'
        elif trade_score > 0:                           basis = 'trade'
        else:                                           basis = '-'
        typ = classify(cap, phys_ref, phys_mine, basis, feed_imp, ore_share)
        if typ == 'minor':
            continue
        rows.append({'iso': iso, 'name': num2name.get(int(c), iso), 'cap': round(cap, 3), 'basis': basis,
                     'type': typ, 'phys_ref': round(phys_ref, 3), 'phys_mine': round(phys_mine, 3),
                     'trade_score': round(trade_score, 3), 'feed_import': round(feed_imp, 2),
                     'net_down': round(net_down, 2), 'ref_world_share': round(ref_share, 3),
                     'ore_world_share': round(ore_share, 3)})
    rows.sort(key=lambda r: -r['cap'])
    capability[lab] = rows

# ---------------- report ----------------
print('\n================  CAPABILITY MAP (trade signature x BGS/USGS)  ================\n')
resolved = 0
for lab, rows in capability.items():
    refs = [r for r in rows if r['cap'] >= REF_FLOOR]
    absorbers = [r for r in refs if r['type'] == 'domestic-absorbing refiner']
    print(f"### {lab.upper()}   ore {CROSSWALK[lab][0]} -> refined {CROSSWALK[lab][1]}")
    for r in refs[:6]:
        how = ('IMPORTS ore' if r['feed_import'] >= 0.5 else 'own ore') if 'refiner' in r['type'] else ''
        print(f"      {r['name'][:20]:20} cap {r['cap']:.2f}  [{r['type']}]"
              f"  basis={r['basis']:28} {how}")
    miners = [r for r in rows if r['type'] == 'raw exporter']
    if miners:
        print(f"    raw exporters: {', '.join(m['name'][:14] for m in miners[:5])}")
    if absorbers:
        resolved += 1
        print(f"    >> domestic-absorbing giant caught by physical data: "
              f"{', '.join(a['name'][:14] for a in absorbers)}")
    print()

print(f"fusion resolved a domestic-absorbing refiner (invisible to trade) in {resolved} materials")
json.dump(capability, open(os.path.join(ROOT, 'out', 'capability.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)
print('WROTE out/capability.json')

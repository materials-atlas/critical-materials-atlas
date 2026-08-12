"""Capability map: fuse the trade FEEDSTOCK SIGNATURE with BGS/USGS physical output, multi-year, and
extend to the downstream MAGNET stage. Turns the export map into a capability map.

Two fused lenses (see methodology memory):
  TRADE signature (BACI bilateral): net_down=(ref_exp-ref_imp)/(ref_exp+ref_imp) [>0 net exporter of
    refined]; feedstock_import=ore_imp/(ore_imp+ore_exp) [~1 sources ore by import];
    trade_score = ref_world_share * max(net_down,0)  -- robust positive, export-control-proof marker.
  PHYSICAL refined share (BGS/USGS, in data.json) -- catches the domestic-absorbing refiner (China
    copper/alumina/Ti sponge, Indonesia nickel) that refines a lot but consumes it, so exports zero.
  cap = max(physical_share, trade_score); basis records which lens carried it.

Stages: the 7 clean ore->refined pairs (fused w/ physical) + a MAGNET stage (REE metal/oxide ->
NdFeB magnet HS 850511) which is TRADE-ONLY (no physical magnet data) and flagged as such.

Outputs:  out/capability.json (latest year, for the map tooltip) and out/capability_years.json
          ({stage: {year: [rows]}}, 2018-2024, for the 'Who actually refines' page slider).
Run:  python build_feedstock.py
"""
import os, io, zipfile, json
import pandas as pd
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
BACI_ZIP = os.path.join(ROOT, 'raw', 'baci', 'BACI_HS17_V202601.zip')
YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024]
LATEST = 2023                      # most recent complete year -> capability.json + map tooltip
EPS = 1e-9
REF_FLOOR, ORE_FLOOR = 0.03, 0.03

CROSSWALK = {'copper': ('260300', '740311'), 'nickel': ('260400', '750210'), 'cobalt': ('260500', '282200'),
             'tungsten': ('261100', '810194'), 'titanium': ('261400', '810820'), 'antimony': ('261710', '811010'),
             'bauxite': ('260600', '281820')}
MAGNET_UP, MAGNET_DOWN = ['280530', '284690'], '850511'      # REE metal + oxide -> NdFeB magnet
CODES = sorted(set([c for pair in CROSSWALK.values() for c in pair] + MAGNET_UP + [MAGNET_DOWN]))

cc = pd.read_csv(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'))
num2iso = dict(zip(cc.country_code, cc.country_iso2)); num2name = dict(zip(cc.country_code, cc.country_name))
d = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf-8'))
cur_ref = {m['label']: {x['c']: x['v'] for x in (m.get('refined') or [])} for m in d['materials']}
cur_mine = {m['label']: {x['c']: x['v'] for x in (m.get('mined') or [])} for m in d['materials']}


def classify(cap, phys_ref, phys_mine, basis, feed_imp, ore_share, magnet=False):
    if magnet:
        if cap >= REF_FLOOR:
            return 'magnet maker · imports feedstock' if feed_imp >= 0.5 else 'magnet maker · integrated'
        if ore_share >= ORE_FLOOR:
            return 'feedstock exporter'
        return 'minor'
    if cap >= REF_FLOOR:
        if phys_mine >= 0.05 and phys_ref >= 0.05:  return 'integrated (mine+refine)'
        if basis.startswith('physical'):            return 'domestic-absorbing refiner'
        if feed_imp >= 0.5:                          return 'import-fed refiner'
        return 'mine-to-metal refiner'
    if ore_share >= ORE_FLOOR:                       return 'raw exporter'
    return 'minor'


def stage_rows(exp, imp, up_codes, down_code, phys_ref_d, phys_mine_d, magnet=False):
    def fexp(c, code): return float(exp.get((c, code), 0.0))
    def fimp(c, code): return float(imp.get((c, code), 0.0))
    countries = sorted({c for (c, _) in exp.index} | {c for (c, _) in imp.index})
    world_ref = sum(fexp(c, down_code) for c in countries) + EPS
    world_ore = sum(sum(fexp(c, u) for u in up_codes) for c in countries) + EPS
    rows = []
    for c in countries:
        iso = num2iso.get(int(c)) if str(c).lstrip('-').isdigit() else None
        if not isinstance(iso, str):
            continue
        oi = sum(fimp(c, u) for u in up_codes); oe = sum(fexp(c, u) for u in up_codes)
        di, de = fimp(c, down_code), fexp(c, down_code)
        phys_ref = (phys_ref_d or {}).get(iso, 0.0) / 100.0
        phys_mine = (phys_mine_d or {}).get(iso, 0.0) / 100.0
        if (oi + oe + di + de) < 200 and phys_ref == 0:
            continue
        net_down = (de - di) / (de + di + EPS)
        feed_imp = oi / (oi + oe + EPS)
        ref_share, ore_share = de / world_ref, oe / world_ore
        trade_score = ref_share * max(net_down, 0.0)
        cap = max(phys_ref, trade_score)
        if phys_ref > 0 and trade_score > 0:        basis = 'both'
        elif phys_ref > 2 * trade_score + 0.02:     basis = 'physical (domestic-absorbing)'
        elif trade_score > 0:                       basis = 'trade'
        else:                                       basis = '-'
        typ = classify(cap, phys_ref, phys_mine, basis, feed_imp, ore_share, magnet)
        if typ == 'minor':
            continue
        rows.append({'iso': iso, 'name': num2name.get(int(c), iso), 'cap': round(cap, 3), 'basis': basis,
                     'type': typ, 'phys_ref': round(phys_ref, 3), 'phys_mine': round(phys_mine, 3),
                     'trade_score': round(trade_score, 3), 'feed_import': round(feed_imp, 2),
                     'net_down': round(net_down, 2), 'ref_world_share': round(ref_share, 3),
                     'ore_world_share': round(ore_share, 3)})
    rows.sort(key=lambda r: -r['cap'])
    return rows[:20]


def compute_year(year):
    with zipfile.ZipFile(BACI_ZIP) as z:
        raw = pd.read_csv(io.TextIOWrapper(z.open(f'BACI_HS17_Y{year}_V202601.csv'), encoding='utf-8'),
                          dtype={'k': str}, usecols=['i', 'j', 'k', 'v'])
    raw = raw[raw.k.isin(CODES)].copy()
    raw['v'] = pd.to_numeric(raw['v'], errors='coerce').fillna(0.0)
    exp = raw.groupby(['i', 'k']).v.sum(); imp = raw.groupby(['j', 'k']).v.sum()
    out = {}
    for lab, (ore, ref) in CROSSWALK.items():
        out[lab] = stage_rows(exp, imp, [ore], ref, cur_ref.get(lab), cur_mine.get(lab))
    out['magnet (NdFeB)'] = stage_rows(exp, imp, MAGNET_UP, MAGNET_DOWN, None, None, magnet=True)
    return out


years_out = {}
for y in YEARS:
    print(f'computing capability {y} ...', flush=True)
    cap_y = compute_year(y)
    for stage, rows in cap_y.items():
        years_out.setdefault(stage, {})[str(y)] = rows

json.dump({'years': YEARS, 'latest': LATEST, 'stages': years_out},
          open(os.path.join(ROOT, 'out', 'capability_years.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)
json.dump({stage: yr[str(LATEST)] for stage, yr in years_out.items()},
          open(os.path.join(ROOT, 'out', 'capability.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)
print(f'\nWROTE out/capability_years.json ({len(YEARS)} yrs) + out/capability.json (latest {LATEST})')
# quick sanity print for the latest year
for stage, rows in {s: yr[str(LATEST)] for s, yr in years_out.items()}.items():
    top = ', '.join(f"{r['name'][:12]}({r['cap']:.2f},{r['type'].split()[0]})" for r in rows[:4])
    print(f"  {stage:16} {top}")

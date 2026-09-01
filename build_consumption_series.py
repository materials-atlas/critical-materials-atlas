#!/usr/bin/env python3
"""Time-series consumption (v1, fixed-intensity): apply the 2023-calibrated intensities to each year's
activity, so the matrix can be watched evolving 2000 -> 2023. demand(country,material,year) =
sum_drivers activity(country,driver,year) x intensity_2023(material,driver).

WHY fixed intensity: it isolates ACTIVITY-driven change (who does more steel / builds more EVs) and the
shifting country distribution -- the story a production map can't show. It does NOT capture intensity change
(thrifting: less cobalt per battery over time; substitution; brand-new end-uses). Stated honestly on the page.
A v2 would re-scale each year to that year's known world consumption (USGS annual totals) to fix the levels.

Only materials whose end-use drivers are ALL present in the historical activity file get a series (the broad-
driver set: steel family, battery metals, copper/silver, PGM). Specialty materials whose drivers (semi, aero,
aluminium, fertp, glass, drilling...) lack a back-series are left out of the time series and stay single-year
on the main consumption page. Intensities + shares are read from consumption.json (single source of truth).

Reads raw/activity/drivers_history.csv (iso3,country,driver,year,value[,source]) with WLD rows for world
totals. Run: python build_consumption_series.py -> out/consumption_series.json
"""
import csv, json, os
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
cj = json.load(open(os.path.join(ROOT, 'out', 'consumption.json'), encoding='utf-8'))
SHARES = cj['end_use_shares']; KNOWN = cj['known_world']
WORLD23 = {d: cj['drivers'][d]['world'] for d in cj['drivers']}
# 2023-calibrated intensity (tonnes of material per driver-unit)
intensity = {}
for m, sh in SHARES.items():
    for d, s in sh.items():
        if WORLD23.get(d):
            intensity[(m, d)] = KNOWN[m] * s / WORLD23[d]

hist = os.path.join(ROOT, 'raw', 'activity', 'drivers_history.csv')
if not os.path.exists(hist):
    print('NOTE: raw/activity/drivers_history.csv not present yet — waiting on the historical activity data.')
    raise SystemExit

# benchmark activity: BM[(iso,driver)] = {year: value}
BM = defaultdict(dict); NAME = {}; HISTDRV = set(); BYEARS = set()
for r in csv.DictReader(open(hist, encoding='utf-8')):
    try: y = int(r['year']); v = float(r['value'])
    except (ValueError, KeyError): continue
    d = r['driver'].strip(); iso = r['iso3'].strip()
    HISTDRV.add(d); BYEARS.add(y)
    if iso == 'WLD': continue
    BM[(iso, d)][y] = v
    NAME[iso] = r.get('country', iso)
BYEARS = sorted(BYEARS)

def interp(bmv, y):
    """piecewise-linear value at year y from a {year: value} dict (flat outside the known range)."""
    ys = sorted(bmv)
    if not ys: return 0.0
    if y <= ys[0]: return bmv[ys[0]]
    if y >= ys[-1]: return bmv[ys[-1]]
    for a, b in zip(ys, ys[1:]):
        if a <= y <= b: return bmv[a] + (bmv[b]-bmv[a]) * (y-a)/(b-a)
    return bmv[ys[-1]]

# DENSIFY: every year between the first and last benchmark; intermediate years interpolated.
YEARS = list(range(BYEARS[0], BYEARS[-1]+1))
series_mats = [m for m in cj['materials'] if SHARES[m] and all(d in HISTDRV for d in SHARES[m])]
isos = sorted({iso for (iso, d) in BM})

# v1 fixed-intensity demand
demand = {y: {} for y in YEARS}
for y in YEARS:
    for iso in isos:
        acts = {d: interp(BM[(iso, d)], y) for d in HISTDRV if (iso, d) in BM}
        cell = {m: sum(acts.get(d, 0) * intensity.get((m, d), 0) for d in SHARES[m]) for m in series_mats}
        cell = {m: v for m, v in cell.items() if v > 0}
        if cell: demand[y][iso] = cell

# v2 RE-CALIBRATION: rescale each material's LEVEL to the real world-consumption trend, anchored so the
# 2023 slice stays at its (already calibrated) v1 value. scale(m,y) = [W(m,y)/W(m,2023)] / [v1sum(m,y)/v1sum(m,2023)]
WC = defaultdict(dict); wcpath = os.path.join(ROOT, 'raw', 'activity', 'world_consumption.csv')
if os.path.exists(wcpath):
    for r in csv.DictReader(open(wcpath, encoding='utf-8')):
        try: WC[r['material']][int(r['year'])] = float(r['world_tonnes'])
        except (ValueError, KeyError): continue
anchor = BYEARS[-1]
v1sum = {(m, y): sum(demand[y].get(i, {}).get(m, 0) for i in demand[y]) for m in series_mats for y in YEARS}
recal = []
for m in series_mats:
    if m in WC and WC[m].get(anchor) and v1sum.get((m, anchor)):
        recal.append(m)
        for y in YEARS:
            wy, wa = interp(WC[m], y), WC[m][anchor] if anchor in WC[m] else interp(WC[m], anchor)
            v1y, v1a = v1sum[(m, y)], v1sum[(m, anchor)]
            if wa and v1y and v1a:
                sc = (wy/wa) / (v1y/v1a)
                for i in demand[y]:
                    if m in demand[y][i]: demand[y][i][m] *= sc

series = {y: {i: {m: round(v) for m, v in demand[y][i].items() if v >= 1} for i in demand[y] if demand[y][i]} for y in YEARS}
out = {'note': ('Time series 2000-2023. v1 = 2023-calibrated intensities x each year’s activity (intermediate '
                'years interpolated between 2000/2010/2023 benchmarks). v2 re-calibration then rescales each '
                'material’s LEVEL to the real world-consumption trend (USGS/IEA), anchored so 2023 = the '
                'calibrated value. Shows activity-driven distribution + real level trend; does NOT model '
                'thrifting/substitution. Broad-driver materials only.'),
       'years': YEARS, 'materials': series_mats, 'recalibrated': recal, 'names': NAME, 'series': series}
json.dump(out, open(os.path.join(ROOT, 'out', 'consumption_series.json'), 'w', encoding='utf-8'), indent=1)
show = [y for y in YEARS if y in BYEARS]
print(f"{len(YEARS)} years ({YEARS[0]}-{YEARS[-1]}) | {len(series_mats)} materials | {len(recal)} v2-recalibrated | drivers {sorted(HISTDRV)}")
print(f"{'material':12}" + ''.join(f'{y:>10}' for y in show))
for m in series_mats:
    print(f"{m:12}" + ''.join(f'{sum(series[y].get(i,{}).get(m,0) for i in series[y])/1e6:>9.2f}M' for y in show))
print('wrote out/consumption_series.json')

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

# activity points per (iso,driver) = {year: value}. Two sources, real-annual PREFERRED over benchmarks:
#   drivers_annual.csv  -> real annual 2000-2024 (elec, pop, nuclear, solar, wind from OWID/Ember; fertp from FAOSTAT)
#   drivers_history.csv -> 3 benchmark years (2000/2010/2023) for the rest (steel, veh, ev, cement, ...)
PTS = defaultdict(dict); NAME = {}; HISTDRV = set(); ANNUAL_DRV = set()
for r in csv.DictReader(open(hist, encoding='utf-8')):    # benchmarks first
    try: y = int(r['year']); v = float(r['value'])
    except (ValueError, KeyError): continue
    d = r['driver'].strip(); iso = r['iso3'].strip(); HISTDRV.add(d)
    if iso == 'WLD': continue
    PTS[(iso, d)][y] = v; NAME[iso] = r.get('country', iso)
annf = os.path.join(ROOT, 'raw', 'activity', 'drivers_annual.csv')
if os.path.exists(annf):
    for r in csv.DictReader(open(annf, encoding='utf-8')):
        try: y = int(r['year']); v = float(r['value'])
        except (ValueError, KeyError): continue
        d = r['driver'].strip(); iso = r['iso3'].strip(); HISTDRV.add(d); ANNUAL_DRV.add(d)
        if iso == 'WLD': continue
        PTS[(iso, d)][y] = v; NAME.setdefault(iso, r.get('country', iso))  # overwrites benchmark year, adds the rest

def interp(pv, y):
    """piecewise-linear value at year y from a {year: value} dict (flat outside the known range)."""
    ys = sorted(pv)
    if not ys: return 0.0
    if y <= ys[0]: return pv[ys[0]]
    if y >= ys[-1]: return pv[ys[-1]]
    for a, b in zip(ys, ys[1:]):
        if a <= y <= b: return pv[a] + (pv[b]-pv[a]) * (y-a)/(b-a)
    return pv[ys[-1]]

YEARS = list(range(2000, 2025))            # 2000-2024 (real-annual drivers reach 2024; benchmark drivers held flat past 2023)
series_mats = [m for m in cj['materials'] if SHARES[m] and all(d in HISTDRV for d in SHARES[m])]
# per material: fraction of its end-use share carried by REAL-ANNUAL drivers (how 'real' the trend is)
real_frac = {m: round(sum(s for d, s in SHARES[m].items() if d in ANNUAL_DRV) / sum(SHARES[m].values()), 2)
             for m in series_mats}
isos = sorted({iso for (iso, d) in PTS})

demand = {y: {} for y in YEARS}
for y in YEARS:
    for iso in isos:
        acts = {d: interp(PTS[(iso, d)], y) for d in HISTDRV if (iso, d) in PTS}
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
anchor = 2023   # the calibration year; series levels are pinned here
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
out = {'note': ('Time series 2000-2024. Each country-share comes from activity; each material-level is rescaled '
                'to the real world-consumption trend (v2), pinned so 2023 = the calibrated value. Drivers are '
                'REAL ANNUAL where available (electricity, population, nuclear, solar, wind from OWID/Ember; '
                'fertilizer from FAOSTAT) and 3-benchmark-interpolated (2000/2010/2023) otherwise (steel, '
                'vehicles, EVs, cement, aluminium, lead, glass, semiconductors, aerospace, drilling). Each '
                'material carries real_frac = the share of its demand carried by real-annual drivers. Does NOT '
                'model thrifting/substitution.'),
       'annual_drivers': sorted(ANNUAL_DRV), 'years': YEARS, 'materials': series_mats,
       'recalibrated': recal, 'real_frac': real_frac, 'names': NAME, 'series': series}
json.dump(out, open(os.path.join(ROOT, 'out', 'consumption_series.json'), 'w', encoding='utf-8'), indent=1)
show = [2000, 2010, 2020, 2023, 2024]
print(f"{len(YEARS)} years ({YEARS[0]}-{YEARS[-1]}) | {len(series_mats)} materials | real-annual drivers {sorted(ANNUAL_DRV)}")
print(f"{'material':12}{'real%':>6}" + ''.join(f'{y:>10}' for y in show))
for m in series_mats:
    print(f"{m:12}{real_frac[m]*100:>5.0f}%" + ''.join(f'{sum(series[y].get(i,{}).get(m,0) for i in series[y])/1e6:>9.2f}M' for y in show))
print('wrote out/consumption_series.json')

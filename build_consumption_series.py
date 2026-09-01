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

ACT = defaultdict(lambda: defaultdict(dict))   # ACT[year][iso][driver]
NAME = {}; HISTDRV = set(); YEARS = set()
for r in csv.DictReader(open(hist, encoding='utf-8')):
    try: y = int(r['year']); v = float(r['value'])
    except (ValueError, KeyError): continue
    d = r['driver'].strip(); iso = r['iso3'].strip()
    HISTDRV.add(d); YEARS.add(y)
    if iso == 'WLD': continue
    ACT[y][iso][d] = v
    NAME[iso] = r.get('country', iso)
YEARS = sorted(YEARS)

# a material gets a series only if ALL its end-use drivers have a back-series (keeps capture honest)
series_mats = [m for m in cj['materials'] if SHARES[m] and all(d in HISTDRV for d in SHARES[m])]

series = {}
for y in YEARS:
    ymat = {}
    for iso, acts in ACT[y].items():
        cell = {}
        for m in series_mats:
            t = sum(acts.get(d, 0) * intensity.get((m, d), 0) for d in SHARES[m])
            if t > 0: cell[m] = round(t)
        if cell: ymat[iso] = cell
    series[y] = ymat

out = {'note': ('Fixed-intensity time series: 2023-calibrated intensities applied to each year’s activity. '
                'Shows activity-driven consumption growth and the shifting country distribution; does NOT model '
                'thrifting/substitution/new intensities. Broad-driver materials only.'),
       'years': YEARS, 'materials': series_mats, 'names': NAME, 'series': series}
json.dump(out, open(os.path.join(ROOT, 'out', 'consumption_series.json'), 'w', encoding='utf-8'), indent=1)
# quick report: world sum per material per year (Mt), to eyeball the trend
print(f"years {YEARS} | {len(series_mats)} series-able materials | drivers in history: {sorted(HISTDRV)}")
print(f"{'material':12}" + ''.join(f'{y:>12}' for y in YEARS))
for m in series_mats:
    tot = {y: sum(series[y][i].get(m, 0) for i in series[y]) for y in YEARS}
    print(f"{m:12}" + ''.join(f'{tot[y]/1e6:>11.2f}M' for y in YEARS))
print('wrote out/consumption_series.json')

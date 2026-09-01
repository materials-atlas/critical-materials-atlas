#!/usr/bin/env python3
"""Trade-INDEPENDENT consumption estimate:  demand(country, material) = sum_uses( activity x material-intensity ).
This is the input the production-constrained anchor needs -- a consumption figure NOT derived from trade, so it
can be used to check and correct the trade data instead of circularly depending on it.

Intensities are SELF-CALIBRATING: rather than guess a kg/unit, each driver's intensity is back-solved from a
known world total, so world sums can't drift and every cell is a country's real activity x a calibrated
intensity:
    intensity(m,driver) = KNOWN_WORLD[m] * end_use_share(m,driver) / WORLD_TOTAL[driver]
    demand(c,m)         = sum_driver activity(c,driver) * intensity(m,driver)
=> world sum of demand = KNOWN_WORLD[m] * (covered end-use share) * (covered country share)  -- an HONEST
   'capture ratio' <= 1; it is never inflated to force a fit. A cell reads ~0 where a country has no activity
   in a material's drivers (a genuine non-consumer), which is exactly what the anchor wants.

Activity = authoritative 2023 data in raw/activity/drivers.csv (worldsteel, OICA, IEA GEVO, Ember, IRENA,
USGS, UN). End-use shares curated from USGS MCS + EU CRM/JRC. This is an ESTIMATE layer (order-of-magnitude
intensities, partial end-use capture for multi-use metals) -- surfaced with a per-material capture ratio so a
reader sees exactly how much of world demand each column accounts for. Run: python build_consumption.py
"""
import csv, json, os
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
DRIVERS = ['steel', 'veh', 'ev', 'elec', 'solar', 'wind', 'cement', 'pop']
SHARES = {   # material -> {driver: fraction of world demand attributable to that activity}
 'manganese':  {'steel': 0.90}, 'chromium': {'steel': 0.85},
 'nickel':     {'steel': 0.66, 'ev': 0.12}, 'molybdenum': {'steel': 0.80},
 'vanadium':   {'steel': 0.90}, 'niobium': {'steel': 0.90}, 'tungsten': {'steel': 0.60},
 'silicon':    {'steel': 0.55, 'solar': 0.10}, 'cokingcoal': {'steel': 0.90},
 'lithium':    {'ev': 0.74}, 'cobalt': {'ev': 0.40}, 'graphite': {'ev': 0.35, 'steel': 0.25},
 'copper':     {'elec': 0.28, 'ev': 0.10, 'solar': 0.06, 'wind': 0.05, 'veh': 0.12, 'cement': 0.20},
 'silver':     {'solar': 0.14, 'veh': 0.05, 'elec': 0.20}, 'rareearths': {'ev': 0.15, 'wind': 0.14},
 'platinum':   {'veh': 0.40}, 'palladium': {'veh': 0.80}, 'phosphate': {'pop': 0.90},
}
KNOWN = {  # ~world annual consumption (t), USGS/industry order-of-magnitude (calibration target)
 'manganese':20_000_000,'chromium':40_000_000,'nickel':3_300_000,'molybdenum':300_000,'vanadium':110_000,
 'niobium':83_000,'tungsten':110_000,'silicon':3_500_000,'cokingcoal':1_100_000_000,'lithium':180_000,
 'cobalt':220_000,'graphite':4_000_000,'copper':26_000_000,'silver':35_000,'rareearths':180_000,
 'platinum':230,'palladium':270,'phosphate':220_000_000,
}

ACT = defaultdict(dict); HEADLINE = {}; CSUM = defaultdict(float); NAME = {}; SRC = {}
for r in csv.DictReader(open(os.path.join(ROOT, 'raw', 'activity', 'drivers.csv'), encoding='utf-8')):
    iso, drv = r['iso3'].strip(), r['driver'].strip()
    try: v = float(r['value'])
    except ValueError: continue
    SRC[drv] = r.get('source', '')
    if iso == 'WLD': HEADLINE[drv] = v
    else: ACT[iso][drv] = v; CSUM[drv] += v; NAME[iso] = r.get('country', iso)
WORLD = {d: max(HEADLINE.get(d, 0), CSUM[d]) for d in DRIVERS if d in CSUM}

intensity = {}
for m, sh in SHARES.items():
    for d, s in sh.items():
        if WORLD.get(d): intensity[(m, d)] = KNOWN[m] * s / WORLD[d]

mats = list(SHARES.keys())
matrix = {}
for iso, acts in ACT.items():
    cell = {}
    for m in mats:
        tot = sum(acts.get(d, 0) * intensity.get((m, d), 0) for d in SHARES[m])
        cov = any(d in acts and (m, d) in intensity for d in SHARES[m])
        cell[m] = {'t': round(tot), 'basis': 'calibrated' if cov else 'none'}
    matrix[iso] = {'name': NAME.get(iso, iso), 'demand': cell}

world_sum = {m: sum(matrix[i]['demand'][m]['t'] for i in matrix) for m in mats}
capture = {m: round(world_sum[m] / KNOWN[m], 3) if KNOWN.get(m) else 0 for m in mats}
ncountry = sum(1 for i in matrix if any(matrix[i]['demand'][m]['basis'] == 'calibrated' for m in mats))
out = {'note': ('Trade-independent consumption estimate (activity x calibrated intensity). Intensities are '
                'back-solved from known world totals; the per-material capture ratio is the honest share of '
                'world demand these drivers+countries account for (<=1, never inflated). ESTIMATE layer.'),
       'drivers': {d: {'world': WORLD[d], 'source': SRC.get(d, '')} for d in WORLD},
       'end_use_shares': SHARES, 'known_world': KNOWN, 'capture': capture,
       'n_countries': ncountry, 'materials': mats, 'matrix': matrix}
json.dump(out, open(os.path.join(ROOT, 'out', 'consumption.json'), 'w', encoding='utf-8'), indent=1)
print(f"{'material':13}{'world sum t':>15}{'capture':>9}")
for m in mats: print(f"{m:13}{world_sum[m]:>15,.0f}{capture[m]:>9.2f}")
print(f"\n{ncountry} countries with >=1 calibrated cell. wrote out/consumption.json")

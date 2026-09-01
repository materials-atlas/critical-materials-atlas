#!/usr/bin/env python3
"""Platinum-group metals, end to end — the geological chokepoint. Third material deep-dive, and a
deliberate CONTRAST to gallium and cobalt. Those are by-products you cannot scale because they ride a
host; the PGMs are the opposite failure mode — a chokepoint that IS the mine, because the deposit cannot
be relocated or substituted. Two facts make it the sharpest 'geological' case on the atlas:

  1. Concentration by geology, not capability: one ore body, South Africa's Bushveld Complex, holds the
     large majority of world PGM reserves; South Africa leads platinum mine supply (~70%) and Russia's
     Norilsk leads palladium (~41%). You cannot build a second Bushveld.
  2. The co-production LOCK: platinum, palladium and rhodium come out of the SAME ore in a ratio the
     rock fixes. So a shortage of ONE (rhodium spiked above $20,000/oz in 2021) cannot be answered by
     'mining more rhodium' — there is no rhodium mine; you mine the whole basket, from the same two
     countries, or none. Demand for one metal is capped by the geology of the others.

The response is therefore not 'build capacity elsewhere' (there is nowhere else) but substitution within
the basket (which moves nothing — see the substitution page), recycling spent autocatalysts (~a quarter
of supply), and stockpiling. Public data + stated constants. Run: python build_pgm.py -> out/pgm.json
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
prod = {r['label']: r for r in json.load(open(os.path.join(ROOT, 'out', 'production.json'), encoding='utf8'))['rows']}

PT_SA = round(prod['platinum']['wmd_top_share']) if prod.get('platinum') else 70   # South Africa, platinum
PD_RU = round(prod['palladium']['wmd_top_share']) if prod.get('palladium') else 41  # Russia, palladium

# stated constants (with ranges) — literature (USGS MCS PGM, Johnson Matthey PGM Market Report)
RESERVES_SA = {'low': 70, 'central': 90, 'high': 91}       # South Africa share of world PGM reserves (USGS)
# mine split of PGM output by mass (Johnson Matthey; Bushveld is Pt-rich, Norilsk Pd-rich -> global mix)
SPLIT = {'platinum': 38, 'palladium': 39, 'rhodium': 8, 'other (Ru/Ir/Os)': 15}
AUTOCAT = {'low': 60, 'central': 68, 'high': 80}           # share of PGM demand in autocatalysts
RECYCLE = {'low': 22, 'central': 27, 'high': 30}           # share of PGM supply from recycled autocatalysts
RH_PEAK_USD = 29800                                        # rhodium price peak, 2021 (Johnson Matthey)

steps = [
    {'label': 'One geological basket (South Africa + Russia)', 'tonnes': 100, 'lo': 100, 'hi': 100,
     'note': f'South Africa ~{PT_SA}% of platinum, Russia ~{PD_RU}% of palladium — {RESERVES_SA["central"]}% of reserves in one complex'},
    {'label': 'Split by the ore, not by demand', 'tonnes': 85, 'lo': 78, 'hi': 92,
     'note': f'Pt {SPLIT["platinum"]}% · Pd {SPLIT["palladium"]}% · Rh {SPLIT["rhodium"]}% — a ratio geology fixes'},
    {'label': 'Into autocatalysts', 'tonnes': AUTOCAT['central'], 'lo': AUTOCAT['low'], 'hi': AUTOCAT['high'],
     'note': f"~{AUTOCAT['central']}% of demand cleans vehicle exhaust — plus hydrogen, jewellery"},
    {'label': 'Recovered from spent catalysts', 'tonnes': RECYCLE['central'], 'lo': RECYCLE['low'], 'hi': RECYCLE['high'],
     'note': f"~{RECYCLE['central']}% of supply is recycled — the one lever that adds metal without new geology"},
]

S = {
    'pt_sa_share': PT_SA, 'pd_ru_share': PD_RU, 'reserves_sa': RESERVES_SA,
    'split': SPLIT, 'autocat': AUTOCAT, 'recycle': RECYCLE, 'rh_peak_usd': RH_PEAK_USD,
    'steps': steps,
}
json.dump(S, open(os.path.join(ROOT, 'out', 'pgm.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(f"PGM: platinum SA ~{PT_SA}%, palladium Russia ~{PD_RU}%, reserves SA ~{RESERVES_SA['central']}%")
print(f"split Pt {SPLIT['platinum']}/Pd {SPLIT['palladium']}/Rh {SPLIT['rhodium']} | autocat ~{AUTOCAT['central']}% | recycle ~{RECYCLE['central']}%")
print("wrote out/pgm.json")

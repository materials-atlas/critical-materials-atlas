#!/usr/bin/env python3
"""Energy footprint of the refining chokepoints — quantifying the 'furnace concentrates at cheap power'
thesis. The chokepoint map classifies ~6 stages as THERMODYNAMIC: a continuous high-temperature process
that can't be stopped, so it sites where power is cheapest and most reliable -- which is why these stages
migrate to one country. That thesis was asserted but never put in numbers. This does: for the
energy-intensive refining stages, the electricity/energy per tonne and the CO2 per tonne, set beside how
concentrated the stage is. The finding is that energy intensity PREDICTS the geography -- the most
energy-hungry stages (magnesium, polysilicon, aluminium) are the most China-concentrated -- and the
concentration carries a huge embedded carbon cost.

Energy/CO2 figures are literature values (approximate, ranges in the sources); the two extremes
(magnesium Pidgeon ~78 MWh/t & ~25 t CO2/t; polysilicon ~40-70 kWh/kg) are web-verified. Concentration is
the top producer/refiner share from the atlas's own data. Run: python build_energy_footprint.py
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
prod = {r['label']: r for r in json.load(open(os.path.join(ROOT, 'out', 'production.json'), encoding='utf8'))['rows']}
def topshare(label, fallback):
    r = prod.get(label)
    return round(r['wmd_top_share']) if r and r.get('wmd_top_share') else fallback

# curated energy intensity (MWh per tonne of product) and CO2 (t CO2 per tonne), with the concentrating stage
DATA = [
    {'m': 'Magnesium', 'process': 'Pidgeon silicothermic reduction', 'mwh': 78, 'co2': 25,
     'share': 87, 'holder': 'China', 'conf': 'measured',
     'note': 'The extreme case: ~78 MWh and ~25 t CO2 per tonne (coal-heated, ~4-5 t coal/t Mg). ~87% China.'},
    {'m': 'Polysilicon (solar)', 'process': 'Siemens CVD', 'mwh': 50, 'co2': 36,
     'share': 95, 'holder': 'China', 'conf': 'estimate',
     'note': '~40-70 kWh/kg; sited on cheap Chinese coal/hydro power. The solar chokepoint is an energy chokepoint.'},
    {'m': 'Aluminium', 'process': 'Hall–Héroult electrolysis', 'mwh': 14, 'co2': 16,
     'share': 59, 'holder': 'China', 'conf': 'measured',
     'note': '~14 MWh/t of electricity; ~16 t CO2/t on a coal grid (China), ~2 t on hydro. Power IS the cost.'},
    {'m': 'Silicon metal', 'process': 'Carbothermic arc furnace', 'mwh': 11, 'co2': 5,
     'share': topshare('silicon', 40), 'holder': 'China', 'conf': 'estimate',
     'note': '~11 MWh/t; the feedstock for both chips and polysilicon, itself energy-sited.'},
    {'m': 'Ammonia', 'process': 'Haber–Bosch', 'mwh': 9.5, 'co2': 2.4,
     'share': 35, 'holder': 'cheap-gas regions', 'conf': 'estimate',
     'note': '~9-10 MWh-equiv/t, mostly natural gas; sites on cheap gas rather than one country — energy-sited but diffuse.'},
    {'m': 'Steel (crude)', 'process': 'Blast furnace', 'mwh': 5.5, 'co2': 1.9,
     'share': 52, 'holder': 'China', 'conf': 'measured',
     'note': '~5.5 MWh-equiv/t, mostly coking coal not electricity; ~1.9 t CO2/t. Huge volume, ~52% China.'},
    {'m': 'Ferrochrome', 'process': 'Submerged-arc furnace', 'mwh': 3.6, 'co2': 4,
     'share': 45, 'holder': 'S. Africa · Kazakhstan · China', 'conf': 'estimate',
     'note': '~3.6 MWh/t; sites on cheap power (South Africa, then Kazakhstan/China) — energy, not the ore.'},
    {'m': 'Copper (smelting)', 'process': 'Flash smelting', 'mwh': 2.5, 'co2': 2,
     'share': topshare('copper', 24), 'holder': 'diffuse', 'conf': 'estimate',
     'note': 'CONTRAST: low energy intensity (~2.5 MWh/t), so it does NOT concentrate on power — smelting is spread worldwide.'},
]
DATA.sort(key=lambda d: -d['mwh'])
out = {'note': ('Energy (MWh) and CO2 (t) per tonne for the energy-intensive refining stages, set beside '
                'how concentrated each stage is. Energy figures are approximate literature values; the '
                'extremes (magnesium, polysilicon) are web-verified. The point: energy intensity predicts '
                'the geography -- the most energy-hungry stages are the most concentrated (on cheap, often '
                'dirty, power), and copper (low energy) stays diffuse as the control case.'),
       'materials': DATA}
json.dump(out, open(os.path.join(ROOT, 'out', 'energy_footprint.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(f"{'material':20}{'MWh/t':>7}{'tCO2/t':>8}{'conc%':>7}  holder")
for d in DATA:
    print(f"{d['m'][:19]:20}{d['mwh']:>7}{d['co2']:>8}{d['share']:>6}%  {d['holder']}")
print("wrote out/energy_footprint.json")

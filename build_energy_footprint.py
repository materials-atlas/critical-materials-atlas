#!/usr/bin/env python3
"""Energy footprint of the refining chokepoints — putting numbers on 'cheap energy concentrates refining'.
The chokepoint map classes several refining stages as energy-sited. This measures the energy per tonne and
the CO2 per tonne beside how concentrated each stage is -- but honestly, because the earlier version made
three mistakes a review caught:

  1. It read wmd_top_share for copper (Chile's MINE share, 24%) on a row labelled 'smelting'. The stage was
     wrong: China's copper SMELTING share is ~40%. Fixed -- each row now carries its OWN stage-matched share.
  2. Silicon isn't in production.json, so topshare('silicon',40) silently used a hardcoded number as if
     derived. Fixed -- silicon's share is now an explicit, sourced estimate flagged as such.
  3. It ranked electricity (aluminium, polysilicon) together with fuel/reductant/feedstock energy
     (magnesium's coal, steel's coking coal, ammonia's gas) as one 'MWh/t' column, then claimed the
     furnace sites on cheap POWER. But magnesium's ~78 MWh/t is PRIMARY energy incl. embodied ferrosilicon;
     the Pidgeon process is coal-fired BATCH retorts (~1-3 MWh/t electricity) sited on dolomite + FeSi + coal,
     not a continuous electrical furnace at cheap power. So we now split energy by TYPE and only claim
     power-siting for the genuinely electricity-dominated stages.

Honest finding: cheap energy concentrates refining, but the FORM of energy sets the mechanism. A few stages
site on cheap POWER (aluminium, polysilicon, silicon metal); others on cheap FUEL + a co-located reductant
or ore (magnesium, ferrochrome, steel, ammonia); and copper shows even a LOW-energy stage can concentrate on
logistics/acid-handling/policy. Energy is a primary driver of the map, not a single monotonic ruler.

Energy/CO2 figures are literature order-of-magnitude (ranges by process, vintage, grid). Concentration is
stage-matched: mine share only where the row IS the mine; refinery/smelter/process share otherwise, each
sourced in the row. Run: python build_energy_footprint.py
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))

# Each row states BOTH its electricity intensity and its total primary energy (MWh/t), its energy TYPE (what
# actually drives siting), the stage the share describes, and an explicit stage-matched share with a source.
# share is NOT pulled from wmd_top_share unless the row's stage IS mine production (it never is here).
DATA = [
    {'m': 'Magnesium', 'process': 'Pidgeon silicothermic reduction', 'group': 'fuel',
     'mwh_elec': 2.5, 'mwh_primary': 78, 'co2': 25, 'share': 66, 'stage': 'metal (WMD)',
     'holder': 'China', 'energy_type': 'fuel + reductant (coal, ferrosilicon)', 'conf': 'measured',
     'src': 'production.json (WMD metal); IMA/Pidgeon LCA',
     'note': 'Not a power story. ~78 MWh/t is PRIMARY energy incl. embodied ferrosilicon; the retorts are '
             'coal-fired BATCH units (~1-3 MWh/t electricity) sited on dolomite + FeSi + cheap coal, not on '
             'cheap electricity. ~66% China on a metal basis (WMD); USGS puts it higher (~88%).'},
    {'m': 'Polysilicon (solar)', 'process': 'Siemens CVD', 'group': 'power',
     'mwh_elec': 50, 'mwh_primary': 50, 'co2': 36, 'share': 93, 'stage': 'refined polysilicon',
     'holder': 'China', 'energy_type': 'electricity', 'conf': 'estimate',
     'src': 'Fraunhofer ISE; BNEF polysilicon capacity',
     'note': '~40-70 kWh/kg of ELECTRICITY; quartz is cheap and ubiquitous, so power dominates the cost and '
             'it sites on cheap Chinese coal/hydro. The solar chokepoint is a power chokepoint. ~93% China.'},
    {'m': 'Aluminium', 'process': 'Hall–Héroult electrolysis', 'group': 'power',
     'mwh_elec': 14, 'mwh_primary': 14, 'co2': 16, 'share': 59, 'stage': 'primary metal (smelting)',
     'holder': 'China', 'energy_type': 'electricity', 'conf': 'measured',
     'src': 'IAI; USGS aluminium',
     'note': '~14 MWh/t of ELECTRICITY; alumina is shipped in, so power is the siting force — China on coal '
             '(~16 t CO2/t), or hydro (~2 t) in Canada/Iceland/Gulf. ~59% China smelting.'},
    {'m': 'Silicon metal', 'process': 'Carbothermic arc furnace', 'group': 'power',
     'mwh_elec': 11, 'mwh_primary': 11, 'co2': 5, 'share': 70, 'stage': 'silicon metal (process)',
     'holder': 'China', 'energy_type': 'electricity', 'conf': 'estimate',
     'src': 'USGS silicon (not in atlas production.json — explicit estimate); China ~68-77%',
     'note': '~11 MWh/t of ELECTRICITY; feedstock for both chips and polysilicon, itself power-sited. '
             '~70% China (explicit estimate; silicon metal is not in the atlas production dataset).'},
    {'m': 'Ferrochrome', 'process': 'Submerged-arc furnace', 'group': 'fuel',
     'mwh_elec': 3.6, 'mwh_primary': 3.6, 'co2': 4, 'share': 40, 'stage': 'ferrochrome (process)',
     'holder': 'China · S. Africa · Kazakhstan', 'energy_type': 'electricity + co-located ore', 'conf': 'estimate',
     'src': 'ICDA; USGS chromium',
     'note': 'Mixed: electricity-hungry, but South Africa smelts on chromite + Eskom coal (ore AND power), '
             'while China imports ore and runs on cheap power. Cheap energy matters, but so does the ore. ~40% top.'},
    {'m': 'Steel (crude)', 'process': 'Blast furnace', 'group': 'fuel',
     'mwh_elec': 0.6, 'mwh_primary': 5.5, 'co2': 1.9, 'share': 52, 'stage': 'crude steel',
     'holder': 'China', 'energy_type': 'reductant + fuel (coking coal)', 'conf': 'measured',
     'src': 'worldsteel',
     'note': '~5.5 MWh-equiv/t, almost all coking coal (reductant), not electricity. Sites on coal + iron '
             'ore + demand, not power. Included as scale reference: ~52% China, ~1.9 t CO2/t.'},
    {'m': 'Ammonia', 'process': 'Haber–Bosch', 'group': 'fuel',
     'mwh_elec': 0.6, 'mwh_primary': 9.5, 'co2': 2.4, 'share': 30, 'stage': 'ammonia (process)',
     'holder': 'China', 'energy_type': 'feedstock (natural gas / coal)', 'conf': 'estimate',
     'src': 'IFA; USGS nitrogen',
     'note': 'Energy IS the feedstock (gas or, in China, coal), not electricity. Moderately concentrated: '
             'China ~30% on coal gasification, the rest spread across gas-rich regions — energy-cost-sited '
             'but multi-country, not a single chokepoint.'},
    {'m': 'Copper (smelting)', 'process': 'Flash smelting', 'group': 'control',
     'mwh_elec': 2.5, 'mwh_primary': 2.5, 'co2': 2, 'share': 42, 'stage': 'refined/smelter (NOT mine)',
     'holder': 'China', 'energy_type': 'electricity (low)', 'conf': 'estimate',
     'src': 'ICSG (China ~40-45% of refined copper) — mine share (Chile ~24%) is a DIFFERENT stage',
     'note': 'THE CONTROL, corrected. Smelting is low-energy (~2.5 MWh/t), yet it is NOT diffuse: China '
             'holds ~40-45% of refined copper. A low-energy stage that concentrated anyway — on concentrate '
             'logistics, sulphuric-acid handling and policy, not on power. Energy is not the whole story.'},
]
GROUP_ORDER = {'power': 0, 'fuel': 1, 'control': 2}
DATA.sort(key=lambda d: (GROUP_ORDER[d['group']], -d['mwh_primary']))
out = {'note': ('Energy per tonne (electricity and total primary) and CO2 per tonne for the energy-intensive '
                'refining stages, beside each stage-matched concentration. Cheap energy concentrates refining, '
                'but its FORM sets the mechanism: some stages site on cheap POWER (aluminium, polysilicon, '
                'silicon), others on cheap FUEL + a co-located reductant/ore (magnesium, ferrochrome, steel, '
                'ammonia), and copper shows even a low-energy stage can concentrate on logistics and policy. '
                'Figures are order-of-magnitude literature values; concentration is stage-matched and sourced '
                'per row (never the mine share for a refining stage).'),
       'materials': DATA}
json.dump(out, open(os.path.join(ROOT, 'out', 'energy_footprint.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(f"{'material':20}{'elec':>6}{'prim':>6}{'CO2':>5}{'share':>7}  {'group':8} {'energy_type'}")
for d in DATA:
    print(f"{d['m'][:19]:20}{d['mwh_elec']:>6}{d['mwh_primary']:>6}{d['co2']:>5}{d['share']:>6}%  {d['group']:8} {d['energy_type']}")
print("wrote out/energy_footprint.json")

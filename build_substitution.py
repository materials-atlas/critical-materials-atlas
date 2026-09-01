#!/usr/bin/env python3
"""Substitution networks — does replacing a material actually MOVE the chokepoint, or just shift it?
The audit flagged this as the atlas's biggest missing dimension. Substitutability is usually shown as a
yes/no flag; the decision-relevant question is different: if you substitute material A with B, does B sit
in a LESS concentrated supply chain (a real escape) or an EQUALLY concentrated one (you just swapped
which country holds you)? This joins a curated substitution graph to the atlas's own production
concentration, so every substitution carries the number that says whether it helps.

Edges are curated from USGS MCS 'Substitutes' lines + battery/magnet/semiconductor domain knowledge;
concentration (top-producer mine share) is read from production.json. Effect is classified:
  escape   - substitute is an abundant/diffuse material (iron, sodium, silicon, carbon) -> real relief
  relieve  - substitute is a tracked material but markedly LESS concentrated than the original
  shift    - substitute is another concentrated chokepoint (>=55% one country) -> problem just moves
  partial  - helps in some uses / at a performance cost, not a clean swap

Public data + stated domain edges. Run: python build_substitution.py  ->  out/substitution.json
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
prod = {r['label']: r for r in json.load(open(os.path.join(ROOT, 'out', 'production.json'), encoding='utf8'))['rows']}
def conc(label):
    r = prod.get(label)
    return (round(r['wmd_top_share'], 0), r['wmd_top']) if r and r.get('wmd_top_share') else (None, None)

# abundant / geologically diffuse substitutes that are NOT supply chokepoints at the mine
ABUNDANT = {'iron + phosphate (LFP)', 'sodium (Na-ion)', 'silicon', 'silicon (anode)', 'aluminium (metal)',
            'ceramics / diamond', 'carbon / organics', 'no-magnet motor (Cu + electronics)'}

# curated substitution edges: from tracked material -> substitute, in a named application
EDGES = [
    # (from_label, from_name, application, substitute, penalty, effect_override, note)
    ('cobalt', 'Cobalt', 'EV & storage batteries', 'iron + phosphate (LFP)', 'lower energy density, heavier packs',
     'escape', 'LFP drops BOTH cobalt (DRC) and nickel (Indonesia) for iron and phosphate — the cleanest real escape in the whole set, and it is already ~40% of new EV batteries.'),
    ('cobalt', 'Cobalt', 'high-performance batteries', 'nickel', 'thermal stability falls as nickel rises',
     'shift', 'High-nickel NMC uses less cobalt but MORE nickel — you swap a DR Congo cobalt dependency for a nickel one, and nickel’s marginal growth is Indonesia-concentrated (with China-linked HPAL processing). The dependency moves; it does not leave.'),
    ('lithium', 'Lithium', 'stationary & entry EV batteries', 'sodium (Na-ion)', 'lower energy density, earlier commercial stage',
     'partial', 'Sodium is one of the most abundant elements on earth, so where Na-ion fits it is a true exit — but that is stationary storage and entry EVs first, not high-energy packs. An escape by SEGMENT, not across the board.'),
    ('magnets', 'Rare-earth magnets', 'EV traction & wind motors', 'no-magnet motor (Cu + electronics)', 'lower efficiency/torque density, more copper & control electronics',
     'partial', 'Induction and externally-excited motors use no rare earths at all (Renault, Tesla have shipped both) — but only for MOTORS, at an efficiency and mass cost, and not for the many other NdFeB uses. A real exit for some drivetrains, not for magnets in general.'),
    ('magnets', 'Rare-earth magnets', 'lower-grade motors & speakers', 'strontium', 'much weaker field — larger, heavier magnets',
     'partial', 'Ferrite (strontium) magnets are cheap and high-volume but far weaker; they replace NdFeB only where size and weight do not matter. Strontium itself is concentrated (Iran).'),
    ('gallium', 'Gallium', 'power & RF semiconductors', 'silicon', 'lower efficiency / frequency; no drop-in for LEDs, RF',
     'partial', 'Silicon is the mature baseline GaN/GaAs improved on, and for some power uses it is a viable fallback — but it cannot replace GaN/GaAs in LEDs, RF or high-frequency parts, where silicon carbide (SiC), not plain silicon, is the closer substitute. A partial exit, use by use.'),
    ('graphite', 'Graphite', 'battery anodes', 'silicon (anode)', 'swelling, shorter cycle life — used blended, not pure',
     'partial', 'Silicon anodes (blended a few %) cut graphite demand and use abundant silicon, but cannot yet replace graphite outright. A pressure valve, not a full exit.'),
    ('copper', 'Copper', 'grid wiring & busbars', 'aluminium (metal)', 'lower conductivity — bigger cross-section',
     'relieve', 'Aluminium already replaces copper in overhead lines and some cabling. Its ORE is more diffuse than copper, though aluminium SMELTING is itself China-heavy — relief at the mine, not fully at the furnace.'),
    ('magnesium', 'Magnesium', 'lightweight structural alloys', 'aluminium (metal)', 'heavier than magnesium',
     'relieve', 'Aluminium substitutes for magnesium in many castings; it trades away some weight saving but exits China’s ~87% Pidgeon-process magnesium grip for a more diversified metal.'),
    ('tantalum', 'Tantalum', 'capacitors', 'niobium', 'lower capacitance density',
     'shift', 'Niobium capacitors substitute for tantalum — but niobium is 92% Brazil, MORE concentrated than tantalum. A textbook case of shifting, not escaping.'),
    ('tantalum', 'Tantalum', 'capacitors', 'ceramics / diamond', 'different performance envelope',
     'escape', 'Multilayer ceramic capacitors replace tantalum in most consumer electronics, using abundant materials — the real exit where performance allows.'),
    ('tungsten', 'Tungsten', 'cutting tools & wear parts', 'ceramics / diamond', 'brittleness / cost in some uses',
     'partial', 'Polycrystalline diamond and ceramics replace tungsten carbide in specific tooling; broad substitution is limited, so tungsten (78% China) stays sticky.'),
    ('platinum', 'Platinum', 'autocatalysts', 'palladium', 'price-driven, within the same basket',
     'shift', 'Pt, Pd and Rh substitute for each other by relative price — but all three come from the same South Africa + Russia basket. Swapping within the PGMs moves nothing structurally.'),
    ('niobium', 'Niobium', 'HSLA / micro-alloyed steel', 'vanadium', 'different strengthening behaviour',
     'shift', 'Vanadium substitutes for niobium in high-strength steel — but vanadium is a China-heavy steel by-product too. Both roads lead back to concentrated supply.'),
    ('antimony', 'Antimony', 'flame retardants', 'phosphorus / mineral retardants', 'not a drop-in synergist; reformulation + certification',
     'partial', 'Phosphorus- and mineral-based retardants replace antimony trioxide in some polymers, but they are not drop-in synergists and phosphorus has its own concentrated supply — relief in places, not a clean exit for a China-controlled, export-restricted metal.'),
]

def classify(sub, override):
    if sub in ABUNDANT:
        return override if override in ('escape', 'partial', 'relieve') else 'escape'
    return override

rows = []
for frm, frm_name, app, sub, penalty, override, note in EDGES:
    fs, ft = conc(frm)
    # substitute concentration if it is itself a tracked material
    sub_label = {'nickel': 'nickel', 'niobium': 'niobium', 'vanadium': 'vanadium',
                 'palladium': 'palladium', 'strontium': 'strontium'}.get(sub.split(' ')[0].lower())
    ss, st = conc(sub_label) if sub_label else (None, None)
    eff = classify(sub, override)
    rows.append({'from': frm, 'from_name': frm_name, 'from_conc': fs, 'from_top': ft,
                 'application': app, 'substitute': sub, 'sub_conc': ss, 'sub_top': st,
                 'penalty': penalty, 'effect': eff, 'note': note})

order = {'escape': 0, 'relieve': 1, 'partial': 2, 'shift': 3}
rows.sort(key=lambda r: (order[r['effect']], -(r['from_conc'] or 0)))
from collections import Counter
tally = Counter(r['effect'] for r in rows)
out = {'note': ('Curated substitution graph joined to the atlas’s production concentration. A substitution '
                'is an ESCAPE only if the replacement sits in an abundant/diffuse or markedly less-concentrated '
                'supply chain; otherwise it SHIFTS the chokepoint to another country. Domain edges from USGS MCS '
                'substitutes + battery/magnet/semiconductor literature; not exhaustive.'),
       'tally': dict(tally), 'edges': rows}
json.dump(out, open(os.path.join(ROOT, 'out', 'substitution.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('substitution edges:', dict(tally))
for r in rows:
    print(f"  [{r['effect']:8}] {r['from_name']:18} ({r['from_conc']}% {r['from_top']}) -> {r['substitute']}")
print('wrote out/substitution.json')

#!/usr/bin/env python3
"""Cobalt, followed end to end — one metal, one mass balance. Second entry in the material-deep-dive
series (after gallium). Where gallium's story is "94% discarded", cobalt's is different and sharper for
this atlas: it is a BY-PRODUCT (of copper in the DRC, of nickel in Indonesia) that is nonetheless almost
fully recovered — so its supply is capped not by a recovery step but by how much COPPER the DRC digs;
its mine sits in one country (DRC ~75%); its refining sits in ANOTHER (China ~75%); and it is the one
material where the atlas's own reconciliation engine demonstrably UNDERSTATED reality (it missed the
2020-2023 surge in DR Congo's cobalt-hydroxide export dominance). That last point makes cobalt the
honest centrepiece: a page that shows its own tool's limit and corrects it from production + BACI.

Mass balance (2024, World Mining Data + stated constants):
  world cobalt mined            ~269,000 t   (WMD)      top: DR Congo ~75%
  of which by-product of Cu/Ni  ~98%         (literature: ~70% copper, ~28% nickel, ~2% primary)
  refined, China share          ~75%         (IEA / USGS MCS)         <- the chokepoint moves country
  into batteries                ~70%+        (Cobalt Institute / IEA) <- and LFP is eroding it

Engine-miss panel: in 2020 the atlas engine reconstructs ~$0.7B of HS 2822.00 cobalt-oxide/hydroxide
trade with DR Congo at ~15%; official BACI shows ~$3.5B with DR Congo at ~84% (HHI 0.71 vs the engine's
~0.15). The engine's reliability weighting shrinks DRC's large but weakly-corroborated export reports.
Verifiable against BACI HS02 (extract_baci) and out/flows_2020.json.

Public data; constants stated inline with ranges. Run: python build_cobalt.py  ->  out/cobalt.json
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
prod = {r['label']: r for r in json.load(open(os.path.join(ROOT, 'out', 'production.json'), encoding='utf8'))['rows']}

CO_T = prod['cobalt']['world_tonnes']                       # ~268,755 t (WMD 2024)
DRC_MINE = prod['cobalt']['wmd_top_share']                  # 74.5% (WMD)  DR Congo
CU_T = prod['copper']['world_tonnes']                       # ~22.9 Mt (the host that caps cobalt)

# stated constants (with ranges) — the load-bearing assumptions, exposed
BYPRODUCT = {'copper': 0.70, 'nickel': 0.28, 'primary': 0.02}   # cobalt production by host (USGS/CDI)
CHINA_REFINE = {'low': 68, 'central': 76, 'high': 80}           # China share of REFINED cobalt (IEA/USGS)
BATTERY = {'low': 65, 'central': 72, 'high': 78}               # share of cobalt end-use in batteries (CDI/IEA)

# --- the engine-miss, 2020 (HS 2822.00 cobalt oxides/hydroxides) ---
def engine_2020():
    p = os.path.join(ROOT, 'out', 'flows_2020.json')
    if not os.path.exists(p):
        return None
    fl = json.load(open(p, encoding='utf8')).get('materials', {})
    co = fl.get('cobalt') or []
    by = {}
    for f in co:
        by[f['from']] = by.get(f['from'], 0.0) + f['value']
    t = sum(by.values())
    drc = 100 * by.get('CD', 0.0) / t if t else 0
    return {'total_musd': round(t / 1e6), 'drc_share': round(drc, 1)}

eng = engine_2020() or {'total_musd': 675, 'drc_share': 15.1}
# BACI HS02 2020, verified via extract_baci (kept as stated constants to avoid the slow zip pass here)
baci = {'total_musd': 3519, 'drc_share': 84.2, 'hhi': 0.71}

# --- mass-balance steps (share-of-world, tonnes) ---
steps = [
    {'label': 'World cobalt mined', 'tonnes': CO_T, 'lo': CO_T, 'hi': CO_T,
     'note': 'WMD 2024 — 100% of primary supply'},
    {'label': 'From DR Congo (as a copper by-product)', 'tonnes': round(CO_T * DRC_MINE / 100),
     'lo': round(CO_T * 0.70), 'hi': round(CO_T * 0.78),
     'note': f'~{DRC_MINE:.0f}% of mine supply, recovered from Katangan copper ore'},
    {'label': 'Refined in China', 'tonnes': round(CO_T * CHINA_REFINE['central'] / 100),
     'lo': round(CO_T * CHINA_REFINE['low'] / 100), 'hi': round(CO_T * CHINA_REFINE['high'] / 100),
     'note': f"~{CHINA_REFINE['central']}% of refining — the chokepoint moves to a different country than the mine"},
    {'label': 'Into batteries', 'tonnes': round(CO_T * BATTERY['central'] / 100),
     'lo': round(CO_T * BATTERY['low'] / 100), 'hi': round(CO_T * BATTERY['high'] / 100),
     'note': f"~{BATTERY['central']}% of end-use — and LFP (cobalt-free) is eroding this"},
]

S = {
    'cobalt_world_t': CO_T,
    'drc_mine_share': round(DRC_MINE, 1),
    'copper_world_t': CU_T,
    'byproduct': BYPRODUCT,
    'byproduct_pct': round(100 * (BYPRODUCT['copper'] + BYPRODUCT['nickel'])),
    'china_refine_pct': CHINA_REFINE,
    'battery_pct': BATTERY,
    'steps': steps,
    'engine_2020': eng,
    'baci_2020': baci,
    'gap_musd': baci['total_musd'] - eng['total_musd'],
}
json.dump(S, open(os.path.join(ROOT, 'out', 'cobalt.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(f"cobalt: {CO_T:,} t mined, DR Congo {DRC_MINE:.1f}% | ~{S['byproduct_pct']}% by-product | "
      f"China refine ~{CHINA_REFINE['central']}% | battery ~{BATTERY['central']}%")
print(f"engine-miss 2020: engine ${eng['total_musd']}M / DRC {eng['drc_share']}%  vs  "
      f"BACI ${baci['total_musd']}M / DRC {baci['drc_share']}%")
print("wrote out/cobalt.json")

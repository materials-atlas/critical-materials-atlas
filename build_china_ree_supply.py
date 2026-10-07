#!/usr/bin/env python3
"""
China's rare-earth supply in one unit: domestic mine output plus imports, both as rare-earth-oxide (REO)
equivalent.

Mine output is already REO (USGS Mineral Commodity Summaries). Imports are customs net weight, so each
of China's 8-digit tariff lines is converted with the REO content of its product type, as a low / central /
high band from formula weights (hydrated vs anhydrous forms bound each band): oxides 1.0; metals 1.15 /
1.17 / 1.27; hydroxides 0.65 / 0.83 / 0.90; carbonates 0.42 / 0.52 / 0.72; chlorides 0.37 / 0.46 / 0.67;
fluorides 0.80 / 0.83 / 0.86; US bastnaesite concentrate (25309020) 0.55 / 0.60 / 0.70; monazite (HS 2612.20)
0.45 / 0.55 / 0.65; other compounds 0.40 / 0.55 / 0.85. The bands are sensitivity bounds, not a confidence
interval. Reviewed 7 Oct 2026.

Inputs (cached by hand-run pulls of UN Comtrade tariff-line data; the builder makes no network call):
  raw/comtrade/china_ree_tariffline.json   China imports, HS 2846.10, 2846.90, 2805.30, 8-digit, 2023-2025
  raw/comtrade/china_261220_tariffline.json China imports, HS 2612.20 (thorium ores: monazite), 2023-2025
  raw/comtrade/china_253090_tariffline.json China imports under HS 2530.90, 8-digit (25309020 = ores of
                                            rare earth metals), 2023-2025
Line descriptions were checked against China's tariff schedule (htshub.com, 2026 edition), 7 Oct 2026.

Writes out/china_ree_supply.json.
"""
import json, os, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
COMP = json.load(open(os.path.join(ROOT, 'raw', 'comtrade', 'china_ree_tariffline.json'), encoding='utf8'))['rows']
ORE = [r for r in json.load(open(os.path.join(ROOT, 'raw', 'comtrade', 'china_253090_tariffline.json'), encoding='utf8'))['rows']
       if r['cmdCode'] == '25309020']
MONAZ = json.load(open(os.path.join(ROOT, 'raw', 'comtrade', 'china_261220_tariffline.json'), encoding='utf8'))['rows']   # HS 2612.20, thorium ores = monazite
# USGS MCS 2026 (2023 from MCS 2025): China mine production, rare-earth-oxide equivalent, t
MINE = {2023: 255000, 2024: 270000, 2025: 270000}

def kind(c):
    if c == '25309020': return 'ore'
    if c.startswith('261220'): return 'monazite'
    if c.startswith('280530'): return 'metal'
    if c == '28461010' or c.startswith('2846901'): return 'oxide'
    if c == '28461020': return 'hydroxide'
    if c == '28461030' or c.startswith('2846904'): return 'carbonate'
    if c.startswith('2846902'): return 'chloride'
    if c.startswith('2846903'): return 'fluoride'
    return 'other'                                  # 28461090, 2846909x

# REO content per tonne of product: (low, central, high)
F = {'oxide': (1.0, 1.0, 1.0), 'metal': (1.15, 1.17, 1.27), 'hydroxide': (0.65, 0.83, 0.90),
     'carbonate': (0.42, 0.52, 0.72), 'chloride': (0.37, 0.46, 0.67), 'fluoride': (0.80, 0.83, 0.86),
     'ore': (0.55, 0.60, 0.70), 'monazite': (0.45, 0.55, 0.65), 'other': (0.40, 0.55, 0.85)}
# factor bands from formula weights (reviewed 7 Oct 2026): hydrated vs anhydrous salts bound each band;
# 'other' cannot reach 1.0 because oxides have their own lines; ore = US bastnaesite flotation concentrate
PARTNER = {104: 'MM', 418: 'LA', 458: 'MY', 704: 'VN', 840: 'US', 566: 'NG', 450: 'MG', 764: 'TH'}

out = {'unit': 'tonnes rare-earth-oxide (REO) equivalent', 'factors': F, 'mine_source': 'USGS MCS', 'years': [],
       'definition': 'domestic mine output (USGS, quota-based) plus customs imports converted to REO; not consumption',
       'caveats': ['exports, re-exports and stocks are not removed, so this is not apparent consumption',
                   'the USGS China figure follows the mining quota; above-quota output would lower the import share',
                   'low/central/high are factor-sensitivity bounds, not a confidence interval',
                   'one REO tonne counts lanthanum and dysprosium alike; no heavy/light split',
                   'HS 2612.20 (thorium ores and concentrates) is treated as monazite feed by inference from the heading, the origins (Nigeria, Madagascar, Thailand) and unit values of $3-4/kg; the code does not name monazite',
                   'US bastnaesite concentrate (25309020) is included; other headings and chemical preparations are not',
                   'null net weights count as zero']}
for y in sorted(MINE):
    by_kind, by_partner = collections.Counter(), collections.defaultdict(collections.Counter)
    for r in COMP + ORE + MONAZ:
        if r['period'] != y:
            continue
        k, w = kind(r['cmdCode']), (r['netWgt'] or 0) / 1000.0
        by_kind[k] += w
        by_partner[PARTNER.get(r['partnerCode'], 'other')][k] += w
    imp = [sum(by_kind[k] * F[k][i] for k in by_kind) for i in range(3)]
    tot = [MINE[y] + x for x in imp]
    share = [imp[i] / tot[i] * 100 for i in range(3)]
    out['years'].append({
        'year': y, 'mine_reo_t': MINE[y], 'imports_net_t': round(sum(by_kind.values())),
        'imports_by_kind_net_t': {k: round(v) for k, v in by_kind.most_common()},
        'imports_reo_t': {'low': round(imp[0]), 'central': round(imp[1]), 'high': round(imp[2])},
        'import_share_pct': {'low': round(share[0], 1), 'central': round(share[1], 1), 'high': round(share[2], 1)},
        'imports_reo_by_partner_central_t': {p: round(sum(c[k] * F[k][1] for k in c)) for p, c in
                                             sorted(by_partner.items(), key=lambda x: -sum(x[1][k] * F[k][1] for k in x[1]))},
    })
json.dump(out, open(os.path.join(ROOT, 'out', 'china_ree_supply.json'), 'w', encoding='utf8'), indent=1)
for r in out['years']:
    print(r['year'], 'mine', r['mine_reo_t'], '| imports REO', r['imports_reo_t'], '| import share %', r['import_share_pct'],
          '| by partner', r['imports_reo_by_partner_central_t'])

# -*- coding: utf-8 -*-
"""Grinding balls, step 1: the coverage gate (grinding-balls/PREREGISTRATION.md).

Can imported forged grinding balls (HS 732611) physically be the input to a country's mills?
For every country milling more than 20 Mt of ore in 2024, compare 2022-24 apparent consumption of
screened forged-ball trade with the ball demand implied by its ore milled. Rules, bands and tiers
are the ones filed before this was run; nothing here chooses them.

Writes out/grinding_balls.json.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import duckdb  # noqa: E402
import baci  # noqa: E402

CODE = '732611'
YEARS = (2022, 2023, 2024)
SCREEN = (0.4, 3.0)
SAMPLE_MIN_ORE_MT = 20.0
MIN_TIER_A = 6

# Ore milled = contained metal / (grade x recovery); filed constants.
ORE = {
    'copper': {'grade': 0.0060, 'recovery': 0.85},
    'gold': {'grade': 1.5e-6, 'recovery': 0.88},        # 1.5 g/t
    'leadzinc': {'grade': 0.06, 'recovery': 0.85},
}
# Verified intensity band, kg of steel media per tonne of ore (deviation of 2026-09-14).
BAND = {'copper': (0.33, 0.88), 'gold': (0.46, 1.01), 'leadzinc': (0.36, 0.74)}


def wmedian(vals, weights):
    pairs = sorted(zip(vals, weights))
    half = sum(weights) / 2.0
    acc = 0.0
    for v, w in pairs:
        acc += w
        if acc >= half:
            return v
    return pairs[-1][0]


def ore_milled(con):
    """t of ore milled by country-year, per commodity group, from BGS mine production."""
    rows = con.execute("""
        select country_iso3, year, material, sum(value_t) t
        from read_parquet(?) where source='BGS World Mineral Statistics' and stage='mine'
          and measure='production' and material in ('copper','gold','lead','zinc')
          and year between 2022 and 2024 and country_iso3 is not null
        group by 1,2,3""", [os.path.join(ROOT, 'out', 'cube.parquet')]).fetchall()
    out = {}
    for iso, yr, mat, t in rows:
        grp = 'leadzinc' if mat in ('lead', 'zinc') else mat
        d = out.setdefault(iso, {}).setdefault(yr, {'copper': 0.0, 'gold': 0.0, 'leadzinc': 0.0})
        d[grp] += (t or 0.0)
    ore = {}
    for iso, years in out.items():
        for yr, metal in years.items():
            ore.setdefault(iso, {})[yr] = {g: metal[g] / (ORE[g]['grade'] * ORE[g]['recovery'])
                                          for g in metal}
    return ore


def trade(con, num2iso):
    """Screened imports and exports (t) of 732611 by country-year, plus screen diagnostics."""
    ac, diag = {}, {}
    for yr in YEARS:
        p = baci.path(yr, 'HS02').replace(os.sep, '/')
        flows = con.execute("select i, j, v, q from read_parquet('%s') where k='%s'" % (p, CODE)).fetchall()
        tot_v = sum(f[2] or 0 for f in flows)
        noq = [f for f in flows if not f[3]]
        withq = [f for f in flows if f[3]]
        med = wmedian([f[2] / f[3] for f in withq], [f[3] for f in withq])   # $k per t
        lo, hi = SCREEN[0] * med, SCREEN[1] * med
        kept = [f for f in withq if lo <= f[2] / f[3] <= hi]
        dropped = [f for f in withq if not (lo <= f[2] / f[3] <= hi)]
        diag[yr] = {
            'median_usd_per_t': round(med * 1000, 1),
            'flows': len(flows),
            'no_quantity_flows': len(noq),
            'no_quantity_value_share_pct': round(100.0 * sum(f[2] or 0 for f in noq) / tot_v, 2),
            'screened_out_flows': len(dropped),
            'screened_out_kt': round(sum(f[3] for f in dropped) / 1000, 1),
            'kept_kt': round(sum(f[3] for f in kept) / 1000, 1),
            'largest_screened_out': sorted(
                [{'from': num2iso.get(str(f[0])), 'to': num2iso.get(str(f[1])), 'kt': round(f[3] / 1000, 1),
                  'usd_per_t': round(1000 * f[2] / f[3])} for f in dropped], key=lambda x: -x['kt'])[:5],
        }
        for i, j, v, q in kept:
            ei, ej = num2iso.get(str(i)), num2iso.get(str(j))
            if ej:
                ac.setdefault(ej, {}).setdefault(yr, [0.0, 0.0])[0] += q
            if ei:
                ac.setdefault(ei, {}).setdefault(yr, [0.0, 0.0])[1] += q
    return ac, diag


def main():
    con = duckdb.connect()
    cc = baci.countries()
    num2iso = {str(k): v for k, v in cc['iso3'].items() if v}
    ore = ore_milled(con)
    tr, diag = trade(con, num2iso)

    sample = sorted(iso for iso, yrs in ore.items()
                    if 2024 in yrs and sum(yrs[2024].values()) / 1e6 > SAMPLE_MIN_ORE_MT)
    rows = []
    for iso in sample:
        yrs = ore[iso]
        missing = [y for y in YEARS if y not in yrs]
        have = [y for y in YEARS if y in yrs]
        mean_ore = {g: sum(yrs[y][g] for y in have) / len(have) for g in BAND}
        demand_mid = sum(mean_ore[g] * (BAND[g][0] + BAND[g][1]) / 2 for g in BAND) / 1e6   # kt
        demand_hi = sum(mean_ore[g] * BAND[g][1] for g in BAND) / 1e6
        demand_lo = sum(mean_ore[g] * BAND[g][0] for g in BAND) / 1e6
        imp = sum(tr.get(iso, {}).get(y, [0, 0])[0] for y in YEARS) / len(YEARS) / 1000
        exp = sum(tr.get(iso, {}).get(y, [0, 0])[1] for y in YEARS) / len(YEARS) / 1000
        # filed rule: AC is floored at zero each year, then averaged (not the floor of the mean)
        acv = sum(max(0.0, tr.get(iso, {}).get(y, [0, 0])[0] - tr.get(iso, {}).get(y, [0, 0])[1])
                  for y in YEARS) / len(YEARS) / 1000
        ratio = acv / demand_mid if demand_mid else None
        if acv > 2 * demand_hi:
            tier = 'flagged'
        elif ratio >= 0.5:
            tier = 'A'
        elif ratio >= 0.1:
            tier = 'B'
        else:
            tier = 'excluded'
        rows.append({
            'iso3': iso,
            'ore_milled_2024_mt': round(sum(yrs[2024].values()) / 1e6, 1),
            'ore_milled_mean_mt': {g: round(mean_ore[g] / 1e6, 1) for g in BAND},
            'ore_years_missing': missing,
            'ball_demand_kt': {'low': round(demand_lo, 1), 'mid': round(demand_mid, 1), 'high': round(demand_hi, 1)},
            'imports_kt': round(imp, 1), 'exports_kt': round(exp, 1), 'apparent_consumption_kt': round(acv, 1),
            'ratio_to_mid': round(ratio, 3) if ratio is not None else None,
            'tier': tier,
        })
    rows.sort(key=lambda r: -(r['ratio_to_mid'] or 0))
    n_a = sum(r['tier'] == 'A' for r in rows)
    doc = {
        'study': 'grinding balls as a public proxy for ore milled',
        'step': 'coverage gate',
        'preregistration': 'grinding-balls/PREREGISTRATION.md',
        'code': CODE, 'years': list(YEARS),
        'constants': {'ore': ORE, 'band_kg_per_t': BAND, 'screen_x_median': SCREEN,
                      'sample_min_ore_mt_2024': SAMPLE_MIN_ORE_MT, 'min_tier_a': MIN_TIER_A},
        'screen': diag,
        'countries': rows,
        'tier_counts': {t: sum(r['tier'] == t for r in rows) for t in ('A', 'B', 'excluded', 'flagged')},
        'decision': ('continue to the throughput test' if n_a >= MIN_TIER_A
                     else 'stop at the gate: fewer than %d import-dependent countries' % MIN_TIER_A),
        'sources': ['CEPII BACI HS02 V202601 (Etalab Open Licence 2.0)',
                    'BGS World Mineral Statistics, mine production (via out/cube.parquet)',
                    'grinding-balls/intensity_sources.csv'],
    }
    with open(os.path.join(ROOT, 'out', 'grinding_balls.json'), 'w', encoding='utf-8') as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)

    print('screen:', {y: (d['median_usd_per_t'], d['screened_out_kt'], d['kept_kt'], d['no_quantity_value_share_pct']) for y, d in diag.items()})
    print('%-4s %8s %8s %8s %8s %8s %7s  %s' % ('iso', 'ore Mt', 'dem lo', 'dem mid', 'dem hi', 'AC kt', 'ratio', 'tier'))
    for r in rows:
        print('%-4s %8.0f %8.1f %8.1f %8.1f %8.1f %7.2f  %s%s' % (
            r['iso3'], r['ore_milled_2024_mt'], r['ball_demand_kt']['low'], r['ball_demand_kt']['mid'],
            r['ball_demand_kt']['high'], r['apparent_consumption_kt'], r['ratio_to_mid'], r['tier'],
            ('  (ore years missing %s)' % r['ore_years_missing']) if r['ore_years_missing'] else ''))
    print('tiers:', doc['tier_counts'], '->', doc['decision'])


if __name__ == '__main__':
    main()

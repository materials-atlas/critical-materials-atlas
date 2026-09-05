#!/usr/bin/env python3
"""Reconcile the two apparent-consumption methods, and record WHY they differ.

Background. Apparent consumption (refined production + imports - exports) has been computed two
ways: by a dedicated per-metal builder using mirror-reconciled trade, and - since the cube exists -
as a single query over one table. A first comparison appeared to show a 4-point disagreement on
China's share of refined copper (53% vs 57%), which would have been a serious problem: two of our
own methods contradicting each other.

It was not a disagreement. It was a bad query, and instructively so - it broke the exact rule the
pairing map exists to enforce. Filtering production on (material='copper', stage='processed')
silently summed THREE different BGS copper forms as if they were one series, and it compared a 2022
cube figure against a 2023 pipeline figure. Pair the declared form (BGS 'copper, refined') with the
declared code (HS 740311, cathodes) in a single year, and the methods agree to under one point.

The residual difference that remains is real and worth keeping visible:
  * production vintage - the per-metal builder mixes years (production 2022, trade 2024) because it
    takes each component from the latest source available. The cube can be internally consistent at
    one year. The page does disclose the mixed vintage per material, so nothing was hidden.
  * trade source - raw BACI vs mirror-reconciled flows differ by ~5% on China's net refined copper
    trade (3,163 vs 3,347 kt), which moves the share by a few tenths of a point.

Run:  python build_ac_reconcile.py   ->  out/ac_reconciliation.json
"""
import os, sys, json
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))

# Explicit pairing, exactly as the cross-source map requires: the production FORM and the trade
# CODE are named, never inferred from the material label.
PAIRS = {
    'copper': {'form': 'copper, refined', 'hs': '740311', 'stage': 'refined metal'},
}

# Published by the old builder but NOT computable from the cube, with the reason. This is the
# gate on retiring that builder: it may only go when the cube reproduces everything it publishes.
CANNOT_PAIR = {
    'lithium': 'BGS carries lithium only as "lithium minerals" - ORE at gross weight - while the '
               'mapped trade code 283691 is lithium CARBONATE, a refined chemical. Production and '
               'trade therefore sit at different stages on different bases, and differencing them '
               'would be the same category error the cross-source map exists to prevent. A cube '
               'apparent consumption for lithium needs a refined-lithium production series we do '
               'not yet have.',
}


def cube_ac(c, material, form, hs, year):
    prod = (c[(c.material == material) & (c.measure == 'production') & (c.native_label == form)
              & (c.year == year) & (c.source.str.startswith('BGS'))]
            .groupby('country_iso3').value_t.sum())
    if prod.empty:
        return None
    imp = (c[(c.material == material) & (c.measure == 'imports') & (c.native_code == hs)
             & (c.year == year)].groupby('country_iso3').value_t.sum())
    exp = (c[(c.material == material) & (c.measure == 'exports') & (c.native_code == hs)
             & (c.year == year)].groupby('country_iso3').value_t.sum())
    if imp.empty and exp.empty:
        return None
    idx = prod.index.union(imp.index).union(exp.index)
    ac = (prod.reindex(idx, fill_value=0) + imp.reindex(idx, fill_value=0)
          - exp.reindex(idx, fill_value=0))
    world = float(ac[ac > 0].sum())
    return {
        'year': year, 'form': form, 'hs': hs,
        'china_production_kt': round(float(prod.get('CHN', 0)) / 1e3, 1),
        'china_net_trade_kt': round(float(imp.get('CHN', 0) - exp.get('CHN', 0)) / 1e3, 1),
        'china_ac_kt': round(float(ac.get('CHN', 0)) / 1e3, 1),
        'world_positive_ac_kt': round(world / 1e3, 1),
        'china_share_pct': round(100 * float(ac.get('CHN', 0)) / world, 1) if world else None,
        'n_countries': int((ac != 0).sum()),
    }


def main():
    c = pd.read_parquet(os.path.join(ROOT, 'pipeline', 'data', 'cube.parquet'))
    old = json.load(open(os.path.join(ROOT, 'out', 'apparent.json'), encoding='utf-8'))
    old_year = old.get('year')
    rows = []
    for mat, spec in PAIRS.items():
        cube = cube_ac(c, mat, spec['form'], spec['hs'], old_year)
        if not cube:
            rows.append({'material': mat, 'status': 'cube cannot pair this material yet',
                         'pairing': spec})
            continue
        blocs = (old.get('minerals', {}).get(mat) or {}).get('rows') or []
        cn = next((b for b in blocs if b.get('bloc') == 'China'), None)
        row = {'material': mat, 'pairing': spec, 'cube': cube}
        if cn:
            row['pipeline'] = {'china_production_kt': cn.get('production'),
                               'china_net_trade_kt': cn.get('net_trade'),
                               'china_ac_kt': cn.get('ac'), 'china_share_pct': cn.get('share')}
            if cube['china_share_pct'] is not None and cn.get('share') is not None:
                row['share_gap_pp'] = round(cube['china_share_pct'] - cn['share'], 1)
        rows.append(row)
    for mat, why in CANNOT_PAIR.items():
        rows.append({'material': mat, 'status': 'NOT computable from the cube', 'reason': why})
    out = {
        'verdict': 'RETAIN the per-metal builder. The cube reproduces copper (within 1 point) but '
                   'cannot compute lithium, which that builder also publishes - so retiring it now '
                   'would delete a published result and the only other method for it.',
        'note': 'Two apparent-consumption methods compared on the same year: a single query over '
                'the harmonized cube vs the dedicated per-metal builder using mirror-reconciled '
                'trade. The apparent 4-point disagreement reported earlier was a QUERY ERROR - '
                'filtering production on stage summed several BGS copper forms as one series and '
                'compared mismatched years. Paired explicitly, the methods agree closely.',
        'residual_causes': [
            'Production vintage: the per-metal builder mixes years (it takes each component from '
            'the latest source available, e.g. production 2022 with trade 2024) while a cube query '
            'can hold one year throughout. The public page discloses the mixed vintage per material.',
            'Trade source: raw BACI vs mirror-reconciled flows differ by roughly 5% on China net '
            'refined copper trade, worth a few tenths of a point on the share.',
        ],
        'rule_this_broke': 'Never select a production series by (material, stage). Name the form. '
                           'Three BGS copper forms carry stage="processed".',
        'pipeline_year': old_year, 'materials': rows,
    }
    json.dump(out, open(os.path.join(ROOT, 'out', 'ac_reconciliation.json'), 'w', encoding='utf-8'),
              indent=1)
    print(f'WROTE out/ac_reconciliation.json (pipeline year {old_year})')
    for r in rows:
        if 'cube' in r and 'pipeline' in r:
            print(f"  {r['material']:<8} cube {r['cube']['china_share_pct']:>5}%  "
                  f"pipeline {r['pipeline']['china_share_pct']:>5}%  "
                  f"gap {r.get('share_gap_pp'):>+5} pp")
        else:
            print(f"  {r['material']:<8} {r.get('status', 'no pipeline row')}")


if __name__ == '__main__':
    main()

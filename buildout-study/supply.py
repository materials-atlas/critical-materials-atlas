# -*- coding: utf-8 -*-
"""Amendment E: China's share of EU supply, not just of EU imports.

apparent supply = EU sold production (Eurostat Prodcom, PRODVAL) + imports from outside the EU
                  - exports to outside the EU (Comext, the amendment B download, UK excluded)

Committed before its first run on the production values. Writes out/buildout_supply.json.
Network fetcher inside: Prodcom is pulled once and cached to buildout-study/prodcom_cache.json, so a
re-run needs no network. Usage:  python buildout-study/supply.py
"""
import glob
import json
import os
import sys
import urllib.request

import duckdb

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'out', 'buildout_supply.json')
CACHE = os.path.join(HERE, 'prodcom_cache.json')
API = ('https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/DS-059358'
       '?format=JSON&lang=EN&freq=A&reporter=EU27_2020&indicators=PRODVAL&product=%s')
GROUPS = {
    'transformers': {'prodcom': ['27114120', '27114150', '27114180'],
                     'hs6': ['850421', '850422', '850423'],
                     'label': 'Liquid-dielectric transformers'},
    'goes': {'prodcom': ['24105310', '24105410'],
             'hs6': ['722511', '722611'],
             'label': 'Grain-oriented electrical steel'},
}
YEARS = list(range(2019, 2026))


def prodcom():
    """EU27 sold production value by Prodcom code and year, in euro. Cached after the first pull."""
    if os.path.exists(CACHE):
        with open(CACHE, encoding='utf-8') as f:
            return json.load(f)
    out = {}
    for g in GROUPS.values():
        for code in g['prodcom']:
            req = urllib.request.Request(API % code, headers={'User-Agent': 'critical-materials-atlas'})
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.load(r)
            if 'error' in d:
                raise RuntimeError('%s: %s' % (code, d['error']))
            years = d['dimension']['time']['category']['index']
            inv = {i: y for y, i in years.items()}
            n_time = len(inv)
            # one product, one reporter, one indicator: the flat index is the time index
            out[code] = {inv[int(i)]: v for i, v in d['value'].items() if int(i) in inv}
            assert len(out[code]) <= n_time
    with open(CACHE, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1)
    return out


def trade():
    """Extra-EU imports and exports by six-digit line and year, euro, UK excluded on both sides."""
    files = sorted(glob.glob(os.path.join(HERE, 'eu_data', 'comext_*.parquet')))
    con = duckdb.connect()
    d = con.execute("""select substr(PRODUCT_NC, 1, 6) as k, substr(PERIOD, 1, 4) as year, FLOW as fl,
                              case when PARTNER = 'CN' then 'CN' else 'other' end as who,
                              sum(try_cast(VALUE_EUR as double)) as v
                       from read_parquet(?)
                       where TRADE_TYPE = 'E' and FLOW in ('1', '2')
                         and REPORTER <> 'GB' and PARTNER not in ('GB', 'XI')
                         and cast(substr(PERIOD, 5, 2) as int) between 1 and 12
                       group by 1, 2, 3, 4""", [files]).df()
    return d


def main():
    pc, tr = prodcom(), trade()
    res = {'filing': 'buildout-study/AMENDMENT_SUPPLY_2026.md',
           'sources': {'production': 'Eurostat Prodcom DS-059358, PRODVAL, EU27_2020',
                       'trade': 'Eurostat Comext, extra-EU imports and exports, UK excluded'},
           'note': 'Values in million euro. Apparent supply = sold production + imports - exports. '
                   'Production is at the factory gate and imports include freight, so the sum mixes '
                   'price bases; sold production excludes what a maker uses itself.',
           'groups': {}}
    for key, g in GROUPS.items():
        rows = {}
        for y in YEARS:
            ys = str(y)
            prod = [pc.get(c, {}).get(ys) for c in g['prodcom']]
            imp = tr[(tr.year == ys) & (tr.fl == '1') & (tr.k.isin(g['hs6']))]
            exp = tr[(tr.year == ys) & (tr.fl == '2') & (tr.k.isin(g['hs6']))]
            imp_cn = float(imp[imp.who == 'CN'].v.sum())
            imp_all, exp_all = float(imp.v.sum()), float(exp.v.sum())
            row = {'production_meur': (None if any(p is None for p in prod)
                                       else round(sum(prod) / 1e6, 1)),
                   'production_missing_codes': [c for c in g['prodcom'] if pc.get(c, {}).get(ys) is None],
                   'imports_meur': round(imp_all / 1e6, 1), 'exports_meur': round(exp_all / 1e6, 1),
                   'imports_from_china_meur': round(imp_cn / 1e6, 1),
                   'china_share_of_imports': round(imp_cn / imp_all, 4) if imp_all else None}
            if row['production_meur'] is not None:
                supply = row['production_meur'] + row['imports_meur'] - row['exports_meur']
                row['apparent_supply_meur'] = round(supply, 1)
                row['china_share_of_supply'] = round(imp_cn / 1e6 / supply, 4) if supply > 0 else None
                row['import_share_of_supply'] = round(row['imports_meur'] / supply, 4) if supply > 0 else None
            rows[y] = row
        res['groups'][key] = {'label': g['label'], 'prodcom': g['prodcom'], 'hs6': g['hs6'], 'years': rows}
    # the filed reading, applied to the latest year that has production
    for key, g in res['groups'].items():
        done = [y for y, r in g['years'].items() if r.get('china_share_of_supply') is not None]
        if done:
            y = max(done)
            r = g['years'][y]
            ratio = r['china_share_of_supply'] / r['china_share_of_imports'] if r['china_share_of_imports'] else None
            g['reading_year'] = y
            g['reading'] = ('the import share is a fair guide to dependence'
                            if ratio is not None and ratio >= 0.5
                            else 'the import share overstates dependence; the supply share is the number to use')
            g['supply_to_import_share_ratio'] = round(ratio, 3) if ratio is not None else None
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=1, default=float)
    for key, g in res['groups'].items():
        print('==', g['label'])
        for y, r in g['years'].items():
            print('  %s prod %9s  imports %8.1f (CN %6.1f)  exports %8.1f  supply %9s  CN share: imports %s supply %s'
                  % (y, r['production_meur'], r['imports_meur'], r['imports_from_china_meur'], r['exports_meur'],
                     r.get('apparent_supply_meur'),
                     ('%.1f%%' % (100 * r['china_share_of_imports'])) if r['china_share_of_imports'] else '-',
                     ('%.1f%%' % (100 * r['china_share_of_supply'])) if r.get('china_share_of_supply') else '-'))
        print('  reading (%s): %s' % (g.get('reading_year'), g.get('reading')))
    print('wrote', OUT)


if __name__ == '__main__':
    main()

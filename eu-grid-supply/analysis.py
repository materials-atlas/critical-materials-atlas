# -*- coding: utf-8 -*-
"""Which parts of Europe's grid come from China, on a supply basis. Runs the measure filed in
eu-grid-supply/PREREGISTRATION.md. Committed before its first run.

apparent supply = EU27 sold production (Prodcom DS-059358, PRODVAL, EU27_2020)
                  + imports from outside the EU - exports to outside the EU (Comext, UK excluded)

A missing Prodcom value is never read as zero. If any of a component's Prodcom codes is missing in a
year, production is summed over the codes that are present and the supply share is reported as an
UPPER BOUND only (missing production would lower China's share), with no point estimate.

Prodcom is pulled once and cached to eu-grid-supply/prodcom_cache.json. Trade comes from the monthly
Comext files downloaded for the export-controls study (export-controls/eu_data).
Writes out/eu_grid_supply.json. Usage: python eu-grid-supply/analysis.py
"""
import glob
import json
import os
import urllib.request

import duckdb

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'out', 'eu_grid_supply.json')
CACHE = os.path.join(HERE, 'prodcom_cache.json')
EU_DATA = os.path.join(ROOT, 'export-controls', 'eu_data')
API = ('https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/DS-059358'
       '?format=JSON&lang=EN&freq=A&reporter=EU27_2020&indicators=PRODVAL&product=%s')
YEARS = list(range(2019, 2025))
HEADLINE = 2024
COMPONENTS = [
    ('transformers', 'Liquid-dielectric transformers',
     ['27114120', '27114150', '27114180'], ['85042100', '85042210', '85042290', '85042300']),
    ('goes', 'Grain-oriented electrical steel', ['24105310', '24105410'], ['72251100', '72261100']),
    ('cables', 'Insulated conductors above 1,000 V', ['27321400'], ['85446010', '85446090']),
    ('switchgear', 'Switchgear above 1,000 V', ['27121010', '27121020', '27121030', '27121041', '27121090'],
     ['85351000', '85352100', '85352900', '85353010', '85353090', '85354000', '85359000']),
    ('switchboards', 'Switchboards above 1,000 V', ['27123203', '27123205'], ['85372091', '85372099']),
    ('inverters', 'Inverters above 7.5 kVA', ['27904155'], ['85044086']),
    ('meters', 'Electricity meters (incl. household smart meters)', ['26516370'],
     ['90283011', '90283019', '90283090']),
]


def prodcom():
    if os.path.exists(CACHE):
        return json.load(open(CACHE, encoding='utf-8'))
    out = {}
    for _, _, pcodes, _ in COMPONENTS:
        for code in pcodes:
            req = urllib.request.Request(API % code, headers={'User-Agent': 'critical-materials-atlas'})
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.load(r)
            if 'error' in d:
                out[code] = {}
                continue
            years = d['dimension']['time']['category']['index']
            inv = {i: y for y, i in years.items()}
            out[code] = {inv[int(i)]: v for i, v in d['value'].items() if int(i) in inv}
    json.dump(out, open(CACHE, 'w', encoding='utf-8'), indent=1)
    return out


def trade():
    files = sorted(glob.glob(os.path.join(EU_DATA, 'comext_*.parquet')))
    con = duckdb.connect()
    return con.execute("""select PRODUCT_NC as code, substr(PERIOD, 1, 4) as year, FLOW as fl,
                                 case when PARTNER = 'CN' then 'CN' else 'other' end as who,
                                 sum(try_cast(VALUE_EUR as double)) as v
                          from read_parquet(?)
                          where TRADE_TYPE = 'E' and FLOW in ('1', '2')
                            and REPORTER <> 'GB' and PARTNER not in ('GB', 'XI')
                            and cast(substr(PERIOD, 5, 2) as int) between 1 and 12
                          group by 1, 2, 3, 4""", [files]).df()


def band(x):
    return None if x is None else ('low' if x < 0.10 else 'material' if x < 0.25 else 'high' if x < 0.50
                                   else 'critical')


def ratio_reading(r):
    return None if r is None else ('the import share overstates dependence' if r < 0.5 else
                                   'the import share partly overstates it' if r < 0.8 else
                                   'the import share is a fair guide')


def main():
    pc, tr = prodcom(), trade()
    res = {'filing': 'eu-grid-supply/PREREGISTRATION.md', 'headline_year': HEADLINE, 'components': {}}
    for key, label, pcodes, cn in COMPONENTS:
        rows = {}
        for y in YEARS:
            ys = str(y)
            present = {c: pc.get(c, {}).get(ys) for c in pcodes}
            missing = [c for c, v in present.items() if v is None]
            prod = sum(v for v in present.values() if v is not None) / 1e6
            t = tr[(tr.year == ys) & tr.code.isin(cn)]
            imp, exp = t[t.fl == '1'], t[t.fl == '2']
            imp_all, imp_cn = float(imp.v.sum()) / 1e6, float(imp[imp.who == 'CN'].v.sum()) / 1e6
            exp_all = float(exp.v.sum()) / 1e6
            supply = prod + imp_all - exp_all
            sh_imp = imp_cn / imp_all if imp_all > 0 else None
            sh_sup = imp_cn / supply if supply > 0 else None
            rows[y] = {'production_meur': round(prod, 1), 'production_missing_codes': missing,
                       'imports_meur': round(imp_all, 1), 'imports_from_china_meur': round(imp_cn, 1),
                       'exports_meur': round(exp_all, 1), 'apparent_supply_meur': round(supply, 1),
                       'china_share_of_imports': round(sh_imp, 4) if sh_imp is not None else None,
                       'china_share_of_supply': (round(sh_sup, 4) if (sh_sup is not None and not missing) else None),
                       'china_share_of_supply_upper_bound': (round(sh_sup, 4) if (sh_sup is not None and missing) else None)}
        h = rows[HEADLINE]
        s = h['china_share_of_supply']
        ratio = (s / h['china_share_of_imports']) if (s is not None and h['china_share_of_imports']) else None
        res['components'][key] = {'label': label, 'prodcom': pcodes, 'cn8': cn, 'years': rows,
                                  'headline': {'supply_share': s,
                                               'supply_share_upper_bound': h['china_share_of_supply_upper_bound'],
                                               'import_share': h['china_share_of_imports'],
                                               'ratio': round(ratio, 3) if ratio is not None else None,
                                               'ratio_reading': ratio_reading(ratio),
                                               'supply_band': band(s)}}
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1, default=float)
    print('%-16s %9s %8s %8s %6s  %s' % ('component', 'prod', 'imports', 'CN imp', 'ratio', 'reading'))
    for k, c in res['components'].items():
        h, r = c['headline'], c['years'][HEADLINE]
        print('%-16s %9.0f %8.0f %8.0f  imp %s  sup %s  ub %s  ratio %s  %s | %s' % (
            k, r['production_meur'], r['imports_meur'], r['imports_from_china_meur'],
            h['import_share'], h['supply_share'], h['supply_share_upper_bound'], h['ratio'],
            h['ratio_reading'], h['supply_band']))
    print('wrote', OUT)


if __name__ == '__main__':
    main()

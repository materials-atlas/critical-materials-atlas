# -*- coding: utf-8 -*-
"""The AI build-out page after 2024: the same lines in the EU's and the US's own customs records.

World trade (CEPII BACI) ends in 2024. This reads the EU's imports from outside the EU (Eurostat
Comext) and US general imports (Census), 2024 to July 2026, for the page's lines, and writes
out/ai_buildout_ext.json: for each line and each side, the value in 2024 and 2025, January-July 2025
and January-July 2026, the change, and the largest suppliers. Measurement only, in current currency
(euros for the EU, dollars for the US), like-for-like months for 2026.

Inputs come from ai-buildout/fetch_comext_ai.py and ai-buildout/fetch_census_ai.py (network
fetchers, never run by the runner). Usage:  python ai-buildout/extend.py
"""
import glob
import json
import os
import re
import sys

import duckdb
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import baci                                                   # country names only

OUT = os.path.join(ROOT, 'out', 'ai_buildout_ext.json')
LINES = ['854231', '854232', '854239', '85414',
         '280461', '280429', '811292', '810320',
         '850421', '850422', '850423', '722511', '722611', '740811',
         '850152', '850153', '841370', '841480',
         '848620', '848610', '848690', '381800', '370790', '903082']
REAL_COUNTRY = re.compile(r'^[1-7]\d{3}$')                    # Census: groupings are '-', 0xxx, 1XXX
# Eurostat partner codes for undisclosed or unallocated trade. QA is Qatar and is NOT among them.
EU_UNSPECIFIED = {'QP', 'QQ', 'QR', 'QS', 'QU', 'QV', 'QW', 'QX', 'QY', 'QZ'}
# Eurostat's own geonomenclature codes that are not ISO 3166 codes.
EU_GEO = {'XS': 'Serbia', 'XK': 'Kosovo', 'XC': 'Ceuta', 'XL': 'Melilla',
          'XI': 'United Kingdom (Northern Ireland)'}
NICE = {'USA': 'the United States', 'Rep. of Korea': 'South Korea', 'Türkiye': 'Türkiye',
        'China, Hong Kong SAR': 'Hong Kong'}
# US ten-digit splits of 2804.29 (Census descriptions, read 2026-09-19): helium, neon, other.
US_RARE_GASES = {'2804290010': 'helium', '2804290020': 'neon'}


def line_of(code):
    code = str(code)
    for l in LINES:
        if code.startswith(l):
            return l
    return None


def eu_frame():
    files = sorted(glob.glob(os.path.join(HERE, 'eu_data', 'comext_*.parquet')))
    con = duckdb.connect()
    d = con.execute("""select PARTNER as partner, PRODUCT_NC as code, PERIOD as period,
                              try_cast(VALUE_EUR as double) as v
                       from read_parquet(?) where TRADE_TYPE = 'E' and FLOW = '1'""", [files]).df()
    d = d[d.period.str[4:6].astype(int).between(1, 12)]
    names = baci.countries().set_index('iso2')['name'].to_dict()
    d['who'] = [('not specified' if p in EU_UNSPECIFIED else EU_GEO.get(p) or NICE.get(names.get(p, p), names.get(p, p)))
                for p in d.partner]
    d['china'] = d.partner == 'CN'
    return d


def us_frame():
    d = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(os.path.join(HERE, 'us_data', 'census_*.parquet')))],
                  ignore_index=True)
    d = d[(d.SUMMARY_LVL == 'DET') & d.CTY_CODE.astype(str).str.match(REAL_COUNTRY)].copy()
    d = d.rename(columns={'I_COMMODITY': 'code', 'month': 'period'})
    d['v'] = pd.to_numeric(d.GEN_VAL_MO, errors='coerce')
    d['who'] = d.CTY_NAME.str.title().str.replace('Korea, South', 'South Korea').replace('United States', 'the United States')
    d['china'] = d.CTY_NAME == 'CHINA'
    return d


def summarise(d, last_month):
    d = d.copy()
    d['line'] = [line_of(c) for c in d.code]
    d = d[d.line.notna()]
    d['year'] = d.period.str[:4].astype(int)
    d['m'] = d.period.str[4:6].astype(int)
    lm = int(last_month[4:])
    out = {}
    for l, g in d.groupby('line'):
        y24, y25 = g[g.year == 2024].v.sum(), g[g.year == 2025].v.sum()
        h25 = g[(g.year == 2025) & (g.m <= lm)].v.sum()
        h26 = g[(g.year == 2026) & (g.m <= lm)].v.sum()
        g25 = g[g.year == 2025]
        by = g25.groupby('who').v.sum().sort_values(ascending=False)
        c26 = g[(g.year == 2026) & (g.m <= lm)]
        out[l] = {
            'value_2024_m': round(y24 / 1e6, 1), 'value_2025_m': round(y25 / 1e6, 1),
            'value_jan_to_last_2025_m': round(h25 / 1e6, 1), 'value_jan_to_last_2026_m': round(h26 / 1e6, 1),
            'change_2025_vs_2024_pct': round(100 * (y25 / y24 - 1), 3) if y24 > 0 else None,
            'change_2026_vs_2025_same_months_pct': round(100 * (h26 / h25 - 1), 3) if h25 > 0 else None,
            'top3_2025': [[w, round(float(x / by.sum()), 4)] for w, x in by.head(3).items()],
            'china_share_2025': round(float(g25[g25.china].v.sum() / by.sum()), 4) if by.sum() > 0 else None,
            'china_share_2026_ytd': round(float(c26[c26.china].v.sum() / c26.v.sum()), 4) if c26.v.sum() > 0 else None,
            'codes': sorted(set(g.code.astype(str))),
        }
    return out


def main():
    eu, us = eu_frame(), us_frame()
    eu_last, us_last = eu.period.max(), us.period.max()
    doc = {
        'note': 'Imports only, current currency. EU: imports of the 27 member states from countries outside '
                'the EU, euros. US: general imports, dollars. 2026 is compared with the same months of 2025.',
        'eu': {'source': 'Eurostat Comext monthly bulk files (CN8), extra-EU imports', 'currency': 'EUR',
               'first_month': eu.period.min(), 'last_month': eu_last, 'lines': summarise(eu, eu_last)},
        'us': {'source': 'US Census Bureau international trade API, general imports (HS10)', 'currency': 'USD',
               'first_month': us.period.min(), 'last_month': us_last, 'lines': summarise(us, us_last)},
    }
    rg = us[us.code.astype(str).str.startswith('280429') & us.period.str.startswith('2025')]
    tot = rg.v.sum()
    doc['us']['rare_gases_2025_split'] = {
        name: round(float(rg[rg.code.astype(str) == c].v.sum() / tot), 4) for c, name in US_RARE_GASES.items()}
    doc['us']['rare_gases_2025_split']['other'] = round(1 - sum(doc['us']['rare_gases_2025_split'].values()), 4)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(doc, f, indent=1, default=float)
    for side in ('eu', 'us'):
        print(side, doc[side]['first_month'], doc[side]['last_month'], len(doc[side]['lines']), 'lines')
        for l, v in doc[side]['lines'].items():
            print('  %-7s %9.0f %9.0f  %+6s%%  ytd %+6s%%  CN %s  %s' % (
                l, v['value_2024_m'], v['value_2025_m'], v['change_2025_vs_2024_pct'],
                v['change_2026_vs_2025_same_months_pct'], v['china_share_2025'],
                ', '.join('%s %.0f%%' % (w, 100 * s) for w, s in v['top3_2025'])))


if __name__ == '__main__':
    main()

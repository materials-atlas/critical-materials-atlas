# -*- coding: utf-8 -*-
"""Descriptive additions to amendments B and C: where the EU buys its transformers, and the monthly
series behind both records.

The filed analyses (analysis_eu.py, analysis_us.py) compare periods. These two descriptive series come
from the same downloads and are added after the fact, logged in each amendment's deviations:

  * EU imports of transformers (8504.21-.23) from outside the EU, by origin, 2019 to July 2026 - the
    counterpart of the US table already in the note.
  * The same imports month by month, as a rolling twelve-month total, for the EU and the United
    States, which is the only way to see within-2026 movement without comparing part-years.

Writes out/buildout_origins.json. Usage:  python buildout-study/origins_monthly.py
"""
import glob
import json
import os
import sys

import duckdb
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import baci                                                   # country names only

OUT = os.path.join(ROOT, 'out', 'buildout_origins.json')
TRANSFORMERS = ('850421', '850422', '850423')
# Eurostat partner codes that are not a country, and its own geonomenclature codes.
EU_UNSPECIFIED = {'QP', 'QQ', 'QR', 'QS', 'QU', 'QV', 'QW', 'QX', 'QY', 'QZ'}
EU_GEO = {'XS': 'Serbia', 'XK': 'Kosovo', 'XI': 'United Kingdom (Northern Ireland)'}
NICE = {'USA': 'the United States', 'Rep. of Korea': 'South Korea', 'China, Hong Kong SAR': 'Hong Kong'}
REAL_COUNTRY = r'^[1-7]\d{3}$'                                # US groupings are '-', 0xxx and 1XXX


def eu_rows():
    files = sorted(glob.glob(os.path.join(HERE, 'eu_data', 'comext_*.parquet')))
    con = duckdb.connect()
    d = con.execute("""select PARTNER as par, PERIOD as period,
                              sum(try_cast(VALUE_EUR as double)) as v,
                              sum(try_cast(QUANTITY_KG as double)) as kg
                       from read_parquet(?)
                       where TRADE_TYPE = 'E' and FLOW = '1' and substr(PRODUCT_NC, 1, 6) in (?, ?, ?)
                       group by 1, 2""", [files] + list(TRANSFORMERS)).df()
    # The United Kingdom is excluded on both sides in every year, as in the filed EU analysis
    # (amendment B, deviation 5), so "outside the EU" means the same partners throughout.
    d = d[~d.par.isin(['GB', 'XI'])]
    d = d[d.period.str[4:6].astype(int).between(1, 12)]
    names = baci.countries().set_index('iso2')['name'].to_dict()
    d['who'] = [('not specified' if p in EU_UNSPECIFIED else EU_GEO.get(p) or NICE.get(names.get(p, p), names.get(p, p)))
                for p in d.par]
    return d


def us_rows():
    files = [f for f in sorted(glob.glob(os.path.join(HERE, 'us_data', 'census_*.parquet')))
             if os.path.basename(f).split('_')[1] in TRANSFORMERS]
    d = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    d = d[(d.SUMMARY_LVL == 'DET') & d.CTY_CODE.astype(str).str.match(REAL_COUNTRY)].copy()
    d['v'] = pd.to_numeric(d.GEN_VAL_MO, errors='coerce')
    d['who'] = d.CTY_NAME.str.title().str.replace('Korea, South', 'South Korea')
    d['period'] = d.month
    return d.groupby(['who', 'period'], as_index=False).v.sum()


def by_year(d, first=2019, scale=1e6, kg=False):
    d = d.copy()
    d['year'] = d.period.str[:4].astype(int)
    out = {}
    for y, g in d[d.year >= first].groupby('year'):
        tot = g.v.sum()
        by = g.groupby('who').v.sum().sort_values(ascending=False)
        row = {'value_m': round(float(tot) / scale, 1),
               'top3': [[w, round(float(x / tot), 4)] for w, x in by.head(3).items()],
               'china_share': round(float(by.get('China', 0.0) / tot), 4),
               'partners_above_1pct': int((by / tot >= 0.01).sum())}
        if kg and 'kg' in g:
            t = g.kg.sum(skipna=True)
            row['tonnes'] = round(float(t) / 1000.0, 0) if t and t > 0 else None
        out[int(y)] = row
    return out


def rolling12(d, scale=1e6):
    """A twelve-month total ending in each month: the only honest way to read part-years."""
    s = d.groupby('period').v.sum().sort_index()
    s = s[s.index >= '201801']
    r = s.rolling(12).sum().dropna()
    return {p: round(float(v) / scale, 1) for p, v in r.items()}


def main():
    eu, us = eu_rows(), us_rows()
    doc = {
        'note': 'Descriptive, added after the filed analyses from the same downloads; logged as '
                'deviations in AMENDMENT_EU_2026.md and AMENDMENT_US_2026.md. EU: imports of '
                'transformers 8504.21-.23 from outside the EU, euros, United Kingdom excluded in '
                'every year. US: general imports of the same lines, dollars. Current prices.',
        'eu_transformer_origins': by_year(eu, kg=True),
        'us_transformer_origins': by_year(us),
        'eu_transformers_rolling12_meur': rolling12(eu),
        'us_transformers_rolling12_musd': rolling12(us),
        'last_month': {'eu': eu.period.max(), 'us': us.period.max()},
    }
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(doc, f, indent=1, default=float)
    for y, v in doc['eu_transformer_origins'].items():
        print('EU %s  EUR %8.1fm  China %5.1f%%  %s' % (
            y, v['value_m'], 100 * v['china_share'],
            ', '.join('%s %.0f%%' % (w, 100 * s) for w, s in v['top3'])))
    r = doc['eu_transformers_rolling12_meur']
    k = sorted(r)
    print('EU rolling 12m: %s %.0fm -> %s %.0fm' % (k[0], r[k[0]], k[-1], r[k[-1]]))
    r = doc['us_transformers_rolling12_musd']
    k = sorted(r)
    print('US rolling 12m: %s %.0fm -> %s %.0fm' % (k[0], r[k[0]], k[-1], r[k[-1]]))
    print('wrote', OUT)


if __name__ == '__main__':
    main()

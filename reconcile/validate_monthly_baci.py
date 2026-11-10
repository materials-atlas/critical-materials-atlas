# -*- coding: utf-8 -*-
"""Does the monthly BACI reproduce CEPII's yearly BACI where the two overlap?

Sums the monthly reconciled flows of monthly_baci.py to calendar years and compares them, flow by
flow (exporter, importer, HS6, year), with BACI_HS17_V202601 for the years both hold. BACI's v is
in thousand USD and q in tonnes; ours are USD and kg.

    python reconcile/validate_monthly_baci.py --monthly raw/monthly_baci_slice --years 2019 2024 [--codes 260300 ...]

Reports, per year: flows in both, in ours only, in BACI only; the share of BACI's value our sum
covers; the median of ours/BACI; the share of flows within 10% and 25%; the correlation of logs.
The product filter matters: a slice run only holds the slice's codes, and BACI must be filtered
to the same codes or "BACI only" is meaningless.
"""
import argparse
import os
import sys
import zipfile

import duckdb
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BACI_ZIP = os.path.join(ROOT, 'raw', 'baci', 'BACI_HS17_V202601.zip')
COUNTRIES = os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--monthly', required=True)
    ap.add_argument('--years', nargs=2, type=int, default=[2019, 2024])
    ap.add_argument('--codes', nargs='*', help='HS6 codes to restrict BACI to (default: the codes present in the monthly output)')
    a = ap.parse_args()
    con = duckdb.connect()
    con.execute("SET memory_limit = '3GB'")
    mon = a.monthly.replace(chr(92), '/')
    con.execute("""CREATE TABLE ours AS
        SELECT period // 100 AS t, exporter, importer, hs6, SUM(v) / 1000.0 AS v_ours, SUM(q) / 1000.0 AS q_ours,
               COUNT(*) AS months, SUM(CASE WHEN basis = 'both' THEN 1 ELSE 0 END) AS months_both
        FROM read_parquet('%s/2*.parquet') WHERE period // 100 BETWEEN %d AND %d
        GROUP BY 1, 2, 3, 4""" % (mon, a.years[0], a.years[1]))
    codes = a.codes or [r[0] for r in con.execute("SELECT DISTINCT hs6 FROM ours").fetchall()]
    cm = pd.read_csv(COUNTRIES, dtype=str); cm.columns = [c.lower() for c in cm.columns]
    cm = cm.dropna(subset=['country_iso3']); cm['code'] = cm.country_code.astype(int)
    con.register('cm', cm[['code', 'country_iso3']])
    z = zipfile.ZipFile(BACI_ZIP)
    frames = []
    for y in range(a.years[0], a.years[1] + 1):
        name = 'BACI_HS17_Y%d_V202601.csv' % y
        if name not in z.namelist():
            continue
        with z.open(name) as fh:
            for chunk in pd.read_csv(fh, dtype={'k': str}, chunksize=2_000_000):
                frames.append(chunk[chunk.k.isin(codes)])
    b = pd.concat(frames, ignore_index=True)
    con.register('baci_raw', b)
    con.execute("""CREATE TABLE baci AS
        SELECT t, e.country_iso3 AS exporter, i.country_iso3 AS importer, k AS hs6, v AS v_baci, q AS q_baci
        FROM baci_raw JOIN cm e ON baci_raw.i = e.code JOIN cm i ON baci_raw.j = i.code""")
    print('BACI rows in scope: %s   ours: %s   codes: %d   years %d-%d' % (
        format(len(b), ','), format(con.execute("SELECT count(*) FROM ours").fetchall()[0][0], ','), len(codes), *a.years))
    print()
    print('year   both   ours_only  baci_only  value_cov  median_ratio  within10%%  within25%%  corr_ln  val_ours/baci')
    for (t, both, oo, bo, cov, med, w10, w25, corr, ratio) in con.execute("""
        WITH j AS (SELECT COALESCE(o.t, b.t) AS t, o.v_ours, b.v_baci FROM ours o FULL JOIN baci b USING (t, exporter, importer, hs6))
        SELECT t, count(*) FILTER (WHERE v_ours IS NOT NULL AND v_baci IS NOT NULL) AS both,
               count(*) FILTER (WHERE v_baci IS NULL) AS ours_only, count(*) FILTER (WHERE v_ours IS NULL) AS baci_only,
               sum(v_baci) FILTER (WHERE v_ours IS NOT NULL) / sum(v_baci) AS value_cov,
               median(v_ours / v_baci) FILTER (WHERE v_ours IS NOT NULL AND v_baci IS NOT NULL) AS med,
               avg(CASE WHEN abs(v_ours / v_baci - 1) <= 0.10 THEN 1.0 ELSE 0.0 END) FILTER (WHERE v_ours IS NOT NULL AND v_baci IS NOT NULL) AS w10,
               avg(CASE WHEN abs(v_ours / v_baci - 1) <= 0.25 THEN 1.0 ELSE 0.0 END) FILTER (WHERE v_ours IS NOT NULL AND v_baci IS NOT NULL) AS w25,
               corr(ln(v_ours), ln(v_baci)) FILTER (WHERE v_ours IS NOT NULL AND v_baci IS NOT NULL) AS c,
               sum(v_ours) FILTER (WHERE v_baci IS NOT NULL) / sum(v_baci) FILTER (WHERE v_ours IS NOT NULL) AS ratio
        FROM j GROUP BY 1 ORDER BY 1""").fetchall():
        print('%d  %7s  %9s  %9s     %5.1f%%        %5.3f     %5.1f%%     %5.1f%%    %5.3f     %5.3f' % (
            t, format(both, ','), format(oo, ','), format(bo, ','), 100 * (cov or 0), med or 0, 100 * (w10 or 0), 100 * (w25 or 0), corr or 0, ratio or 0))
    print()
    print('by basis (how the flow was reconciled), all years, flows in both:')
    for r in con.execute("""
        SELECT CASE WHEN o.months_both = o.months THEN 'both every month' WHEN o.months_both = 0 THEN 'one side only' ELSE 'mixed' END AS basis,
               count(*), median(v_ours / v_baci), avg(CASE WHEN abs(v_ours / v_baci - 1) <= 0.25 THEN 1.0 ELSE 0.0 END)
        FROM ours o JOIN baci b USING (t, exporter, importer, hs6) GROUP BY 1 ORDER BY 2 DESC""").fetchall():
        print('  %-18s n=%-9s median ratio %.3f   within 25%%: %.1f%%' % (r[0], format(r[1], ','), r[2], 100 * r[3]))


if __name__ == '__main__':
    main()

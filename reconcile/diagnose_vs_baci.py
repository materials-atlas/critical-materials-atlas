# -*- coding: utf-8 -*-
"""Why do we not match BACI? Read CEPII's procedure off its own output.

BACI is built from Comtrade's ANNUAL declarations. Where we hold the same annual declarations
(the atlas pulled them for its 54 codes: raw/comtrade/comtrade_<year>.csv), each BACI flow can
be set against the exporter's and the importer's raw report, and the three things the method
does become directly visible:

  A. flows only the exporter declared     BACI should equal that declaration        -> is the raw data the same?
  B. flows only the importer declared     raw import / BACI = the CIF rate CEPII used -> their fobization
  C. flows both declared                  where BACI sits between the two reports     -> their weights

and, apart from the method, the question the monthly series raises:

  D. the months of a year summed, against the same reporter's annual declaration     -> is monthly data the same data?

    python reconcile/diagnose_vs_baci.py --year 2024 [--slice ~/comtrade/crm_monthly.parquet]
"""
import argparse
import os
import sys
import zipfile

import duckdb
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from hs_concordance import conversion

BACI_ZIP = os.path.join(ROOT, 'raw', 'baci', 'BACI_HS17_V202601.zip')
COUNTRIES = os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv')
GEO = os.path.join(ROOT, 'raw', 'geodist', 'dist_cepii.xls')


def q(con, sql):
    return con.execute(sql).fetchall()


def quant(con, expr, table, where='TRUE'):
    r = q(con, "SELECT count(*), quantile_cont(%s, 0.05), quantile_cont(%s, 0.25), median(%s), quantile_cont(%s, 0.75), "
               "quantile_cont(%s, 0.95) FROM %s WHERE %s" % (expr, expr, expr, expr, expr, table, where))[0]
    return 'n=%s  p5 %.3f  p25 %.3f  median %.3f  p75 %.3f  p95 %.3f' % (format(r[0], ','), *[x if x is not None else float('nan') for x in r[1:]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--year', type=int, default=2024)
    ap.add_argument('--slice', help='monthly raw lines (for part D)')
    a = ap.parse_args()
    y = a.year
    con = duckdb.connect(); con.execute("SET memory_limit = '3GB'")
    raw = os.path.join(ROOT, 'raw', 'comtrade', 'comtrade_%d.csv' % y).replace(chr(92), '/')
    cm = pd.read_csv(COUNTRIES, dtype=str); cm.columns = [c.lower() for c in cm.columns]
    cm = cm.dropna(subset=['country_iso3']); cm['code'] = cm.country_code.astype(int)
    con.register('cm', cm[['code', 'country_iso3']])
    conv = conversion(2022, 2017)
    con.register('conv', pd.DataFrame({'k22': list(conv.keys()), 'k17': list(conv.values())}))
    # the annual declarations: the file holds the total line several times and its breakdowns; the
    # total is the largest value of a key
    con.execute("""CREATE TABLE ann AS
        SELECT reporter, partner, lpad(CAST(cmd AS VARCHAR), 6, '0') AS k, flow, max(value) AS v, max(netwgt) AS kg
        FROM read_csv('%s', header=true, types={'cmd': 'VARCHAR'}) WHERE partner <> 0 AND flow IN ('M', 'X') AND value > 0
        GROUP BY 1, 2, 3, 4""" % raw)
    print('annual raw %d: %s declarations, %d reporters, %d codes' % (y, *[format(v, ',') if i == 0 else v for i, v in enumerate(
        q(con, "SELECT count(*), count(DISTINCT reporter), count(DISTINCT k) FROM ann")[0])]))
    changed = q(con, "SELECT count(DISTINCT a.k) FROM ann a JOIN conv c ON c.k22 = a.k WHERE c.k17 <> a.k")[0][0]
    print('codes among them whose number differs between HS 2022 and HS 2017: %d (BACI is HS 2017; converted)' % changed)
    con.execute("""CREATE TABLE pairs AS
        WITH x AS (SELECT e.country_iso3 AS exporter, i.country_iso3 AS importer, COALESCE(c.k17, a.k) AS k, sum(v) AS vx, sum(kg) AS qx
                   FROM ann a JOIN cm e ON a.reporter = e.code JOIN cm i ON a.partner = i.code LEFT JOIN conv c ON c.k22 = a.k
                   WHERE flow = 'X' GROUP BY 1, 2, 3),
             m AS (SELECT e.country_iso3 AS exporter, i.country_iso3 AS importer, COALESCE(c.k17, a.k) AS k, sum(v) AS vm, sum(kg) AS qm
                   FROM ann a JOIN cm i ON a.reporter = i.code JOIN cm e ON a.partner = e.code LEFT JOIN conv c ON c.k22 = a.k
                   WHERE flow = 'M' GROUP BY 1, 2, 3)
        SELECT COALESCE(x.exporter, m.exporter) AS exporter, COALESCE(x.importer, m.importer) AS importer, COALESCE(x.k, m.k) AS k, vx, vm, qx, qm
        FROM x FULL JOIN m ON x.exporter = m.exporter AND x.importer = m.importer AND x.k = m.k
        WHERE COALESCE(x.exporter, m.exporter) <> COALESCE(x.importer, m.importer)""")
    codes = [r[0] for r in q(con, "SELECT DISTINCT k FROM pairs")]
    z = zipfile.ZipFile(BACI_ZIP); fr = []
    with z.open('BACI_HS17_Y%d_V202601.csv' % y) as fh:
        for ch in pd.read_csv(fh, dtype={'k': str}, chunksize=2_000_000):
            fr.append(ch[ch.k.isin(codes)])
    con.register('braw', pd.concat(fr))
    con.execute("""CREATE TABLE baci AS SELECT e.country_iso3 AS exporter, i.country_iso3 AS importer, k, sum(v) * 1000.0 AS vb, sum(q) * 1000.0 AS qb
                   FROM braw JOIN cm e ON braw.i = e.code JOIN cm i ON braw.j = i.code GROUP BY 1, 2, 3""")
    con.execute("""CREATE TABLE j AS SELECT COALESCE(p.exporter, b.exporter) AS exporter, COALESCE(p.importer, b.importer) AS importer,
                          COALESCE(p.k, b.k) AS k, vx, vm, qx, qm, vb, qb
                   FROM pairs p FULL JOIN baci b USING (exporter, importer, k)""")
    tot = q(con, "SELECT count(*), sum(vb)/1e9 FROM j WHERE vb IS NOT NULL")[0]
    print()
    print('BACI %d on these codes: %s flows, %.1f bn USD. Against the annual raw declarations:' % (y, format(tot[0], ','), tot[1]))
    for lab, cond in (('only the exporter declared', 'vx IS NOT NULL AND vm IS NULL'), ('only the importer declared', 'vx IS NULL AND vm IS NOT NULL'),
                      ('both declared', 'vx IS NOT NULL AND vm IS NOT NULL'), ('NEITHER declared (not in our raw data)', 'vx IS NULL AND vm IS NULL')):
        r = q(con, "SELECT count(*), COALESCE(sum(vb), 0)/1e9 FROM j WHERE vb IS NOT NULL AND %s" % cond)[0]
        print('  %-42s %8s flows  %7.1f bn  (%.1f%% of value)' % (lab, format(r[0], ','), r[1], 100 * r[1] / tot[1]))
    r = q(con, "SELECT count(*), sum(COALESCE(vx, vm))/1e9 FROM j WHERE vb IS NULL")[0]
    print('  raw declarations with NO BACI flow:        %8s flows  %7.1f bn' % (format(r[0], ','), r[1] or 0))

    print()
    print('A. only the exporter declared: BACI / exporter value')
    print('   ', quant(con, 'vb / vx', 'j', 'vb IS NOT NULL AND vx IS NOT NULL AND vm IS NULL'))
    for tol in (0.001, 0.01, 0.05):
        s = q(con, "SELECT avg(CASE WHEN abs(vb / vx - 1) <= %f THEN 1.0 ELSE 0.0 END) FROM j WHERE vb IS NOT NULL AND vx IS NOT NULL AND vm IS NULL" % tol)[0][0]
        print('    equal within %.1f%%: %.1f%% of flows' % (100 * tol, 100 * s))
    print()
    print('B. only the importer declared: importer value / BACI  (= 1 + the CIF rate CEPII removed)')
    print('   ', quant(con, 'vm / vb', 'j', 'vb IS NOT NULL AND vx IS NULL AND vm IS NOT NULL'))
    s = q(con, """SELECT avg(CASE WHEN abs(vm / vb - 1) <= 0.001 THEN 1.0 ELSE 0.0 END), avg(CASE WHEN vm / vb BETWEEN 1.001 AND 1.25 THEN 1.0 ELSE 0.0 END),
                         avg(CASE WHEN vm / vb < 0.999 THEN 1.0 ELSE 0.0 END), avg(CASE WHEN vm / vb > 1.25 THEN 1.0 ELSE 0.0 END)
                  FROM j WHERE vb IS NOT NULL AND vx IS NULL AND vm IS NOT NULL""")[0]
    print('    not fobized (ratio = 1): %.1f%%   rate between 0.1%% and 25%%: %.1f%%   below 1: %.1f%%   above 1.25: %.1f%%' % tuple(100 * v for v in s))
    # the rate against distance, where a rate was applied
    try:
        g = pd.read_excel(GEO, engine='calamine')
    except Exception:
        g = pd.read_excel(GEO)
    g.columns = [c.lower() for c in g.columns]
    for c in ('dist', 'distw', 'contig'):
        g[c] = pd.to_numeric(g[c], errors='coerce')
    con.register('geo', g[['iso_o', 'iso_d', 'dist', 'distw', 'contig']])
    print('    the rate CEPII removed, by distance band (flows with a rate between 0.1% and 25%):')
    for r in q(con, """SELECT CASE WHEN g.dist < 1000 THEN '1  under 1,000 km' WHEN g.dist < 3000 THEN '2  1-3,000 km' WHEN g.dist < 8000 THEN '3  3-8,000 km' ELSE '4  over 8,000 km' END AS band,
                              count(*), median(vm / vb) - 1, avg(vm / vb) - 1
                       FROM j JOIN geo g ON g.iso_o = j.exporter AND g.iso_d = j.importer
                       WHERE vb IS NOT NULL AND vx IS NULL AND vm / vb BETWEEN 1.001 AND 1.25 GROUP BY 1 ORDER BY 1"""):
        print('      %-18s n=%-7s median rate %.1f%%  mean %.1f%%' % (r[0][3:], format(r[1], ','), 100 * r[2], 100 * r[3]))
    print('    by importer (largest, share not fobized / median rate):')
    for r in q(con, """SELECT importer, count(*), avg(CASE WHEN abs(vm / vb - 1) <= 0.001 THEN 1.0 ELSE 0.0 END), median(vm / vb) - 1
                       FROM j WHERE vb IS NOT NULL AND vx IS NULL AND vm IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 14"""):
        print('      %s n=%-6s not fobized %.0f%%  median rate %.1f%%' % (r[0], format(r[1], ','), 100 * r[2], 100 * r[3]))

    print()
    print('C. both declared: where BACI sits. lambda = (BACI - importer value) / (exporter value - importer value);')
    print('   1 = the exporter\'s report, 0 = the importer\'s raw CIF report, slightly below 0..1 once freight is out.')
    con.execute("""CREATE TABLE c AS SELECT *, (vb - vm) / NULLIF(vx - vm, 0) AS lam FROM j
                   WHERE vb IS NOT NULL AND vx IS NOT NULL AND vm IS NOT NULL AND abs(ln(vx / vm)) > 0.10""")
    print('   ', quant(con, 'lam', 'c'))
    for lab, cond in (('at the exporter (0.95..1.05)', 'lam BETWEEN 0.95 AND 1.05'), ('at the importer, net of freight (-0.6..0.05)', 'lam BETWEEN -0.6 AND 0.05'),
                      ('in between (0.05..0.95)', 'lam > 0.05 AND lam < 0.95'), ('outside both', 'lam < -0.6 OR lam > 1.05')):
        s = q(con, "SELECT avg(CASE WHEN %s THEN 1.0 ELSE 0.0 END) FROM c" % cond)[0][0]
        print('    %-46s %.1f%%' % (lab, 100 * s))
    print('    histogram of lambda (flows whose two reports differ by more than 10%):')
    for r in q(con, """SELECT floor(GREATEST(LEAST(lam, 1.25), -0.5) * 10) / 10 AS b, count(*) FROM c GROUP BY 1 ORDER BY 1"""):
        print('      %5.1f  %s' % (r[0], '#' * int(60 * r[1] / max(1, q(con, 'SELECT count(*) FROM c')[0][0]) * 4)))
    print('    mean lambda by exporter (largest exporters; near 1 = CEPII trusts this exporter):')
    for r in q(con, "SELECT exporter, count(*), median(lam), avg(CASE WHEN lam BETWEEN 0.05 AND 0.95 THEN 1.0 ELSE 0.0 END) FROM c GROUP BY 1 ORDER BY 2 DESC LIMIT 12"):
        print('      %s n=%-6s median lambda %.2f   strictly in between: %.0f%%' % (r[0], format(r[1], ','), r[2], 100 * r[3]))

    if a.slice:
        print()
        print('D. the months of %d summed against the same reporter\'s ANNUAL declaration (same partner, code, flow)' % y)
        sl = os.path.expanduser(a.slice).replace(chr(92), '/')
        con.execute("""CREATE TABLE mon AS SELECT reporterCode AS reporter, partnerCode AS partner, cmdCode AS k, flowCode AS flow,
                              sum(primaryValue) AS v, count(DISTINCT period) AS n_months
                       FROM read_parquet('%s') WHERE period / 100 = %d AND customsCode = 'C00' AND motCode = 0 AND partner2Code = 0
                         AND partnerCode <> 0 AND flowCode IN ('M', 'X') AND primaryValue > 0 GROUP BY 1, 2, 3, 4""" % (sl, y))
        con.execute("CREATE TABLE repm AS SELECT reporter, count(DISTINCT n_months) AS x, max(n_months) AS months FROM mon GROUP BY 1")
        r = q(con, """SELECT (SELECT count(DISTINCT reporter) FROM ann), (SELECT count(DISTINCT reporter) FROM mon),
                             (SELECT count(DISTINCT reporter) FROM ann WHERE reporter NOT IN (SELECT reporter FROM mon)),
                             (SELECT sum(v)/1e9 FROM ann WHERE reporter NOT IN (SELECT reporter FROM mon)), (SELECT sum(v)/1e9 FROM ann)""")[0]
        print('    reporters: %d annual, %d monthly; %d report annually only, holding %.1f of %.1f bn USD of annual declarations (%.1f%%)' % (
            r[0], r[1], r[2], r[3] or 0, r[4], 100 * (r[3] or 0) / r[4]))
        full = q(con, "SELECT count(*) FROM repm WHERE months = 12")[0][0]
        print('    monthly reporters with all 12 months of %d: %d of %d' % (y, full, r[1]))
        con.execute("""CREATE TABLE cmp AS SELECT a.reporter, a.partner, a.k, a.flow, a.v AS va, m.v AS vmn, m.n_months
                       FROM ann a LEFT JOIN mon m USING (reporter, partner, k, flow)
                       WHERE a.reporter IN (SELECT reporter FROM repm WHERE months = 12)""")
        s = q(con, """SELECT count(*), sum(va)/1e9, count(vmn), sum(va) FILTER (WHERE vmn IS NOT NULL)/1e9, sum(vmn)/1e9 FROM cmp""")[0]
        print('    for reporters with 12 months: %s annual lines (%.1f bn); %s also in the monthly sums (%.1f bn annual vs %.1f bn monthly)' % (
            format(s[0], ','), s[1], format(s[2], ','), s[3], s[4]))
        print('    monthly sum / annual declaration, line by line:', quant(con, 'vmn / va', 'cmp', 'vmn IS NOT NULL'))
        for tol in (0.001, 0.01, 0.05, 0.25):
            v = q(con, "SELECT avg(CASE WHEN abs(vmn / va - 1) <= %f THEN 1.0 ELSE 0.0 END) FROM cmp WHERE vmn IS NOT NULL" % tol)[0][0]
            print('      equal within %.1f%%: %.1f%% of lines' % (100 * tol, 100 * v))
        print('    worst reporters (value-weighted gap, 12-month reporters):')
        for r in q(con, """SELECT reporter, sum(va)/1e9, sum(vmn)/1e9, sum(vmn)/sum(va) FROM cmp WHERE vmn IS NOT NULL GROUP BY 1
                           HAVING sum(va) > 1e9 ORDER BY abs(ln(sum(vmn)/sum(va))) DESC LIMIT 8"""):
            print('      reporter %-4d annual %.1f bn  monthly %.1f bn  ratio %.3f' % r)


if __name__ == '__main__':
    main()

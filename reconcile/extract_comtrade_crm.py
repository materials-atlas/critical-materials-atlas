# -*- coding: utf-8 -*-
"""The atlas's UN Comtrade rows, cut out of the bulk corpus - so the atlas stops asking the UN API
for data the bulk corpus already holds.

Until Nov 2026 the nightly refresh pulled the atlas's codes month by month from the Comtrade DATA
API (pipeline/pull_comtrade.py -> pipeline/data/comtrade_cache.jsonl). The bulk pull
(reconcile/pull_comtrade_bulk.py) now holds every reporter, every month, every product from 2000,
and is kept current by its --recheck pass. Two downloads of the same UN database, sharing one key
and one daily call quota, was waste. This script is the bridge: it reads the corpus and writes one
small parquet per year with exactly the rows the API pull used to fetch, in the API's field names,
so adapter_comtrade.read_cache() reads them unchanged.

WHICH ROWS: the atlas's tracked HS6 codes (concordance.tracked_hs6_set(), the same list the API
call asked for), imports and exports (flowCode M, X - re-exports and re-imports are separate flows
in the bulk files and were never requested), and the TOTAL cell only:
  motCode 0      all modes of transport (the bulk files also carry each mode)
  partner2Code 0 all second partners - OR equal to the partner. Some reporters (Switzerland,
                 Hungary, ...) file every import with the second partner filled in and no 0 row;
                 requiring 0 dropped them (found 18 Nov 2026 against the API store). This is the
                 adapter's own rule, and its max-value dedup keeps the total where both exist.
  customsCode C00 all customs procedures
  partnerCode <> 0 (0 is World, an aggregate the adapter drops anyway)
The bulk files break a cell out by all three; the API's default answer was the total. Taking the
total here is what keeps one cell one row (see the 7 Sep 2026 bug in adapter_comtrade.normalize).

INCREMENTAL: a year is re-cut only when a bulk file of that year is newer than its extract, so the
nightly run re-reads the two or three years the recheck touched, not 27.

Run (on the machine holding the corpus):
  python reconcile/extract_comtrade_crm.py [--bulk DIR] [--out DIR] [--years 2025 2026] [--force]
Defaults: --bulk $CMA_BULK_DIR or <repo>/raw/comtrade_bulk, --out <repo>/raw/comtrade_bulk_crm.
"""
import argparse
import glob
import os
import sys
import time

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import concordance  # noqa: E402

BULK = os.environ.get('CMA_BULK_DIR', os.path.join(ROOT, 'raw', 'comtrade_bulk'))
OUT = os.environ.get('CMA_BULK_CRM_DIR', os.path.join(ROOT, 'raw', 'comtrade_bulk_crm'))


def newest(paths):
    return max((os.path.getmtime(p) for p in paths), default=0.0)


def cut_year(con, files, codes, dest):
    lst = ','.join("'%s'" % c for c in codes)
    src = '[' + ','.join("'%s'" % f.replace('\\', '/') for f in files) + ']'
    tmp = dest + '.tmp'
    con.execute(f"""
        COPY (
          SELECT period, reporterCode, partnerCode, partner2Code, cmdCode, flowCode,
                 primaryValue, netWgt, isNetWgtEstimated, motCode, customsCode,
                 isAggregate, isReported, FOBValue AS fobvalue, CIFValue AS cifvalue
          FROM read_parquet({src}, union_by_name=true)
          WHERE cmdCode IN ({lst}) AND flowCode IN ('M', 'X')
            AND motCode = 0 AND (partner2Code = 0 OR partner2Code = partnerCode)
            AND customsCode = 'C00' AND partnerCode <> 0
          ORDER BY period, reporterCode, cmdCode, partnerCode, flowCode
        ) TO '{tmp.replace(chr(92), '/')}' (FORMAT PARQUET, COMPRESSION ZSTD)""")
    os.replace(tmp, dest)            # never leave a half file looking complete
    return con.execute(f"SELECT count(*) FROM read_parquet('{dest.replace(chr(92), '/')}')").fetchone()[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bulk', default=BULK)
    ap.add_argument('--out', default=OUT)
    ap.add_argument('--years', nargs='*', help='only these years (default: every year present)')
    ap.add_argument('--force', action='store_true', help='re-cut even when the extract is current')
    a = ap.parse_args()
    import duckdb
    con = duckdb.connect()
    con.execute("SET memory_limit='3GB'")
    con.execute('SET threads=3')
    codes = sorted(concordance.tracked_hs6_set())
    os.makedirs(a.out, exist_ok=True)
    years = a.years or sorted(d for d in os.listdir(a.bulk)
                              if d.isdigit() and os.path.isdir(os.path.join(a.bulk, d)))
    cut = 0
    for y in years:
        files = sorted(glob.glob(os.path.join(a.bulk, y, '*.parquet')))
        # A 0-byte file is a download that never reached the disk (the power cut of 14 Nov 2026
        # left seven). The downloader fetches it again on its next start; here it is skipped and
        # named, so a year is never silently cut without one of its countries.
        empty = [f for f in files if os.path.getsize(f) < 100]
        if empty:
            print('%s  WARNING %d empty file(s) skipped: %s' % (y, len(empty), ', '.join(
                os.path.basename(f) for f in empty)), flush=True)
            files = [f for f in files if f not in empty]
        if not files:
            continue
        dest = os.path.join(a.out, '%s.parquet' % y)
        if not a.force and os.path.exists(dest) and os.path.getmtime(dest) >= newest(files):
            continue
        t0 = time.time()
        n = cut_year(con, files, codes, dest)
        cut += 1
        print('%s  %d files -> %s rows  %.0fs' % (y, len(files), format(n, ','), time.time() - t0),
              flush=True)
    print('extract: %d year(s) re-cut, %d codes, -> %s' % (cut, len(codes), a.out))


if __name__ == '__main__':
    main()

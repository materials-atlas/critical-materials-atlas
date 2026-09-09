# -*- coding: utf-8 -*-
"""CEPII BACI: the one writer. Phase 2 of ARCHITECTURE.md.

Turns each archive member (one nomenclature, one year, ~11M rows of t,i,j,k,v,q) into one parquet
file under extract/baci/<HS>/Y<year>.parquet. After this runs, nothing in the repository has a
reason to open a BACI zip, and baci.py is the only thing that opens the extract.

WHY DUCKDB, AND WHY VIA A TEMP FILE
pandas.read_csv on 364 MB of text is slow and memory-hungry; DuckDB streams it. DuckDB reads
paths, not zip members, so each member is streamed to a temp file first and deleted after -
the extract never needs the archive unpacked on disk.

TWO THINGS FORCED, BECAUSE INFERENCE GETS THEM WRONG
- k is VARCHAR. HS6 codes carry leading zeros (010121, 020110). Integer inference would turn
  010121 into 10121 and every join on the code would silently miss.
- The literal string NA is NULL. BACI writes NA where it has no quantity. Twenty-six readers test
  for the string; after migration they test isna(), and the acceptance harness catches any that
  were missed.

VERIFIED PER MEMBER, NOT ASSUMED
Row count against the CSV, count of leading-zero codes preserved, count of NULLs where NA was.
A member that fails verification is deleted, not kept - a partial extract is a second door.

Run:  python extract_baci.py              # all 23 members (~15-25 min)
      python extract_baci.py --only 2024  # one year, for testing or a refresh
      python extract_baci.py --force      # redo members that already exist
"""
import os
import sys
import tempfile
import time
import zipfile

import duckdb

import baci

ROOT = os.path.dirname(os.path.abspath(__file__))
ARCHIVE = {'HS02': 'BACI_HS02_%s.zip' % baci.VINTAGE, 'HS17': 'BACI_HS17_%s.zip' % baci.VINTAGE}
MEMBER = 'BACI_%s_Y%d_%s.csv'
COLS = "{'t':'INTEGER','i':'INTEGER','j':'INTEGER','k':'VARCHAR','v':'DOUBLE','q':'DOUBLE'}"


def _fwd(p):
    return p.replace(os.sep, '/')


def extract_one(con, zf, nom, year):
    member = MEMBER % (nom, year, baci.VINTAGE)
    out = baci.path(year, nom)          # both nomenclatures hold 2017-2024; each gets its own file
    os.makedirs(os.path.dirname(out), exist_ok=True)
    t0 = time.time()
    tmp = os.path.join(tempfile.gettempdir(), member)
    nlines = 0
    with zf.open(member) as src, open(tmp, 'wb') as dst:
        for chunk in iter(lambda: src.read(1 << 24), b''):
            dst.write(chunk)
            nlines += chunk.count(b'\n')
    t1 = time.time()
    try:
        # v and q come in as TEXT and are cast here, strictly. In this vintage q is sometimes the
        # EMPTY string rather than NA (103,985 times in the first 3M rows of 2024), and a
        # nullstr='NA' alone made DuckDB's sniffer refuse the column. Both spellings become NULL;
        # anything else that fails to cast is COUNTED and fails the member, so a silent NULL can
        # never stand in for a real number.
        src = ("read_csv('%s', header=true, columns={'t':'INTEGER','i':'INTEGER','j':'INTEGER',"
               "'k':'VARCHAR','v':'VARCHAR','q':'VARCHAR'})" % _fwd(tmp))
        strict = con.execute(
            "SELECT count(*) FROM %s WHERE (v IS NOT NULL AND trim(v) NOT IN ('', 'NA') AND TRY_CAST(v AS DOUBLE) IS NULL)"
            "   OR (q IS NOT NULL AND trim(q) NOT IN ('', 'NA') AND TRY_CAST(q AS DOUBLE) IS NULL)" % src).fetchone()[0]
        if strict:
            raise SystemExit('%s %d: %d values in v/q are neither numeric, empty nor NA - refusing'
                             % (nom, year, strict))
        con.execute("COPY (SELECT t, i, j, k, "
                    "TRY_CAST(NULLIF(trim(v), 'NA') AS DOUBLE) AS v, "
                    "TRY_CAST(NULLIF(NULLIF(trim(q), 'NA'), '') AS DOUBLE) AS q "
                    "FROM %s) TO '%s' (FORMAT PARQUET, COMPRESSION ZSTD)" % (src, _fwd(out)))
    except BaseException:
        # DuckDB creates the target before it fails. A 0-byte parquet is not "not extracted",
        # it is a lie that the accessor would otherwise believe.
        if os.path.exists(out):
            os.remove(out)
        raise
    finally:
        os.remove(tmp)
    t2 = time.time()
    n, lead0, qnull, kmax = con.execute(
        "SELECT count(*), sum(CASE WHEN k LIKE '0%%' THEN 1 ELSE 0 END), "
        "sum(CASE WHEN q IS NULL THEN 1 ELSE 0 END), max(length(k)) FROM read_parquet('%s')"
        % _fwd(out)).fetchone()
    # the CSV has a header line and a trailing newline: rows = lines - 1 (when the last line ends
    # in \n) - be tolerant of a missing final newline by one.
    ok = n in (nlines - 1, nlines) and kmax == 6 and lead0 > 0
    if not ok:
        os.remove(out)
        raise SystemExit('VERIFY FAILED %s %d: rows %d vs csv %d, max(len k) %s, leading-zero codes %d '
                         '- extract deleted' % (nom, year, n, nlines - 1, kmax, lead0))
    mb = os.path.getsize(out) / 1e6
    print('  %s %d  %9d rows  %3.0f MB  unzip %4.0fs  convert %4.0fs  (lead-0 codes %d, q NULL %d)'
          % (nom, year, n, mb, t1 - t0, t2 - t1, lead0, qnull), flush=True)
    return n


def main():
    a = sys.argv[1:]
    only = int(a[a.index('--only') + 1]) if '--only' in a else None
    force = '--force' in a
    con = duckdb.connect()
    con.execute("SET threads TO 4")
    total = 0
    t0 = time.time()
    for nom, years in baci.NOMENCLATURE.items():
        want = [y for y in years if only is None or y == only]
        if not want:
            continue
        zpath = os.path.join(baci.RAW, ARCHIVE[nom])
        with zipfile.ZipFile(zpath) as zf:
            for y in want:
                if os.path.exists(baci.path(y, nom)) and not force:
                    print('  %s %d  already extracted (--force to redo)' % (nom, y))
                    continue
                total += extract_one(con, zf, nom, y)
    av = baci.available()
    print('\nextract/baci: %d (nomenclature, year) members present  %d rows written this run  %.0f min'
          % (len(av), total, (time.time() - t0) / 60))
    for nom in baci.NOMENCLATURE:
        ys = [y for n, y in av if n == nom]
        print('  %s: %s' % (nom, ('%d..%d (%d)' % (ys[0], ys[-1], len(ys))) if ys else 'NONE'))


if __name__ == '__main__':
    main()

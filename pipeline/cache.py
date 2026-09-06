# -*- coding: utf-8 -*-
"""Per-source canonical-row cache. refresh.py writes each source's validated canonical rows to
pipeline/data/cache/<source>.parquet; build.py just unions the caches. This decouples the slow,
rate-limited pulls from the (now instant) build."""
import os, glob, json, datetime, duckdb
import schema

CACHE_DIR = os.path.join(schema.ROOT, 'pipeline', 'data', 'cache')
MANIFEST = os.path.join(CACHE_DIR, '_manifest.json')


def path(source):
    return os.path.join(CACHE_DIR, f'{source}.parquet')


def _stamp(source, rows):
    """Provenance: record when this source was refreshed + its latest data period."""
    m = {}
    if os.path.exists(MANIFEST):
        try:
            m = json.load(open(MANIFEST))
        except ValueError:
            m = {}
    periods = [r.get('period') for r in rows if r.get('period') is not None]
    m[source] = {'rows': len(rows), 'refreshed_at': datetime.datetime.now().isoformat(timespec='seconds'),
                 'latest_period': max(periods) if periods else None,
                 # the SPAN matters as much as the newest period: a source pinned to one month
                 # looks perfectly fresh by refreshed_at while being useless for reconciliation.
                 'earliest_period': min(periods) if periods else None,
                 'n_periods': len(set(periods)) if periods else 0}
    json.dump(m, open(MANIFEST, 'w'), indent=2, sort_keys=True)


# The natural key of an observation. Two fetches of the same cell are the SAME observation - a
# revision - not two observations, so a merge keeps the newer and drops the older.
OBS_KEY = ['source', 'period', 'reporter', 'partner', 'flow', 'hs6', 'native_code']


def save(source, rows, accumulate=True):
    """Write a source's rows to its cache parquet, MERGING with what is already there.

    It used to overwrite. That was the defect behind the whole 6 Sep reconciliation problem:
    several adapters return exactly one period per run (Comtrade's free endpoint is pinned to a
    single month), so overwriting meant the cache could never hold more than that one month no
    matter how often it refreshed. 81% of our "mirror pairs" turned out to be one month of
    Comtrade compared against itself, and a 51% disagreement rate was computed off it and nearly
    published.

    Now each refresh ADDS its periods to the ones already held, and a cell fetched twice keeps the
    newer row - which is the right treatment for a revision. Repeated refreshes therefore build a
    series instead of replacing one. Pass accumulate=False to force a clean rebuild of a source
    whose history is known to be bad.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    con = duckdb.connect()
    con.execute(schema.DDL.replace('CREATE TABLE flows', 'CREATE TABLE t'))
    ph = ','.join(['?'] * len(schema.COLUMNS))
    con.executemany(f"INSERT INTO t VALUES ({ph})", [[r[c] for c in schema.COLUMNS] for r in rows])

    existing = path(source)
    if accumulate and os.path.exists(existing):
        cols = ', '.join(schema.COLUMNS)
        con.execute(f"""CREATE OR REPLACE TABLE merged AS
          WITH incoming AS (SELECT {cols}, 1 AS vintage FROM t),
               held     AS (SELECT {cols}, 0 AS vintage
                            FROM read_parquet('{existing.replace(chr(92), '/')}')),
               allrows  AS (SELECT * FROM incoming UNION ALL SELECT * FROM held),
               ranked   AS (SELECT *, ROW_NUMBER() OVER (
                              PARTITION BY {', '.join(OBS_KEY)} ORDER BY vintage DESC) AS rn
                            FROM allrows)
          SELECT {cols} FROM ranked WHERE rn = 1""")
        con.execute("DROP TABLE t")
        con.execute("ALTER TABLE merged RENAME TO t")

    tmp = path(source) + '.tmp'
    con.execute(f"COPY (SELECT * FROM t) TO '{tmp.replace(chr(92), '/')}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    os.replace(tmp, path(source))
    # Stamp from what was actually SAVED, not from what came in. With merging on, the incoming
    # batch is one period while the file may now hold many - stamping the batch would report a
    # one-month cache as one month forever, which is the exact blindness this change exists to fix.
    saved = con.execute("SELECT period FROM t").fetchall()
    _stamp(source, [{'period': r[0]} for r in saved])
    return len(saved)


def files():
    return sorted(glob.glob(os.path.join(CACHE_DIR, '*.parquet')))

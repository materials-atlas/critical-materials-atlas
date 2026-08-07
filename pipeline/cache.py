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
                 'latest_period': max(periods) if periods else None}
    json.dump(m, open(MANIFEST, 'w'), indent=2, sort_keys=True)


def save(source, rows):
    """Write a source's canonical rows to its cache parquet (atomic-ish: temp then replace)."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    con = duckdb.connect()
    con.execute(schema.DDL.replace('CREATE TABLE flows', 'CREATE TABLE t'))
    ph = ','.join(['?'] * len(schema.COLUMNS))
    con.executemany(f"INSERT INTO t VALUES ({ph})", [[r[c] for c in schema.COLUMNS] for r in rows])
    tmp = path(source) + '.tmp'
    con.execute(f"COPY (SELECT * FROM t) TO '{tmp.replace(chr(92), '/')}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    os.replace(tmp, path(source))
    _stamp(source, rows)
    return len(rows)


def files():
    return sorted(glob.glob(os.path.join(CACHE_DIR, '*.parquet')))

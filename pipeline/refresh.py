# -*- coding: utf-8 -*-
"""Refresh source caches — the slow, rate-limited pulls, run occasionally / on a schedule (each source
is independent, so the fleet can split them). A source that FAILs its validation gate keeps its old
cache rather than clobbering good data. Afterwards, `python pipeline/build.py` assembles the caches
in seconds.

Usage:  python pipeline/refresh.py [source ...|all]     (default: all)
        python pipeline/refresh.py comexstat hmrc        (just these)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cache
from build import ADAPTERS

BY_KEY = {a.key: a for a in ADAPTERS}


def refresh_one(a):
    res = a.run()
    if res['ok']:
        cache.save(a.key, res['rows'])
        print(f"[OK  ] {a.key:10} {res['period']}  {len(res['rows']):>7,} rows -> cache")
    else:
        print(f"[FAIL] {a.key:10} kept old cache · {'; '.join(res['problems'])}")


def main():
    args = sys.argv[1:] or ['all']
    targets = ADAPTERS if 'all' in args else [BY_KEY[k] for k in args if k in BY_KEY]
    unknown = [k for k in args if k not in BY_KEY and k != 'all']
    if unknown:
        print(f"unknown source(s): {unknown}  ·  known: {sorted(BY_KEY)}")
    print(f"refreshing {len(targets)} source(s) — slow (network pulls + rate limits)...\n")
    for a in targets:
        refresh_one(a)
    print("\ndone. now:  python pipeline/build.py")


if __name__ == '__main__':
    main()

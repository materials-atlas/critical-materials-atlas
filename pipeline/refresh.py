# -*- coding: utf-8 -*-
"""Refresh source caches — the slow, rate-limited pulls, run occasionally / on a schedule (each source
is independent, so the fleet can split them). A source that FAILs its validation gate keeps its old
cache rather than clobbering good data. Afterwards, `python pipeline/build.py` assembles the caches
in seconds.

Usage:  python pipeline/refresh.py [source ...|all] [--periods N|all]   (default: all, 1 period)
        python pipeline/refresh.py comexstat hmrc        (just these)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cache
from build import ADAPTERS

BY_KEY = {a.key: a for a in ADAPTERS}


def refresh_one(a, n_periods=1):
    """Pull the latest n_periods this source offers, newest first.

    It used to pull exactly one - run() takes periods[-1] - and cache.save() overwrote. Between
    them the cache could never hold more than one month per source however often it ran, which is
    how a "monthly five-source mirror reconciliation" ended up being one month of one source
    compared against itself. cache.save now merges, so pulling several periods actually builds a
    series; this is the other half of that fix.
    """
    try:
        periods = a.discover()
    except Exception as e:
        print(f"[FAIL] {a.key:10} discover(): {type(e).__name__}: {e}")
        return
    if not periods:
        print(f"[FAIL] {a.key:10} discover() returned nothing")
        return
    want = periods[-n_periods:] if n_periods > 0 else periods
    print(f"[    ] {a.key:10} {len(periods)} period(s) offered, pulling {len(want)}: "
          f"{want[0]}..{want[-1]}")
    for p in want:
        res = a.run(period=p)
        if res['ok']:
            n = cache.save(a.key, res['rows'])
            print(f"[OK  ] {a.key:10} {res['period']}  {len(res['rows']):>7,} rows -> cache "
                  f"(now {n:,} rows held)")
        else:
            print(f"[FAIL] {a.key:10} {p} kept old cache · {'; '.join(res['problems'])}")


def main():
    args = sys.argv[1:] or ['all']
    n_periods = 1
    for a in list(args):                       # --periods N, or --periods all
        if a.startswith('--periods'):
            v = a.split('=', 1)[1] if '=' in a else args[args.index(a) + 1]
            n_periods = 0 if v == 'all' else int(v)
            args = [x for x in args if not x.startswith('--periods') and x != v]
    args = args or ['all']
    targets = ADAPTERS if 'all' in args else [BY_KEY[k] for k in args if k in BY_KEY]
    unknown = [k for k in args if k not in BY_KEY and k != 'all']
    if unknown:
        print(f"unknown source(s): {unknown}  ·  known: {sorted(BY_KEY)}")
    print(f"refreshing {len(targets)} source(s) — slow (network pulls + rate limits)...\n")
    for a in targets:
        refresh_one(a, n_periods)
    print("\ndone. now:  python pipeline/build.py")


if __name__ == '__main__':
    main()

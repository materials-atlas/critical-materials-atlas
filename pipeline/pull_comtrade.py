# -*- coding: utf-8 -*-
"""Standalone / cron job that GROWS the Comtrade cache — kept out of build.py so builds stay fast.
Comtrade's free tier is strictly rate-limited, so this pulls a small rotation of reporters per run and
appends to comtrade_cache.jsonl; run it occasionally (or on a schedule) and coverage accumulates.

Usage:  python pipeline/pull_comtrade.py [n_reporters]   (default 1; each reporter ~= 6 rate-limited calls)
Then a normal `python pipeline/build.py` folds the accumulated cache into flows.parquet."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adapter_comtrade as ct


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    month = ct.ComtradeAdapter.MONTH
    before = len(ct.read_cache())
    print(f"growing Comtrade cache: {n} reporter(s), month {month} (this is slow — rate-limited)...")
    ct.fetch_batch(month, n_reporters=n)
    after = len(ct.read_cache())
    # coverage summary
    import json
    reps = set()
    for line in (open(ct.CACHE, encoding='utf8') if os.path.exists(ct.CACHE) else []):
        try:
            reps.add(json.loads(line).get('reporterCode'))
        except ValueError:
            pass
    print(f"cache: {before:,} -> {after:,} rows  ({after-before:,} new) · {len(reps)} distinct reporters so far")
    print("next: run  python pipeline/build.py  to fold it into flows.parquet")


if __name__ == '__main__':
    main()

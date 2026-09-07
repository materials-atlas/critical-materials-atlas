# -*- coding: utf-8 -*-
"""One-shot backfill of the whole BACI gap, using the subscription key.

WHY THIS EXISTS SEPARATELY FROM pull_comtrade.py
The nightly rotation is built around the keyless endpoint's constraints: 500 rows per call, so
codes are chunked and flows split, and a run can only afford a slice. With a key the limit is
100,000 records, and the shape of the job changes completely - all 31 codes, both flows and six
months come back in ONE call. The backfill is then ~114 calls, inside a single 500/day allowance,
so it runs once rather than accumulating over weeks.

WHAT THE KEY ALSO FIXES, which matters more than the speed. The keyless endpoint truncates at 500
rows silently - no error, no flag. Measured: Canada, 31 codes, one month, one flow returns exactly
500 without a key and 1,111 with one. Every Comtrade row this project holds was collected through
that cap, so the existing cache is incomplete by construction. This does not just add months; it
replaces truncated months with whole ones.

Run:  python pipeline/backfill_comtrade.py [months_per_call]
Then: python pipeline/refresh.py comtrade  &&  python pipeline/build.py
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adapter_comtrade as ct
import concordance


def main():
    if not ct.API_KEY:
        print('no key at pipeline/.comtrade_key - refusing to run the backfill through the '
              'truncating keyless endpoint, which is what this exists to escape')
        return 1
    per = int(sys.argv[1]) if len(sys.argv) > 1 else ct.MONTHS_PER_CALL
    cal = ct.ComtradeAdapter.calendar()
    blocks = [cal[i:i + per] for i in range(0, len(cal), per)]
    codes = ','.join(sorted(concordance.tracked_hs6_set()))
    before = len(ct.read_cache())
    total = len(blocks) * len(ct.REPORTERS)
    print('backfill: %d months in %d blocks x %d reporters = %d calls (limit 500/day)'
          % (len(cal), len(blocks), len(ct.REPORTERS), total))

    done = rows = fails = 0
    with open(ct.CACHE, 'a', encoding='utf8') as f:
        for blk in blocks:
            period = ','.join(str(m) for m in blk)
            for m49 in ct.REPORTERS:
                d = ct._get(f"{ct.BASE}?reporterCode={m49}&period={period}"
                            f"&cmdCode={codes}&flowCode=M,X")
                got = 0
                for r in (d or {}).get('data', []):
                    f.write(json.dumps({k: r.get(k) for k in
                            ('reporterCode', 'partnerCode', 'partner2Code', 'cmdCode', 'flowCode',
                             'period', 'primaryValue', 'netWgt', 'motCode', 'customsCode',
                             'isAggregate', 'isReported', 'fobvalue', 'cifvalue')}) + '\n')
                    got += 1
                rows += got
                done += 1
                if d is None:
                    fails += 1
                if done % 10 == 0 or got > 5000:
                    print('  %3d/%d calls  %s  reporter %-4s  %6d rows (running total %d)'
                          % (done, total, blk[-1], m49, got, rows), flush=True)
                time.sleep(ct._PAUSE)

    after = len(ct.read_cache())
    print('\ncache %d -> %d rows (+%d). %d calls, %d returned nothing.'
          % (before, after, after - before, done, fails))
    print('next: python pipeline/refresh.py comtrade && python pipeline/build.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())

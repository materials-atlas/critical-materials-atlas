# -*- coding: utf-8 -*-
"""Pull the FULL reporter universe, not the 38 we hand-picked.

WHY ALL OF THEM
The hand-picked list was built for the keyless endpoint, where every reporter cost 8 rate-limited
calls and 38 was already ambitious. With a key the constraint is gone: reporters can be batched
into one call, and a measured 5 reporters x 12 months x 31 codes x both flows returns ~36,000 rows
in 38 seconds - one call out of a 500/day allowance.

The cost of the narrow list is not missing countries, it is missing PAIRS. A mirror comparison
needs both sides, so a corridor where we hold only the exporter is not half-useful, it is
unusable. Cross-source pairs fell to 16% after the last backfill precisely because we went deep
on 38 reporters rather than broad across the panel.

255 reporters, 18 months, 5 per call = ~102 calls. The whole thing fits inside one day.

Run:  python pipeline/backfill_all_reporters.py [reporters_per_call] [months_per_call]
"""
import json, os, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adapter_comtrade as ct
import concordance

FIELDS = ('reporterCode', 'partnerCode', 'partner2Code', 'cmdCode', 'flowCode', 'period',
          'primaryValue', 'netWgt', 'motCode', 'customsCode', 'isAggregate', 'isReported',
          'fobvalue', 'cifvalue')


def reporters():
    """Every reporter Comtrade lists, not the curated 38."""
    u = "https://comtradeapi.un.org/files/v1/app/reference/Reporters.json"
    req = urllib.request.Request(u, headers={'Ocp-Apim-Subscription-Key': ct.API_KEY,
                                             'User-Agent': 'critical-materials-atlas'})
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.load(r)
    rows = d.get('results') or d.get('data') or d
    out = []
    for x in rows:
        v = x.get('id') or x.get('reporterCode') or x.get('code')
        try:
            v = int(v)
        except (TypeError, ValueError):
            continue
        if v > 0:                      # 0 is 'World', not a reporter
            out.append(v)
    return sorted(set(out))


def main():
    if not ct.API_KEY:
        print('no key - this needs pipeline/.comtrade_key')
        return 1
    per_rep = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    per_mon = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    reps = reporters()
    cal = ct.ComtradeAdapter.calendar()
    codes = ','.join(sorted(concordance.tracked_hs6_set()))
    rblocks = [reps[i:i + per_rep] for i in range(0, len(reps), per_rep)]
    mblocks = [cal[i:i + per_mon] for i in range(0, len(cal), per_mon)]
    total = len(rblocks) * len(mblocks)
    before = len(ct.read_cache())
    print('reporters %d in %d blocks x %d month-blocks = %d calls (limit 500/day)'
          % (len(reps), len(rblocks), len(mblocks), total))

    done = rows = empty = 0
    with open(ct.CACHE, 'a', encoding='utf8') as f:
        for mb in mblocks:
            period = ','.join(str(m) for m in mb)
            for rb in rblocks:
                q = (f"{ct.BASE}?reporterCode={','.join(str(r) for r in rb)}&period={period}"
                     f"&cmdCode={codes}&flowCode=M,X")
                d = ct._get(q)
                got = 0
                for r in (d or {}).get('data', []):
                    f.write(json.dumps({k: r.get(k) for k in FIELDS}) + '\n')
                    got += 1
                rows += got
                done += 1
                if not got:
                    empty += 1
                if done % 15 == 0:
                    print('  %3d/%d calls  %s  %7d rows so far' % (done, total, mb[-1], rows),
                          flush=True)
                time.sleep(ct._PAUSE)

    after = len(ct.read_cache())
    print('\ncache %d -> %d rows (+%d) in %d calls; %d returned nothing'
          % (before, after, after - before, done, empty))
    print('next: python pipeline/refresh.py comtrade && python pipeline/build.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())

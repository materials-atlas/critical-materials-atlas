# -*- coding: utf-8 -*-
"""The long backfill: every reporter, every month Comtrade has monthly data for.

SCOPE
Measured, not assumed: monthly HS data begins around 2010 (probed on Germany/740311 - 2010 returns
rows, 2005 does not). Before 1988 there is no HS at all, only SITC, so "no data in 1970" means
"not in this classification" rather than "no trade". That leaves roughly 190 months x 255
reporters - about 4,300 calls at 5 reporters and 12 months each, or nine days inside a 500/day
allowance.

WHY THIS DOES NOT APPEND TO comtrade_cache.jsonl
That file is already 119 MB for eighteen months of thirty-eight reporters, and read_cache() parses
the whole thing on every refresh. Ten times the months and seven times the reporters would put it
past a gigabyte and make every build wait on it. So this writes PARQUET PARTS, one per month-block,
which are columnar, compressed, and readable without parsing the lot.

RESUMABLE BY CONSTRUCTION
A nine-day job will be interrupted - by a reboot, a rate limit, a mistake. State records every
(month-block, reporter-block) pair already fetched, so a re-run skips them. It also counts calls
against a daily budget and stops cleanly rather than burning the allowance and failing at 480.

Run:  python pipeline/backfill_history.py [--budget N] [--from YYYYMM] [--to YYYYMM]
"""
import json, os, sys, time, datetime, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adapter_comtrade as ct
import concordance


NL = chr(10)   # the escape survives every quoting layer this file has been edited through
HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = os.path.join(HERE, 'data', 'comtrade_history')
STATE = os.path.join(HERE, 'data', 'comtrade_history_state.json')
FIELDS = ('reporterCode', 'partnerCode', 'partner2Code', 'cmdCode', 'flowCode', 'period',
          'primaryValue', 'netWgt', 'motCode', 'customsCode', 'isAggregate', 'isReported',
          'fobvalue', 'cifvalue')
MONTHLY_FROM = 201001      # measured floor for monthly HS coverage
DAILY_BUDGET = 450         # of 500, leaving headroom for the nightly job and ad-hoc queries
REPS_PER_CALL = 5
MONTHS_PER_CALL = 12


def load_state():
    if os.path.exists(STATE):
        with open(STATE, encoding='utf8') as f:
            s = json.load(f)
        s['done'] = set(tuple(x) for x in s.get('done', []))
        return s
    return {'done': set(), 'calls': {}}


def save_state(s):
    out = {'done': sorted(list(x) for x in s['done']),
           'empty': sorted(list(x) for x in s.get('empty', ())),
           'calls': s['calls']}
    with open(STATE, 'w', encoding='utf8') as f:
        json.dump(out, f)


def reporters():
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
        if v > 0:
            out.append(v)
    return sorted(set(out))


def months(lo, hi):
    out, y, m = [], lo // 100, lo % 100
    while y * 100 + m <= hi:
        out.append(y * 100 + m)
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return out


def main():
    if not ct.API_KEY:
        print('no key at pipeline/.comtrade_key')
        return 1
    a = sys.argv[1:]
    budget = int(a[a.index('--budget') + 1]) if '--budget' in a else DAILY_BUDGET
    lo = int(a[a.index('--from') + 1]) if '--from' in a else MONTHLY_FROM
    d = datetime.date.today().replace(day=1)
    for _ in range(ct.ComtradeAdapter.LAG_MONTHS):
        d = (d - datetime.timedelta(days=1)).replace(day=1)
    hi = int(a[a.index('--to') + 1]) if '--to' in a else d.year * 100 + d.month

    os.makedirs(PARTS, exist_ok=True)
    st = load_state()
    today = datetime.date.today().isoformat()
    spent = st['calls'].get(today, 0)
    reps = reporters()
    cal = months(lo, hi)
    codes = ','.join(sorted(concordance.tracked_hs6_set()))
    rblocks = [reps[i:i + REPS_PER_CALL] for i in range(0, len(reps), REPS_PER_CALL)]
    mblocks = [cal[i:i + MONTHS_PER_CALL] for i in range(0, len(cal), MONTHS_PER_CALL)]
    # STATE REPAIR. `done` used to mean "we called this block", not "we got an answer". A run that
    # hit the daily quota therefore marked 150 blocks permanently complete on the strength of 150
    # HTTP 403s, and they would never have been fetched again - a silent hole in the history that
    # no later run could find.
    #
    # A block is only genuinely finished if we know its outcome: it wrote a part file, or we
    # recorded that it legitimately holds no rows. Anything else goes back in the queue, which
    # also repairs state written under the old, wrong definition.
    # STATE IS KEYED ON WHAT A BLOCK IS, NOT WHERE IT SITS. It used to be (month-index, reporter-
    # index), both computed from --from and the reporter list of the day. Change --from to reach
    # further back and every index shifts: block 0 stops meaning 2010 and starts meaning 2000, and
    # the state would have skipped the new decade as done. The part files were always named by
    # (first month, first reporter); the state now is too, so any range can be added later.
    key = lambda mi, ri: (mblocks[mi][0], rblocks[ri][0])
    st['empty'] = set(tuple(x) for x in st.get('empty', []))
    proven = set()
    for mi in range(len(mblocks)):
        for ri in range(len(rblocks)):
            if key(mi, ri) in st['empty'] or os.path.exists(
                    os.path.join(PARTS, 'p_%d_%d.parquet' % (mblocks[mi][0], rblocks[ri][0]))):
                proven.add(key(mi, ri))
    # Only blocks INSIDE this run's range can be judged here. A block from another range - the
    # 2010-2024 history while running 2000-2009 - is not "lost" because this run did not look at
    # it; it is kept exactly as recorded. The first version dropped all 765 of them.
    in_range = {key(mi, ri) for mi in range(len(mblocks)) for ri in range(len(rblocks))}
    outside = {k for k in st['done'] if k not in in_range}
    lost = len((st['done'] & in_range) - proven)
    if lost:
        print('  state repair: %d blocks were marked done with no data and no recorded reason '
              '- re-queued' % lost)
    st['done'] = proven | outside
    todo = [(mi, ri) for mi in range(len(mblocks)) for ri in range(len(rblocks))
            if key(mi, ri) not in st['done']]
    print('span %d..%d = %d months | %d reporters | %d calls total, %d already done, %d left'
          % (lo, hi, len(cal), len(reps), len(mblocks) * len(rblocks),
             len(st['done']), len(todo)))
    print('budget today: %d of %d already spent, %d available' % (spent, budget, max(0, budget - spent)))

    import pandas as pd
    made = rows = failed = 0
    quota_hit = False
    for mi, ri in todo:
        if spent >= budget:
            print('daily budget reached - stopping cleanly. Re-run tomorrow to continue.')
            break
        mb, rb = mblocks[mi], rblocks[ri]
        q = (f"{ct.BASE}?reporterCode={','.join(str(r) for r in rb)}"
             f"&period={','.join(str(m) for m in mb)}&cmdCode={codes}&flowCode=M,X")
        try:
            data = ct._get(q)
        except ct.QuotaExceeded as e:
            # The API's own count decides, not ours. Ours read 300 of 450 while the server had
            # already cut us off - our counter cannot see the retries inside _get, and each of
            # those is a real call. Believe the server and stop.
            print(NL + '  API refused: %s' % e)
            print('  our local count said %d of %d spent. The server disagrees, and the server '
                  'is right - stopping so nothing is marked done on a refusal.' % (spent, budget))
            quota_hit = True
            break
        spent += 1
        st['calls'][today] = spent
        if data is None:
            # A failed call proves nothing about the block. Leave it in the queue.
            failed += 1
            time.sleep(ct._PAUSE)
            continue
        recs = [{k: r.get(k) for k in FIELDS} for r in data.get('data', [])]
        if recs:
            path = os.path.join(PARTS, 'p_%d_%d.parquet' % (mb[0], rb[0]))
            pd.DataFrame(recs).to_parquet(path, index=False, compression='zstd')
            rows += len(recs)
            made += 1
        else:
            # A successful call returning nothing IS an answer: this block holds no rows for our
            # HS6 set. Record it, so it is not re-fetched on every run for the rest of time.
            st['empty'].add(key(mi, ri))
        st['done'].add(key(mi, ri))
        if spent % 20 == 0:
            save_state(st)
            print('  %d calls spent, %d parts, %d rows (%s..%s)'
                  % (spent, made, rows, mb[0], mb[-1]), flush=True)
        time.sleep(ct._PAUSE)

    save_state(st)
    print(NL + 'this run: %d parts written, %d rows, %d calls failed'
          % (made, rows, failed))
    if quota_hit:
        print('STOPPED ON QUOTA - nothing was marked complete on a refusal.')
    print('progress: %d of %d call-blocks answered (%d confirmed empty)'
          % (len(st['done']), len(mblocks) * len(rblocks), len(st['empty'])))
    return 0


if __name__ == '__main__':
    sys.exit(main())

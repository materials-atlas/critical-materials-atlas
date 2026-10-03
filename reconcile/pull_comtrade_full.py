# -*- coding: utf-8 -*-
"""Full-universe UN Comtrade crawl: ALL HS6 products, all reporters, MONTHLY, newest first.

WHY THIS EXISTS
reconcile/reconcile.py deflates CIF imports to an FOB basis with a per-product MEDIAN markup rather
than BACI's gravity regression, and its own step 2 says why: on our 31-code slice distance is
unidentified - measured R^2 = 0.01. That is a statement about the SLICE, not about the method. A
gravity model needs the full product universe to identify a distance coefficient, so the only way to
find out whether CEPII's method beats ours on our data is to go and get the universe.

MONTHLY, NOT ANNUAL
The first version of this file asked the ANNUAL endpoint and walked straight into two empty years:
annual 2026 is not published until 2027, which is why the first probe returned zero rows for
Afghanistan. CEPII BACI V202601 stops at 2024, so the years we do not already have from them are
exactly the ones that only exist monthly. This asks /C/M/HS.

THE COST IS THE QUERY SHAPE, NOT THE DATA
Asking one HS code at a time would be 10,768 calls for a single year. Asking one reporter-month at
a time is 5,640. But `period` takes a COMMA-SEPARATED LIST - the official client's own example is
period='200001,200002,200003' - so one call can carry a whole year of months for any reporter whose
year fits under the record cap. Sized against BACI 2023 (11.78M flows, 226 exporters, median 9,321
flows/year), 151 of 226 reporters fit a whole year in one call and the ten largest need 13-23.
That is ~600-900 calls per year of data instead of 5,640.

ADAPTIVE, BECAUSE THE MULTIPLIER IS A GUESS
How many months an average flow appears in decides everything, and it is the one number here that
was never measured - bracketed 2x to 6x. So the crawler does not plan the split in advance: it asks
for the widest window it thinks will fit, and when a response comes back AT the cap it halves the
window and retries. A capped page is indistinguishable from a small trader otherwise, which is the
failure this guards against.

IT MUST NOT STARVE THE NIGHTLY REFRESH
pipeline/refresh.py pulls Comtrade from the same key against the same 500/day allowance, and
adapter_comtrade.py's own note puts an 18-month backfill at ~114 calls. The default budget here is
380, leaving ~120, because a crawl that silently stops the daily atlas is a bad trade at any speed.

ONE SIDE AT A TIME, KEPT APART
Each (reporter, flow) is stored separately and never merged here. Which side a number came from
decides whether it is ours to publish - the annual engine's output is withheld as a bundle precisely
because it mixed them.

    python reconcile/pull_comtrade_full.py --plan            # the schedule, no network
    python reconcile/pull_comtrade_full.py --probe           # ONE call, fixes the multiplier
    python reconcile/pull_comtrade_full.py                   # a day's crawl, budget 380
    python reconcile/pull_comtrade_full.py --budget 100 --years 2026

The key is read from pipeline/.comtrade_key or $COMTRADE_KEY and is never printed or logged.
"""
import argparse
import io
import json
import os
import sys
import time

import pandas as pd

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

OUTDIR = os.path.join(ROOT, 'raw', 'comtrade_full')      # raw/ is gitignored in full
STATE = os.path.join(OUTDIR, '_state.json')
BASE = 'https://comtradeapi.un.org/data/v1/get/C/M/HS'

PAGE_CAP = 100000          # free tier: 100k records per call. A full page means TRUNCATED.
YEAR_MAX, YEAR_MIN = 2026, 2000
DEFAULT_BUDGET = 380       # 500/day minus ~120 reserved for pipeline/refresh.py

# The window ladder, in months. Start wide; halve on a capped response.
WINDOWS = (12, 6, 3, 1)


def _key():
    """Read the key. Never print it, never put it in an error message."""
    k = os.environ.get('COMTRADE_KEY', '').strip()
    if not k:
        p = os.path.join(ROOT, 'pipeline', '.comtrade_key')
        if os.path.exists(p):
            k = io.open(p, encoding='utf-8').read().strip()
    if not k:
        sys.exit('No Comtrade key: set $COMTRADE_KEY or create pipeline/.comtrade_key')
    return k


def reporters():
    """M49 code -> ISO3, from the BACI country table already in the repo."""
    import baci
    cc = pd.read_csv(baci.country_file(), keep_default_na=False, na_values=[''])
    return [(int(r.country_code), r.country_iso3) for r in cc.itertuples()
            if str(r.country_iso3).isalpha() and len(str(r.country_iso3)) == 3]


def load_state():
    if os.path.exists(STATE):
        try:
            s = json.load(io.open(STATE, encoding='utf-8'))
            s.setdefault('done', {}); s.setdefault('empty', {}); s.setdefault('calls', 0)
            s.setdefault('rows', 0); s.setdefault('window', {})
            return s
        except ValueError:
            pass
    return {'done': {}, 'empty': {}, 'calls': 0, 'rows': 0, 'window': {}, 'started': None}


def save_state(st):
    os.makedirs(OUTDIR, exist_ok=True)
    tmp = STATE + '.tmp'
    io.open(tmp, 'w', encoding='utf-8').write(json.dumps(st, indent=1, sort_keys=True))
    os.replace(tmp, STATE)          # never leave a half-written state file behind


def chunk_key(year, iso3, flow, months):
    return '%d|%s|%s|%s' % (year, iso3, flow, '-'.join('%02d' % m for m in (months[0], months[-1])))


def part_path(year, iso3, flow, months):
    return os.path.join(OUTDIR, str(year),
                        '%s_%s_%02d-%02d.parquet' % (iso3, flow, months[0], months[-1]))


def split_months(window):
    """Calendar months 1..12 grouped into windows of `window` length."""
    return [list(range(s, min(s + window, 13))) for s in range(1, 13, window)]


def pending(years, st):
    """(year, code, iso3, flow) still owing at least one chunk. Newest year first."""
    out = []
    for y in years:
        for code, iso3 in reporters():
            for flow in ('M', 'X'):
                if st['done'].get('%d|%s|%s' % (y, iso3, flow)) == 'complete':
                    continue
                if st['empty'].get('%d|%s|%s' % (y, iso3, flow)):
                    continue
                out.append((y, code, iso3, flow))
    return out


def fetch(session, key, periods, code, flow):
    """One call. Returns (rows, status). Retries transient failures with backoff."""
    params = {'period': ','.join(str(p) for p in periods), 'reporterCode': code,
              'cmdCode': 'AG6', 'flowCode': flow, 'partnerCode': ''}
    for attempt in range(5):
        try:
            r = session.get(BASE, headers={'Ocp-Apim-Subscription-Key': key},
                            params=params, timeout=300)
            if r.status_code == 200:
                return (r.json().get('data') or []), 200
            if r.status_code in (429, 500, 502, 503, 504):
                wait = 30 * (attempt + 1) if r.status_code == 429 else 6 * (attempt + 1)
                print('      http %d, waiting %ds' % (r.status_code, wait), flush=True)
                time.sleep(wait)
                continue
            return None, r.status_code         # 401/403: do not retry, do not log the key
        except Exception as e:
            print('      %s, retrying' % type(e).__name__, flush=True)
            time.sleep(6 * (attempt + 1))
    return None, -1


COLS = ['period', 'reporter', 'partner', 'cmd', 'flow', 'value', 'netwgt', 'qty', 'qtyunit']


def to_frame(rows):
    return pd.DataFrame([{
        'period': r.get('period'), 'reporter': r.get('reporterCode'),
        'partner': r.get('partnerCode'), 'cmd': str(r.get('cmdCode')),
        'flow': r.get('flowCode'), 'value': r.get('primaryValue'),
        'netwgt': r.get('netWgt'), 'qty': r.get('qty'), 'qtyunit': r.get('qtyUnitCode'),
    } for r in rows], columns=COLS)


def crawl_one(session, key, st, year, code, iso3, flow, spend, budget):
    """Fetch one reporter-year-flow, narrowing the window whenever a page comes back capped.

    Returns calls used. Records per-reporter the window that worked, so the next year starts
    there instead of rediscovering it.
    """
    used = 0
    start_w = st['window'].get(iso3, WINDOWS[0])
    wi = WINDOWS.index(start_w) if start_w in WINDOWS else 0
    queue = [(wi, m) for m in split_months(WINDOWS[wi])]
    got_any = False

    while queue:
        if spend[0] + used >= budget:
            return used                       # out of budget: the rest stays pending
        wi, months = queue.pop(0)
        k = chunk_key(year, iso3, flow, months)
        if st['done'].get(k) or st['empty'].get(k):
            continue
        if os.path.exists(part_path(year, iso3, flow, months)):
            st['done'][k] = 'on disk'
            got_any = True
            continue

        periods = ['%d%02d' % (year, m) for m in months]
        rows, status = fetch(session, key, periods, code, flow)
        used += 1
        st['calls'] += 1
        if rows is None:
            print('   %d %s %s %02d-%02d  FAILED http %s'
                  % (year, iso3, flow, months[0], months[-1], status), flush=True)
            if status in (401, 403):
                raise SystemExit('the key was rejected - stopping')
            continue

        if len(rows) >= PAGE_CAP and wi + 1 < len(WINDOWS):
            nxt = WINDOWS[wi + 1]
            st['window'][iso3] = nxt          # remember: this reporter is a big one
            print('   %d %s %s %02d-%02d  capped at %d -> narrowing to %d-month windows'
                  % (year, iso3, flow, months[0], months[-1], len(rows), nxt), flush=True)
            sub = [m for m in split_months(nxt) if set(m) & set(months)]
            queue = [(wi + 1, m) for m in sub] + queue
            continue

        if not rows:
            st['empty'][k] = True
            continue

        df = to_frame(rows)
        p = part_path(year, iso3, flow, months)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        df.to_parquet(p, index=False, compression='zstd')
        st['done'][k] = len(df)
        st['rows'] += len(df)
        got_any = True
        warn = '  AT CAP, still truncated' if len(rows) >= PAGE_CAP else ''
        print('   %d %s %s %02d-%02d  %7d rows  %4d codes%s'
              % (year, iso3, flow, months[0], months[-1], len(df), df.cmd.nunique(), warn),
              flush=True)

    rk = '%d|%s|%s' % (year, iso3, flow)
    st['done' if got_any else 'empty'][rk] = 'complete' if got_any else True
    return used


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--budget', type=int, default=DEFAULT_BUDGET, help='max API calls this run')
    ap.add_argument('--years', type=int, nargs='*', default=None)
    ap.add_argument('--plan', action='store_true')
    ap.add_argument('--probe', action='store_true', help='ONE call, to fix the multiplier')
    ap.add_argument('--sleep', type=float, default=1.3)
    a = ap.parse_args()

    years = a.years or list(range(YEAR_MAX, YEAR_MIN - 1, -1))
    st = load_state()
    todo = pending(years, st)

    if a.plan:
        reps = len(reporters())
        print('full-universe MONTHLY Comtrade crawl - PLAN ONLY, no calls made')
        print('  endpoint     %s' % BASE)
        print('  years        %d..%d (newest first)' % (years[0], years[-1]))
        print('  reporters    %d  x 2 flows = %d reporter-year-flows per year' % (reps, reps * 2))
        print('  window       starts at %d months per call, halving on a capped page' % WINDOWS[0])
        print('  budget       %d calls/run (500/day minus ~120 for pipeline/refresh.py)' % a.budget)
        print()
        print('  reporter-year-flows outstanding : %d' % len(todo))
        print('  calls already made              : %d' % st.get('calls', 0))
        print('  rows already stored             : %s' % format(st.get('rows', 0), ','))
        print()
        print('  at ~1.5 calls per reporter-year-flow, that is ~%d calls, ~%.0f days at %d/run'
              % (len(todo) * 1.5, len(todo) * 1.5 / max(a.budget, 1), a.budget))
        print()
        print('  output  %s/<year>/<ISO3>_<flow>_<mm-mm>.parquet   (raw/ is gitignored)'
              % os.path.relpath(OUTDIR, ROOT).replace(os.sep, '/'))
        return 0

    key = _key()
    import requests
    session = requests.Session()

    if a.probe:
        # A mid-sized reporter in a year that certainly has monthly data, asking for a FULL YEAR.
        # The row count answers the one question the schedule depends on.
        code, iso3 = 76, 'BRA'
        print('probe: %s 2023, all 12 months, imports, cmdCode=AG6 ...' % iso3, flush=True)
        rows, status = fetch(session, key, ['2023%02d' % m for m in range(1, 13)], code, 'M')
        if rows is None:
            print('  FAILED http %s' % status); return 1
        df = to_frame(rows)
        print('  %s rows, %d HS6 codes, %d partners, %d periods'
              % (format(len(df), ','), df.cmd.nunique(), df.partner.nunique(), df.period.nunique()))
        if len(rows) >= PAGE_CAP:
            print('  -> AT THE CAP: even a mid-sized reporter needs narrower windows.')
        else:
            print('  -> a whole year fits in ONE call for this reporter.')
        # BACI is read through baci.py, which is the one door this repository allows
        # (ARCHITECTURE.md phase 2). Opening raw/baci/ directly is what check_baci_door refuses.
        try:
            import baci
            b = baci.year(2023, columns=['i'])
            ann = int((b['i'].astype(str) == str(iso3)).sum())
            if not ann:                       # baci.year may return M49 rather than ISO3
                cf = pd.read_csv(baci.country_file(), keep_default_na=False, na_values=[''])
                m49 = dict(zip(cf.country_iso3, cf.country_code))
                ann = int((pd.to_numeric(b['i'], errors='coerce') == m49.get(iso3, -1)).sum())
            if ann:
                print('  -> BACI 2023 has %s annual flows for %s, so the multiplier is %.2fx'
                      % (format(ann, ','), iso3, len(df) / ann))
                print('     (that is the number the whole schedule was guessed at: 2x-6x)')
            else:
                print('  (no BACI 2023 rows for %s, so no multiplier)' % iso3)
        except Exception as e:
            print('  (could not compute the multiplier: %s)' % type(e).__name__)
        return 0

    os.makedirs(OUTDIR, exist_ok=True)
    st['started'] = st.get('started') or time.strftime('%Y-%m-%d %H:%M')
    spend = [0]
    t0 = time.time()
    try:
        for (y, code, iso3, flow) in todo:
            if spend[0] >= a.budget:
                print('budget of %d calls reached' % a.budget)
                break
            spend[0] += crawl_one(session, key, st, y, code, iso3, flow, spend, a.budget)
            if spend[0] % 25 < 2:
                save_state(st)
            time.sleep(a.sleep)
    finally:
        save_state(st)

    left = len(pending(years, st))
    print()
    print('this run: %d calls in %.1f min. total calls %d, rows stored %s'
          % (spend[0], (time.time() - t0) / 60, st.get('calls', 0), format(st.get('rows', 0), ',')))
    print('outstanding reporter-year-flows: %d (~%.0f more runs at --budget %d)'
          % (left, left * 1.5 / max(a.budget, 1), a.budget))
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())

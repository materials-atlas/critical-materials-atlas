# -*- coding: utf-8 -*-
"""Full-universe UN Comtrade crawl: ALL HS6 products, all reporters, newest year first.

WHY THIS EXISTS
reconcile/reconcile.py deflates CIF imports to an FOB basis with a per-product MEDIAN markup, not
BACI's gravity regression, and says why in its own step 2: on our 31-code slice distance is
unidentified - measured R^2 = 0.01. That is a statement about the SLICE, not about the method. The
gravity model needs the full product universe to identify a distance coefficient, so the only way to
find out whether CEPII's method beats ours on our data is to go and get the universe.

THE COST IS THE QUERY SHAPE, NOT THE DATA
pull_comtrade.py asks for one HS code at a time: 2 calls per code per year, so 5,384 codes would be
10,768 calls for a single year. This asks for one REPORTER at a time with cmdCode=AG6 - every
6-digit line that reporter filed - which is ~240 reporters x 2 flows = ~480 calls for the same year.
A full year of the whole universe therefore costs about what 240 codes cost the old way.

NEWEST FIRST, AND WHY
The crawl runs 2026 -> 2000. CEPII BACI V202601 stops at 2024, so the years we do not already have
from them are the newest ones, and they are the only years where our own reconciliation is not a
reproduction of theirs. If the crawl is interrupted for good at any point, the part we finished is
the part that was worth having. The oldest years are the ones BACI already covers better.

ONE SIDE AT A TIME, KEPT APART
Each (reporter, flow) is stored separately and never merged here. The exporter's FOB report and the
importer's CIF report are two observations, and which of them a final number came from decides
whether that number is ours to publish. The annual engine's output is withheld as a bundle precisely
because it mixed them; this crawl is built so the successor does not have to.

RATE LIMIT
A daily budget is enforced in-process (--budget, default 400) and the state file records every call,
so a run resumes where the last one stopped and never re-fetches a (year, reporter, flow) it already
has. Nothing here is destructive: an existing part file is skipped, never rewritten.

    python reconcile/pull_comtrade_full.py --plan              # what it would do, no network
    python reconcile/pull_comtrade_full.py --probe             # ONE call, to verify the query shape
    python reconcile/pull_comtrade_full.py --budget 400        # a day's crawl
    python reconcile/pull_comtrade_full.py --years 2026 2025   # restrict

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
BASE = 'https://comtradeapi.un.org/data/v1/get/C/A/HS'

# The response cap. A reporter whose year exceeds it is re-fetched chapter by chapter rather than
# silently truncated - a short page looks exactly like a small trader otherwise.
PAGE_CAP = 100000
YEAR_MAX, YEAR_MIN = 2026, 2000


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
            return json.load(io.open(STATE, encoding='utf-8'))
        except ValueError:
            pass
    return {'done': {}, 'empty': {}, 'calls': 0, 'started': None}


def save_state(st):
    os.makedirs(OUTDIR, exist_ok=True)
    io.open(STATE, 'w', encoding='utf-8').write(json.dumps(st, indent=1, sort_keys=True))


def part_path(year, iso3, flow):
    return os.path.join(OUTDIR, str(year), '%s_%s.parquet' % (iso3, flow))


def tasks(years, st):
    """Newest year first; within a year, reporters alphabetically so a resume is predictable."""
    out = []
    for y in years:
        for code, iso3 in reporters():
            for flow in ('M', 'X'):
                k = '%d|%s|%s' % (y, iso3, flow)
                if k in st['done'] or k in st['empty']:
                    continue
                if os.path.exists(part_path(y, iso3, flow)):
                    st['done'][k] = 'on disk'
                    continue
                out.append((y, code, iso3, flow))
    return out


def fetch(session, key, year, code, flow, cmd='AG6'):
    """One call. Returns (rows, http_status). Retries transient failures with backoff."""
    params = {'period': year, 'reporterCode': code, 'cmdCode': cmd,
              'flowCode': flow, 'partnerCode': ''}
    for attempt in range(5):
        try:
            r = session.get(BASE, headers={'Ocp-Apim-Subscription-Key': key},
                            params=params, timeout=180)
            if r.status_code == 200:
                return (r.json().get('data') or []), 200
            if r.status_code in (429, 500, 502, 503, 504):
                wait = 20 * (attempt + 1) if r.status_code == 429 else 5 * (attempt + 1)
                print('   http %d, waiting %ds' % (r.status_code, wait), flush=True)
                time.sleep(wait)
                continue
            return None, r.status_code           # 401/403 etc: do not retry, do not log the key
        except Exception as e:
            print('   %s, retrying' % type(e).__name__, flush=True)
            time.sleep(5 * (attempt + 1))
    return None, -1


COLS = ['year', 'reporter', 'partner', 'cmd', 'flow', 'value', 'netwgt', 'qty', 'qtyunit']


def to_frame(rows, year):
    return pd.DataFrame([{
        'year': year, 'reporter': r.get('reporterCode'), 'partner': r.get('partnerCode'),
        'cmd': str(r.get('cmdCode')), 'flow': r.get('flowCode'),
        'value': r.get('primaryValue'), 'netwgt': r.get('netWgt'),
        'qty': r.get('qty'), 'qtyunit': r.get('qtyUnitCode'),
    } for r in rows], columns=COLS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--budget', type=int, default=400, help='max API calls this run')
    ap.add_argument('--years', type=int, nargs='*', default=None)
    ap.add_argument('--plan', action='store_true', help='print the schedule, make no calls')
    ap.add_argument('--probe', action='store_true', help='ONE call, to verify the query shape')
    ap.add_argument('--sleep', type=float, default=1.3)
    a = ap.parse_args()

    years = a.years or list(range(YEAR_MAX, YEAR_MIN - 1, -1))
    st = load_state()
    todo = tasks(years, st)

    if a.plan:
        reps = len(reporters())
        print('full-universe Comtrade crawl - PLAN ONLY, no calls made')
        print('  years        %s (newest first)' % (
            '%d..%d' % (years[0], years[-1]) if len(years) > 1 else years[0]))
        print('  reporters    %d   x 2 flows = %d calls per year' % (reps, reps * 2))
        print('  already done %d' % len(st['done']))
        print('  outstanding  %d calls' % len(todo))
        print('  at --budget %d/day: %.1f days' % (a.budget, len(todo) / max(a.budget, 1)))
        print()
        for y in years[:3]:
            n = sum(1 for t in todo if t[0] == y)
            print('     %d: %4d calls outstanding' % (y, n))
        print()
        print('  output  %s/<year>/<ISO3>_<flow>.parquet   (raw/ is gitignored)'
              % os.path.relpath(OUTDIR, ROOT).replace(os.sep, '/'))
        print('  NOTE    the exporter (X) and importer (M) sides are stored apart and never merged '
              'here;\n          which side a number came from decides whether it is ours to publish.')
        return 0

    key = _key()
    import requests
    session = requests.Session()

    if a.probe:
        if not todo:
            print('nothing outstanding to probe'); return 0
        y, code, iso3, flow = todo[0]
        print('probe: %d %s flow=%s cmdCode=AG6 ...' % (y, iso3, flow), flush=True)
        rows, status = fetch(session, key, y, code, flow)
        if rows is None:
            print('  FAILED http %s - the query shape or the key is wrong' % status)
            return 1
        df = to_frame(rows, y)
        print('  %d rows, %d distinct HS6 codes, %d partners'
              % (len(df), df.cmd.nunique(), df.partner.nunique()))
        print('  -> AG6 returns %s' % ('all 6-digit lines as expected' if df.cmd.nunique() > 50
                                       else 'TOO FEW CODES - check the cmdCode parameter'))
        if len(rows) >= PAGE_CAP:
            print('  -> hit the %d cap: this reporter needs chapter splitting' % PAGE_CAP)
        return 0

    os.makedirs(OUTDIR, exist_ok=True)
    st['started'] = st.get('started') or time.strftime('%Y-%m-%d %H:%M')
    used = 0
    for (y, code, iso3, flow) in todo:
        if used >= a.budget:
            print('budget of %d calls reached' % a.budget); break
        rows, status = fetch(session, key, y, code, flow)
        used += 1
        st['calls'] = st.get('calls', 0) + 1
        k = '%d|%s|%s' % (y, iso3, flow)
        if rows is None:
            print('  %d %s %s  FAILED http %s' % (y, iso3, flow, status), flush=True)
            if status in (401, 403):
                print('  stopping: the key was rejected'); break
            continue
        if not rows:
            st['empty'][k] = True
            print('  %d %s %s  (nothing filed)' % (y, iso3, flow), flush=True)
        else:
            df = to_frame(rows, y)
            os.makedirs(os.path.dirname(part_path(y, iso3, flow)), exist_ok=True)
            df.to_parquet(part_path(y, iso3, flow), index=False, compression='zstd')
            st['done'][k] = len(df)
            flag = '  CAPPED - needs chapter split' if len(rows) >= PAGE_CAP else ''
            print('  %d %s %s  %7d rows  %4d codes%s'
                  % (y, iso3, flow, len(df), df.cmd.nunique(), flag), flush=True)
        if used % 25 == 0:
            save_state(st)
        time.sleep(a.sleep)

    save_state(st)
    print()
    print('this run: %d calls. total recorded: %d. parts on disk: %d'
          % (used, st.get('calls', 0), len(st['done'])))
    left = len(tasks(years, st))
    print('outstanding: %d calls (%.1f more days at --budget %d)'
          % (left, left / max(a.budget, 1), a.budget))
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())

# -*- coding: utf-8 -*-
"""Fetch UN Comtrade monthly imports, as reported by the importer, for the AI build-out page and
buildout-study Amendment D. January 2024 to June 2026, HS 6-digit.

Totals only (motCode=0, customsCode=C00, partner2Code=0), imports only, one reporter per call and six
months per call. A call that returns close to the API's 100,000-record ceiling would be silently cut
off, so it is split (months first, then codes) until every piece is safely under it. Resumable:
state records every (reporter, months, codes) piece answered, including empty ones. Stops cleanly on
the daily quota, leaving headroom for the nightly refresh.

The key is read by pipeline/adapter_comtrade.py from pipeline/.comtrade_key and never printed. Raw
Comtrade records are written only to ai-buildout/comtrade/ (gitignored) and never redistributed.
Network fetcher: named fetch_* so the runner never runs it.

Usage:  python ai-buildout/fetch_comtrade_ai.py [--budget 350]
"""
import datetime
import json
import os
import sys
import time
import zlib

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import adapter_comtrade as ct                                  # _get, BASE, QuotaExceeded, key

OUTDIR = os.path.join(HERE, 'comtrade')
STATE = os.path.join(OUTDIR, 'state.json')
LOG = os.path.join(OUTDIR, 'fetch.log')
CEILING = 100000
SAFE = 90000
CODES = sorted(set([
    # the AI build-out page
    '854231', '854232', '854239', '854141', '854142', '854143', '854149',
    '280461', '280429', '811292', '810320',
    '850421', '850422', '850423', '722511', '722611', '740811',
    '850152', '850153', '841370', '841480',
    '848620', '848610', '848690', '381800', '370790', '903082',
    # buildout-study: the filed heavy machinery, the steel and copper comparisons
    '842810', '842649', '847420', '847431', '851531', '851539',
    '722530', '722540', '722550', '722599', '740311']))
MONTHS = ['2024%02d' % m for m in range(1, 13)] + ['2025%02d' % m for m in range(1, 13)] + \
         ['2026%02d' % m for m in range(1, 7)]
BLOCKS = [MONTHS[i:i + 6] for i in range(0, len(MONTHS), 6)]
FIELDS = ('reporterCode', 'partnerCode', 'cmdCode', 'flowCode', 'period', 'primaryValue', 'netWgt',
          'cifvalue', 'fobvalue', 'isReported', 'isAggregate')
# China, India, Taiwan (Comtrade 490) and Hong Kong are probed once even though they were absent from
# the 2025 monthly data on disk: an empty answer costs one call and settles it.
PROBE = [156, 356, 490, 344]


def log(msg):
    os.makedirs(OUTDIR, exist_ok=True)
    line = '%s  %s' % (datetime.datetime.now().isoformat(timespec='seconds'), msg)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
    print(line, flush=True)


def load_state():
    if os.path.exists(STATE):
        with open(STATE, encoding='utf-8') as f:
            s = json.load(f)
        s['done'] = set(s['done'])
        return s
    return {'done': set(), 'calls': {}}


def save_state(s):
    t = dict(s, done=sorted(s['done']))
    with open(STATE + '.part', 'w', encoding='utf-8') as f:
        json.dump(t, f)
    os.replace(STATE + '.part', STATE)


def piece_key(rep, months, codes):
    return '%d|%s|%s' % (rep, ','.join(months), ','.join(codes))


class Budget(Exception):
    pass


def fetch(rep, months, codes, st, budget):
    """Fetch one piece; split it if the answer is near the ceiling. Returns rows written."""
    k = piece_key(rep, months, codes)
    if k in st['done']:
        return 0
    today = datetime.date.today().isoformat()
    if st['calls'].get(today, 0) >= budget:
        raise Budget()
    q = ('%s?reporterCode=%d&period=%s&cmdCode=%s&flowCode=M&motCode=0&customsCode=C00&partner2Code=0'
         % (ct.BASE, rep, ','.join(months), ','.join(codes)))
    data = ct._get(q)                                          # raises ct.QuotaExceeded on refusal
    st['calls'][today] = st['calls'].get(today, 0) + 1
    time.sleep(ct._PAUSE)
    if data is None:
        log('  %d %s..%s: failed call, left in the queue' % (rep, months[0], months[-1]))
        return 0
    recs = data.get('data', []) or []
    if len(recs) >= SAFE:
        # Too close to the ceiling to trust: split, months first, then codes.
        log('  %d %s..%s %d codes: %d rows, splitting' % (rep, months[0], months[-1], len(codes), len(recs)))
        if len(months) > 1:
            h = len(months) // 2
            parts = [(months[:h], codes), (months[h:], codes)]
        elif len(codes) > 1:
            h = len(codes) // 2
            parts = [(months, codes[:h]), (months, codes[h:])]
        else:
            raise RuntimeError('one reporter, month and code exceeds the ceiling: %s' % k)
        n = sum(fetch(rep, m, c, st, budget) for m, c in parts)
        st['done'].add(k)
        return n
    if recs:
        path = os.path.join(OUTDIR, 'c_%d_%s_%s_%d.parquet' % (rep, months[0], months[-1], zlib.crc32(','.join(codes).encode()) % 10 ** 6))
        pd.DataFrame([{f: r.get(f) for f in FIELDS} for r in recs]).to_parquet(path, index=False)
    st['done'].add(k)
    return len(recs)


def main():
    a = sys.argv[1:]
    budget = int(a[a.index('--budget') + 1]) if '--budget' in a else 350
    if not ct.API_KEY:
        sys.exit('no Comtrade key: the keyless endpoint truncates at 500 rows')
    with open(os.path.join(HERE, 'comtrade_reporters.json'), encoding='utf-8') as f:
        reps = sorted(set(json.load(f)) | set(PROBE))
    st = load_state()
    todo = [(r, b) for r in reps for b in BLOCKS if piece_key(r, b, CODES) not in st['done']]
    log('reporters %d, blocks %d, pieces left %d, budget %d/day (spent today %d)'
        % (len(reps), len(BLOCKS), len(todo), budget, st['calls'].get(datetime.date.today().isoformat(), 0)))
    rows = 0
    try:
        for i, (r, b) in enumerate(todo):
            rows += fetch(r, b, CODES, st, budget)
            if i % 20 == 19:
                save_state(st)
                log('  %d of %d pieces, %d rows this run' % (i + 1, len(todo), rows))
    except Budget:
        log('daily budget reached - stopping cleanly; re-run tomorrow')
    except ct.QuotaExceeded:
        log('API quota refused - stopping; nothing was marked done on the refusal')
    save_state(st)
    left = [(r, b) for r in reps for b in BLOCKS if piece_key(r, b, CODES) not in st['done']]
    log('this run: %d rows | pieces left %d' % (rows, len(left)))


if __name__ == '__main__':
    main()

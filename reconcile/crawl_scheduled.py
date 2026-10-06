# -*- coding: utf-8 -*-
"""One scheduled day of the full-universe Comtrade crawl. Run by Task Scheduler, logs to a file.

WHY A WRAPPER AND NOT THE PULLER DIRECTLY
Task Scheduler runs pythonw.exe, which HAS NO STDOUT. A script that prints its progress writes it
into the void, and a task that dies looks exactly like a task that finished. This repository has
already paid for that lesson once: the nightly refresh was killed at its time limit for ELEVEN days
and nobody could tell, because the only log line was written at the END. So this logs at the START,
at the end, and on the way out of an exception - and the heartbeat line is written before any work
begins, so an empty tail means "killed", not "idle".

BUDGET
880 calls across TWO keys. Key #1 (Toma) gives 500 minus the ~120 that pipeline/refresh.py needs
from the same key, so 380; key #2 (a second free account, added 6 Oct 2026 with its holder's agreement) carries no
such reserve and gives its full 500. A crawl that silently stops the daily atlas is a bad trade at
any speed, which is why the reserve stays on key #1 rather than being spent.

If a key is ever removed from pipeline/.comtrade_key, drop this back to 380 - the puller caps each
key at its own remaining allowance, so an over-large budget is not spent twice, but it does make the
run stop early and look like a failure.

    python reconcile/crawl_scheduled.py            # one day's worth
    python reconcile/crawl_scheduled.py --budget 50
"""
import argparse
import io
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, 'raw', 'comtrade_full', '_crawl.log')


def log(msg):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    line = '%s  %s\n' % (time.strftime('%Y-%m-%dT%H:%M:%S'), msg)
    with io.open(LOG, 'a', encoding='utf-8') as f:
        f.write(line)
        f.flush()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--budget', type=int, default=880)
    a = ap.parse_args()

    # Written BEFORE any work: if the process is killed, this line is what proves it started.
    log('START  budget=%d  pid=%d' % (a.budget, os.getpid()))
    t0 = time.time()
    try:
        p = subprocess.run(
            [sys.executable, os.path.join(ROOT, 'reconcile', 'pull_comtrade_full.py'),
             '--budget', str(a.budget)],
            cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
        tail = (p.stdout or '').strip().splitlines()
        for line in tail[-6:]:
            log('   %s' % line)
        if p.returncode != 0:
            log('   stderr: %s' % (p.stderr or '')[-400:].replace('\n', ' | '))
        log('END    exit=%d  %.1f min' % (p.returncode, (time.time() - t0) / 60))
        return p.returncode
    except Exception as e:
        log('CRASH  %s: %s  after %.1f min' % (type(e).__name__, e, (time.time() - t0) / 60))
        return 1


if __name__ == '__main__':
    sys.exit(main())

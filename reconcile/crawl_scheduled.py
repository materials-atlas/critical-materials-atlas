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
import collections
import io
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, 'raw', 'comtrade_full', '_crawl.log')
RUNDIR = os.path.join(ROOT, 'raw', 'comtrade_full', 'runs')


def log(msg):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    line = '%s  %s\n' % (time.strftime('%Y-%m-%dT%H:%M:%S'), msg)
    with io.open(LOG, 'a', encoding='utf-8') as f:
        f.write(line)
        f.flush()


def _report():
    """Raise the progress notification NOW, because the run has just finished.

    CMA-crawl-watch also runs on a daily clock, but a clock cannot know when the crawl ends: on
    8 Oct 2026 it fired at 07:43:45, five seconds AFTER that day's run began, and so reported the
    previous day's totals. The day before, the run ended at 12:12 and the watcher had already
    spoken at 07:43. Every notification was therefore a day stale, which is indistinguishable from
    the crawl having stopped.

    The clock watcher stays: it is the only thing that can report a run that never started at all.
    This one reports what a run actually did, the moment it did it.
    """
    try:
        subprocess.run([sys.executable, os.path.join(ROOT, 'reconcile', 'crawl_watch.py')],
                       cwd=ROOT, capture_output=True, text=True, timeout=180)
        log('   progress notification raised')
    except Exception as e:
        log('   progress notification FAILED: %s' % type(e).__name__)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--budget', type=int, default=880)
    a = ap.parse_args()

    # Written BEFORE any work: if the process is killed, this line is what proves it started.
    log('START  budget=%d  pid=%d' % (a.budget, os.getpid()))
    t0 = time.time()
    try:
        # The full output goes to a per-day file, STREAMED, and only a short tail is copied
        # into the summary log. It used to be capture_output plus tail[-6:], which threw the run
        # away: on 9 Oct 2026 the crawl printed a sizing failure for every reporter it tried and
        # the log kept two lines, both stamped with the end time, so a day of 429s was
        # indistinguishable from a quiet success. Streaming also means the file can be read while
        # the run is still going, which capture_output made impossible.
        os.makedirs(RUNDIR, exist_ok=True)
        runlog = os.path.join(RUNDIR, time.strftime('%Y-%m-%d') + '.log')
        tail = collections.deque(maxlen=6)
        counts = collections.Counter()
        with io.open(runlog, 'a', encoding='utf-8') as rf:
            rf.write('===== START %s  budget=%d =====\n'
                     % (time.strftime('%Y-%m-%dT%H:%M:%S'), a.budget))
            rf.flush()
            p = subprocess.Popen(
                [sys.executable, os.path.join(ROOT, 'reconcile', 'pull_comtrade_full.py'),
                 '--budget', str(a.budget)],
                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace', bufsize=1)
            for line in p.stdout:
                line = line.rstrip('\n')
                rf.write('%s  %s\n' % (time.strftime('%H:%M:%S'), line))
                rf.flush()
                if line.strip():
                    tail.append(line.strip())
                    if 'FAILED http' in line:
                        counts['failed'] += 1
                    elif 'rows' in line and 'codes' in line:
                        counts['stored'] += 1
                    elif 'nothing filed' in line:
                        counts['empty'] += 1
            p.wait()
            rf.write('===== END exit=%d =====\n' % p.returncode)
        for line in tail:
            log('   %s' % line)
        if counts:
            log('   lines: %s' % ', '.join('%s=%d' % kv for kv in sorted(counts.items())))
        log('END    exit=%d  %.1f min   full log: runs/%s'
            % (p.returncode, (time.time() - t0) / 60, os.path.basename(runlog)))
        _report()
        return p.returncode
    except Exception as e:
        log('CRASH  %s: %s  after %.1f min' % (type(e).__name__, e, (time.time() - t0) / 60))
        _report()
        return 1


if __name__ == '__main__':
    sys.exit(main())

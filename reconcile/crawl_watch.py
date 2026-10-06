# -*- coding: utf-8 -*-
"""Tell somebody when the full-universe Comtrade crawl stops working.

WHY THIS EXISTS. The crawl is an eight-month job that nobody watches: it runs at 05:00 under
pythonw.exe, which has no stdout, and it writes parquet into a directory that only grows. A crawl
that dies looks exactly like a crawl that is between runs - yesterday's files are still there, the
site is unaffected, and the only symptom is that the finish date quietly moves further away. That is
the same shape of failure that killed eleven consecutive nightly refreshes in September 2026 without
a single visible sign, which is what pipeline/refresh_watch.py exists for. This is its twin.

It pushes the answer OUT rather than waiting to be asked: a Windows toast when something is wrong,
and a one-line status file either way that can be read without running anything.

    python reconcile/crawl_watch.py             # toast on trouble, always write the status file
    python reconcile/crawl_watch.py --quiet     # status file only, no toast

Register (daily 07:30 - after a 05:00 run, which takes about an hour at 880 calls, has finished, and
late enough that StartWhenAvailable has also caught up a run the machine missed overnight):
  schtasks /create /tn "CMA-crawl-watch" /tr "<pythonw.exe> <repo>\reconcile\crawl_watch.py" /sc daily /st 07:30 /f
Remove:  schtasks /delete /tn "CMA-crawl-watch" /f
Status:  type raw\comtrade_full\_crawl_status.txt

It always exits 0. A watcher whose own failure needs watching is not worth having.
"""
import datetime
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUTDIR = os.environ.get('CMA_CRAWL_DIR', os.path.join(REPO, 'raw', 'comtrade_full'))
LOG = os.path.join(OUTDIR, '_crawl.log')
STATE = os.path.join(OUTDIR, '_state.json')
STATUS = os.path.join(OUTDIR, '_crawl_status.txt')
TASK = 'CMA-comtrade-universe'

# A run is expected daily. 28 hours, not 24: a run that starts late, or a day the machine was off
# and StartWhenAvailable caught it up in the morning, is not a fault.
STALE_HOURS = 28

# The planner's estimate for the whole universe, from pull_comtrade_full.py --plan.
TOTAL_CALLS_EST = 203550

# The toast has to be attributed to a registered AppID or Windows drops it silently.
APPID = 'Microsoft.WindowsTerminal_8wekyb3d8bbwe!App'

PS_TOAST = r'''
$ErrorActionPreference = 'Stop'
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null
$t = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(
        [Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$n = $t.GetElementsByTagName('text')
$n.Item(0).AppendChild($t.CreateTextNode($env:CMA_TOAST_TITLE)) | Out-Null
$n.Item(1).AppendChild($t.CreateTextNode($env:CMA_TOAST_BODY)) | Out-Null
$toast = [Windows.UI.Notifications.ToastNotification]::new($t)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($env:CMA_TOAST_APPID).Show($toast)
'''

STAMP = re.compile(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s+(START|END|CRASH)\b(.*)$')


def read_log():
    """The last START and how that run ended. Returns (start, ended_or_None) or None."""
    if not os.path.exists(LOG):
        return None
    events = []
    with io.open(LOG, encoding='utf-8', errors='replace') as fh:
        for ln in fh:
            m = STAMP.match(ln.strip())
            if m:
                events.append((m.group(1), m.group(2), m.group(3).strip()))
    if not events:
        return None
    for i in range(len(events) - 1, -1, -1):
        if events[i][1] == 'START':
            after = events[i + 1:]
            ended = next((e for e in after if e[1] in ('END', 'CRASH')), None)
            return events[i], ended
    return events[-1], None


def check():
    """Returns a list of warnings. Empty means healthy."""
    warns = []
    now = datetime.datetime.now()

    if not os.path.isdir(OUTDIR):
        return ['crawl directory missing: %s' % OUTDIR]

    # 1. Is the task still registered? An unregistered task never fires and so never logs - the
    #    quietest failure of all, and invisible to any check that only reads the log.
    try:
        r = subprocess.run(
            ['powershell', '-NoProfile', '-NonInteractive', '-Command',
             "(Get-ScheduledTask -TaskName '%s' -ErrorAction SilentlyContinue).State" % TASK],
            capture_output=True, text=True, timeout=60)
        state = (r.stdout or '').strip()
        if not state:
            warns.append('scheduled task %s is NOT registered - the crawl will never run' % TASK)
        elif state.lower() == 'disabled':
            warns.append('scheduled task %s is DISABLED' % TASK)
    except Exception as e:
        warns.append('could not read the scheduled task: %s' % type(e).__name__)

    # 2. Did a run start recently, and how did it end?
    got = read_log()
    if not got:
        warns.append('no run has ever been logged in %s' % os.path.basename(LOG))
    else:
        start, ended = got
        try:
            when = datetime.datetime.strptime(start[0], '%Y-%m-%dT%H:%M:%S')
            age = (now - when).total_seconds() / 3600.0
        except Exception:
            age = None
        if age is not None and age > STALE_HOURS:
            warns.append('last run started %.0f h ago (%s) - one is expected daily'
                         % (age, start[0]))
        if ended is None:
            # Still running is normal for the first hour. Silent for longer is a kill or a hang,
            # which is exactly the case the START line was added to make visible.
            if age is not None and age > 6:
                warns.append('run started %s never logged END - killed or hung' % start[0])
        elif ended[1] == 'CRASH':
            warns.append('last run CRASHED: %s' % ended[2][:120])
        else:
            m = re.search(r'exit=(-?\d+)', ended[2])
            if m and m.group(1) != '0':
                warns.append('last run exited %s' % m.group(1))

    # 3. Is it actually storing anything? Calls spent with nothing stored is a broken run that
    #    still looks busy.
    try:
        st = json.load(io.open(STATE, encoding='utf-8'))
        stuck = len(st.get('stuck', {}))
        if stuck:
            warns.append('%d chunk(s) recorded STUCK - unsplittable, needs a look' % stuck)
        if not st.get('done'):
            warns.append('state records no completed reporter-months')
    except Exception as e:
        warns.append('could not read %s: %s' % (os.path.basename(STATE), type(e).__name__))

    return warns


def summary():
    """One line of where the crawl has got to."""
    try:
        st = json.load(io.open(STATE, encoding='utf-8'))
        n = 0
        size = 0
        for d, _, fs in os.walk(OUTDIR):
            for f in fs:
                if f.endswith('.parquet'):
                    n += 1
                    size += os.path.getsize(os.path.join(d, f))
        calls = int(st.get('calls', 0))
        pct = 100.0 * calls / float(TOTAL_CALLS_EST)
        return ('  %s parquet files, %.2f GB, %s calls spent (~%.2f%% of the estimated job)'
                % (format(n, ','), size / (1024.0 ** 3), format(calls, ','), pct))
    except Exception:
        return '  (could not summarise progress)'


def toast(title, body):
    """Best effort. A notification that cannot be raised must not take the status file down."""
    env = dict(os.environ, CMA_TOAST_TITLE=title, CMA_TOAST_BODY=body[:220], CMA_TOAST_APPID=APPID)
    try:
        r = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', PS_TOAST],
                           capture_output=True, text=True, env=env, timeout=60)
        return r.returncode == 0
    except Exception:
        return False


def main():
    quiet = '--quiet' in sys.argv
    warns = check()
    stamp = datetime.datetime.now().isoformat(timespec='seconds')
    if warns:
        head = 'NOT HEALTHY - %d warning(s)' % len(warns)
        shown = toast('Atlas Comtrade crawl', warns[0]) if not quiet else False
    else:
        head = 'healthy'
        shown = False
    lines = ['%s  comtrade universe crawl: %s' % (stamp, head)]
    lines += ['  - ' + w for w in warns]
    lines.append(summary())
    if warns and not quiet:
        lines.append('  (toast %s)' % ('shown' if shown else 'could NOT be raised'))
    lines.append('  log: raw/comtrade_full/_crawl.log'
                 '   plan: python reconcile/pull_comtrade_full.py --plan')
    text = '\n'.join(lines) + '\n'
    with io.open(STATUS, 'w', encoding='utf8') as fh:
        fh.write(text)
    # pythonw.exe has no stdout and writing to it raises, which would make the task report failure
    # while having worked perfectly. refresh_watch.py already fell into exactly this trap.
    try:
        sys.stdout.write(text)
    except Exception:
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main())

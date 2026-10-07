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

Register (daily 07:30 - after a 05:00 run, which takes about two hours at 880 calls, has finished,
and late enough that StartWhenAvailable has also caught up a run the machine missed overnight).

DO NOT register this with a bare `schtasks /create`. Its defaults are AC-power-only with no
catch-up, and on 7 Oct 2026 that is exactly how this watcher failed: the machine moved to battery
at 00:47, the task was refused with 0x800710E0, StartWhenAvailable was False so it never retried,
and the one job whose whole purpose is to report trouble was the only thing that reported nothing.

  $s = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries `
         -AllowStartIfOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
         -MultipleInstances IgnoreNew
  $a = New-ScheduledTaskAction -Execute '<pythonw.exe>' -Argument '"<repo>\reconcile\crawl_watch.py"'
  Register-ScheduledTask -TaskName 'CMA-crawl-watch' -Action $a -Settings $s `
         -Trigger (New-ScheduledTaskTrigger -Daily -At 07:30)

Remove:  Unregister-ScheduledTask -TaskName 'CMA-crawl-watch' -Confirm:$false
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
HISTORY = os.path.join(OUTDIR, '_crawl_progress.tsv')
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


def reading():
    """Today's numbers: (files, bytes, calls, rows, done)."""
    st = json.load(io.open(STATE, encoding='utf-8'))
    n = 0
    size = 0
    for d, _, fs in os.walk(OUTDIR):
        for f in fs:
            if f.endswith('.parquet'):
                n += 1
                size += os.path.getsize(os.path.join(d, f))
    return n, size, int(st.get('calls', 0)), int(st.get('rows', 0)), len(st.get('done', {}))


def history(calls, rows, files):
    """Append today's reading and return the rows, oldest first.

    One line per watcher run. This is the only record of the RATE: the state file knows how far the
    crawl has got but not how fast, and a projected finish date computed from the planner's
    assumptions rather than from what the machine actually achieves is a guess dressed as a fact.
    """
    today = datetime.date.today().isoformat()
    rows_out = []
    try:
        if os.path.exists(HISTORY):
            with io.open(HISTORY, encoding='utf-8') as fh:
                for ln in fh:
                    parts = ln.rstrip('\n').split('\t')
                    if len(parts) == 4 and parts[0] != 'date':
                        rows_out.append((parts[0], int(parts[1]), int(parts[2]), int(parts[3])))
    except Exception:
        rows_out = []
    # one row per day: a second run on the same day replaces the first rather than doubling it
    rows_out = [r for r in rows_out if r[0] != today]
    rows_out.append((today, calls, rows, files))
    rows_out.sort()
    try:
        with io.open(HISTORY, 'w', encoding='utf-8') as fh:
            fh.write('date\tcalls\trows\tfiles\n')
            for r in rows_out:
                fh.write('%s\t%d\t%d\t%d\n' % r)
    except Exception:
        pass
    return rows_out


NOMINAL_CALLS_PER_DAY = 880      # the run budget: 380 on key #1 (the rest is the refresh
                                 # reserve) + 500 on key #2


def project(hist, calls):
    """(calls_per_day, days_left, finish_date, basis) - or None while nothing can be said.

    The rate is NOT the difference between the last two readings. Each reading is a snapshot taken
    whenever the watcher happened to run, and a run takes about two hours: comparing yesterday
    mid-afternoon with today ten minutes into a run gave "150 calls/day -> finishing June 2030",
    off by nearly four years, because 150 was simply how far into today's run the reading landed.

    So full days only. Today's row is always partial and is excluded, and two complete days are
    needed before anything is measured. Until then the budget is quoted as what it is - a planned
    rate, labelled as such - rather than dressed up as an observation.
    """
    import datetime as _dt
    today = _dt.date.today().isoformat()
    full = [r for r in hist if r[0] != today]
    left = max(0, TOTAL_CALLS_EST - calls)

    if len(full) >= 2:
        try:
            d0 = _dt.date.fromisoformat(full[0][0])
            d1 = _dt.date.fromisoformat(full[-1][0])
        except Exception:
            return None
        span = (d1 - d0).days
        gained = full[-1][1] - full[0][1]
        if span >= 1 and gained > 0:
            rate = gained / float(span)
            days = int(round(left / rate))
            return rate, days, _dt.date.today() + _dt.timedelta(days=days), 'measured over %d full days' % span

    rate = float(NOMINAL_CALLS_PER_DAY)
    days = int(round(left / rate))
    return rate, days, _dt.date.today() + _dt.timedelta(days=days), 'planned rate, not yet measured'


def summary():
    """Two lines of where the crawl has got to and when it is due to finish."""
    try:
        n, size, calls, rows, done = reading()
    except Exception:
        return ['  (could not summarise progress)'], None
    pct = 100.0 * calls / float(TOTAL_CALLS_EST)
    lines = ['  %s files, %.2f GB, %s rows, %s reporter-months'
             % (format(n, ','), size / (1024.0 ** 3), format(rows, ','), format(done, ',')),
             '  %s of ~%s calls spent - %.2f%% of the job'
             % (format(calls, ','), format(TOTAL_CALLS_EST, ','), pct)]
    hist = history(calls, rows, n)
    pr = project(hist, calls)
    if pr:
        rate, days, when, basis = pr
        lines.append('  %s calls/day (%s) -> ~%d days left, finishing about %s'
                     % (format(int(rate), ','), basis, days, when.strftime('%d %b %Y')))
        head = '%.1f%% done, ~%d days left (about %s)' % (pct, days, when.strftime('%d %b %Y'))
    else:
        lines.append('  not enough history to project yet')
        head = '%.2f%% done, %s rows stored so far' % (pct, format(rows, ','))
    return lines, head


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
    sumlines, progress = summary()
    # A toast goes up EVERY day, not only on trouble. "Keep me informed" is not satisfied by a
    # status that only speaks when something breaks: an eight-month job that is quietly healthy
    # still needs to say how far it has got, or the only way to know is to come and ask.
    if warns:
        head = 'NOT HEALTHY - %d warning(s)' % len(warns)
        body = warns[0]
    else:
        head = 'healthy'
        body = progress or 'running'
    shown = toast('Atlas Comtrade crawl', body) if not quiet else False
    lines = ['%s  comtrade universe crawl: %s' % (stamp, head)]
    lines += ['  - ' + w for w in warns]
    lines += sumlines
    if not quiet:
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

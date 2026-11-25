# -*- coding: utf-8 -*-
"""One-shot scheduled runner for Windows Task Scheduler (or cron): grow Comtrade coverage a little,
refresh every source cache, rebuild the parquets. National customs data is monthly, so a WEEKLY cadence
keeps it fresh with headroom while the Comtrade rotation slowly widens coverage. Appends a timestamped
transcript to pipeline/data/scheduled.log so you can see what each run did.

Register (daily, 03:00). The execution-time limit MUST be larger than a run: a full night is
pull_comtrade (~27 min) + refresh (~100 min) + build (~4 min), and the 30-minute default killed
every run from 2026-09-06 to 2026-09-17 silently. WakeToRun and the restart settings were added
2026-10-02 after two more runs died mid-refresh (2026-09-25, 2026-10-01) because the machine slept
underneath them - the run now also blocks sleep itself, see _stay_awake.
  schtasks /create /tn "CMA-trade-refresh" /tr "<python.exe> <repo>\pipeline\scheduled_run.py" /sc daily /st 03:00 /f
  powershell -c "$s = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 3) -StartWhenAvailable -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 20) -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries; $s.WakeToRun = $true; Set-ScheduledTask -TaskName CMA-trade-refresh -Settings $s"

Health is watched: pipeline/refresh_watch.py (CMA-refresh-watch, daily 13:00) toasts when a run
dies and writes pipeline/data/refresh_status.txt. check.py's `refresh` check reads the same log.
Remove:  schtasks /delete /tn "CMA-trade-refresh" /f
Run now: schtasks /run /tn "CMA-trade-refresh"
Health:  the last lines of pipeline/data/scheduled.log should be a recent "run finished, exits".

ON THE SERVER (from 18 Nov 2026; the Windows task above is disabled). The Lenovo holds the whole
UN bulk corpus, so the API step - pull_comtrade.py, one month a night through the same key and
the same daily quota - is gone: it was a second download of the same database. Server mode is
switched on by CMA_CORPUS, the folder of the bulk downloader (~/comtrade), and runs:
  1. the corpus keep-fresh pass, monthly then yearly (pull_comtrade_bulk.py --recheck): one
     listing call per recent period, a download only where the UN published something new or
     corrected. Skipped while the full download (comtrade-bulk.service) still runs - they share
     the quota - and stopped, not slept, if the quota is spent (--quota-exit).
  2. reconcile/extract_comtrade_crm.py: re-cuts the atlas's codes for the years that changed.
  3. refresh.py, build.py as before; adapter_comtrade now reads the extract.
Systemd user units: atlas-nightly.service + atlas-nightly.timer (02:00), see pipeline/server/.
"""
import ctypes, os, sys, subprocess, datetime, time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PY = sys.executable
LOG = os.path.join(HERE, 'data', 'scheduled.log')
# The downloader is run from the REPOSITORY with ATLAS_ROOT pointing at the corpus (24 Nov 2026).
# Before, the corpus held its own copy (~/comtrade/reconcile/), which silently missed every change.
DL = os.path.join(REPO, 'reconcile', 'pull_comtrade_bulk.py')
# Download jobs the nightly works through after the build, one line each (see the file).
QUEUE = os.path.join(HERE, 'server', 'backfill_queue.txt')
BACKFILL_MIN = float(os.environ.get('CMA_BACKFILL_MIN', '200'))   # the unit's limit is 5 h; a run takes ~1 h



# Windows lets the machine sleep underneath a running scheduled task, and a slept run dies leaving a
# START with no END - exactly what killed 2026-09-25 and 2026-10-01, both inside refresh.py, which
# is the long step (~100 minutes against ~27 for the pull). Task Scheduler has no "do not sleep
# while running" setting; the RUN has to say so itself. ES_SYSTEM_REQUIRED keeps the system awake,
# ES_CONTINUOUS makes it hold until cleared, and ES_AWAYMODE_REQUIRED keeps it working with the
# screen off. The display is deliberately NOT kept on - this runs at 3am.
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_AWAYMODE_REQUIRED = 0x00000040


def _stay_awake(on):
    """Ask Windows not to sleep while the run is in progress. Best effort, and it says what
    happened: a failure here costs a whole night, so it must not be silent."""
    if not sys.platform.startswith('win'):
        return None
    full = ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_AWAYMODE_REQUIRED
    try:
        r = ctypes.windll.kernel32.SetThreadExecutionState(
            ctypes.c_uint(full if on else ES_CONTINUOUS))
    except Exception as e:                       # never take the run down over this
        return 'could not call SetThreadExecutionState: %s' % e
    if r == 0 and on:
        # away mode needs a power policy some machines refuse; retry without it before giving up
        try:
            r = ctypes.windll.kernel32.SetThreadExecutionState(
                ctypes.c_uint(ES_CONTINUOUS | ES_SYSTEM_REQUIRED))
        except Exception as e:
            return 'retry without away mode failed: %s' % e
        if r == 0:
            return 'the OS refused the sleep block - the machine may still sleep mid-run'
        return 'held WITHOUT away mode (a screen-off suspend may still interrupt the run)'
    return None


def _log(text):
    """Append immediately. The log used to be written once, after the last step, so when Task
    Scheduler killed a run at its 30-minute limit it left NO trace: eleven nightly runs from
    2026-09-06 vanished and the last line in the log still read like a healthy run. A step that
    dies now leaves its own line behind."""
    with open(LOG, 'a', encoding='utf8') as f:
        f.write(text + '\n')
        f.flush()


def _run(args):
    t0 = datetime.datetime.now()
    _log('--- %s  START %s' % (t0.isoformat(timespec='seconds'), ' '.join(args)))
    r = subprocess.run([PY] + args, cwd=REPO, capture_output=True, text=True)
    out = (r.stdout or '') + (r.stderr or '')
    secs = (datetime.datetime.now() - t0).total_seconds()
    _log(out.rstrip())
    _log('--- END %s  exit %d  %.0fs' % (' '.join(args), r.returncode, secs))
    return r.returncode


def _run_in(args, cwd, py, env=None):
    """_run for a program outside the repo (the corpus downloader) - same log format."""
    t0 = datetime.datetime.now()
    _log('--- %s  START %s' % (t0.isoformat(timespec='seconds'), ' '.join(args)))
    e = dict(os.environ, **(env or {}))
    r = subprocess.run([py] + args, cwd=cwd, capture_output=True, text=True, env=e)
    out = (r.stdout or '') + (r.stderr or '')
    # The downloader's per-file lines are already in its own log; keep the tail here.
    lines = out.rstrip().splitlines()
    _log('\n'.join(lines[-40:]))
    _log('--- END %s  exit %d  %.0fs' % (' '.join(args), r.returncode,
                                        (datetime.datetime.now() - t0).total_seconds()))
    return r.returncode


def _server_steps(corpus):
    cpy = os.path.join(corpus, '.venv', 'bin', 'python')
    if not os.path.exists(cpy):
        cpy = PY
    codes = []
    busy = subprocess.run(['systemctl', '--user', 'is-active', 'comtrade-bulk.service'],
                          capture_output=True, text=True).stdout.strip() == 'active'
    if busy:
        _log('--- the full bulk download is still running: keep-fresh pass skipped tonight')
    else:
        root = {'ATLAS_ROOT': corpus}
        codes.append(_run_in([DL, '--all-codes', '--recheck', '24', '--quota-exit'], corpus, cpy, root))
        codes.append(_run_in([DL, '--all-codes', '--freq', 'A', '--cl', 'HS', '--recheck', '3',
                              '--quota-exit'], corpus, cpy, root))
        # Keep-fresh for the sets finished by the backfill queue (25 Nov 2026): 3 listing calls each.
        # Logged but not counted as refresh steps: a skipped recheck must not fail the atlas build.
        for extra in (['--tariffline', '--freq', 'A'], ['--type', 'S', '--freq', 'A', '--cl', 'EB']):
            _run_in([DL, '--all-codes'] + extra + ['--recheck', '3', '--quota-exit'], corpus, cpy, root)
    codes.append(_run_in(['reconcile/extract_comtrade_crm.py'], REPO, PY,
                         {'CMA_BULK_DIR': os.path.join(corpus, 'raw', 'comtrade_bulk')}))
    codes.append(_run(['pipeline/refresh.py', 'all', '--periods', '3']))
    codes.append(_run(['pipeline/build.py']))
    return codes


def _backfill(corpus, minutes=BACKFILL_MIN):
    """The download queue: each job resumes where it stopped (the downloader keeps its own state and
    caches the UN listings, so a finished job costs no quota), stops between files when the night's
    budget is spent, and stops - not sleeps - on an exhausted quota. Runs AFTER the build, so it can
    never delay the atlas. Its exits are logged apart: a stalled download is not a failed refresh."""
    if not os.path.exists(QUEUE):
        return []
    cpy = os.path.join(corpus, '.venv', 'bin', 'python')
    if not os.path.exists(cpy):
        cpy = PY
    t0, codes = time.time(), []
    for line in open(QUEUE, encoding='utf-8'):
        job = line.split('#')[0].split()
        if not job:
            continue
        left = minutes - (time.time() - t0) / 60
        if left < 5:
            _log('--- backfill: %g minutes spent tonight; the rest waits for tomorrow' % minutes)
            break
        codes.append(_run_in([DL] + job + ['--quota-exit', '--max-minutes', '%d' % left], corpus, cpy,
                             {'ATLAS_ROOT': corpus}))
    return codes


def main():
    stamp = datetime.datetime.now().isoformat(timespec='seconds')
    _log(f"\n===== scheduled run {stamp} =====")
    note = _stay_awake(True)
    if note:
        _log('--- sleep block: %s' % note)
    corpus = os.environ.get('CMA_CORPUS')
    if corpus and '--backfill-only' in sys.argv:       # by hand: python pipeline/scheduled_run.py --backfill-only [MIN]
        mins = [float(x) for x in sys.argv[1:] if x.replace('.', '', 1).isdigit()]
        _log('--- backfill exits %s' % (_backfill(corpus, *mins),))
        return
    if corpus:
        codes = _server_steps(corpus)
        _stay_awake(False)
        _log('===== scheduled run finished, exits %s =====' % (codes,))
        _log('--- backfill exits %s' % (_backfill(corpus),))
        # A failed step now fails the run (24 Nov 2026), so `systemctl --user status` shows it.
        # The backfill's exits do not count: a stalled download is not a failed refresh.
        return 1 if any(codes) else 0
    codes = [
        # ALL reporters, one month per run. The goal is maximum country coverage, and with
        # the measured pause that is ~19 minutes at 3am rather than 3 minutes - which buys
        # a whole month of the BACI gap per night instead of an eighth of one.
        _run(['pipeline/pull_comtrade.py', 'all']),
        # --periods 3: refresh used to take only the newest period a source offered, which
        # with an overwriting cache meant the caches could never hold more than one month.
        # Both are fixed; asking for several is what actually builds the series.
        _run(['pipeline/refresh.py', 'all', '--periods', '3']),
        _run(['pipeline/build.py']),                      # assemble flows / flows_best / flows_reconciled
    ]
    _stay_awake(False)
    _log('===== scheduled run finished, exits %s =====' % (codes,))
    print(f"scheduled run complete {stamp}  ->  {LOG}")
    return 1 if any(codes) else 0


if __name__ == '__main__':
    sys.exit(main())

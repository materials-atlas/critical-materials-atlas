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
"""
import ctypes, os, sys, subprocess, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PY = sys.executable
LOG = os.path.join(HERE, 'data', 'scheduled.log')



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


def main():
    stamp = datetime.datetime.now().isoformat(timespec='seconds')
    _log(f"\n===== scheduled run {stamp} =====")
    note = _stay_awake(True)
    if note:
        _log('--- sleep block: %s' % note)
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


if __name__ == '__main__':
    main()

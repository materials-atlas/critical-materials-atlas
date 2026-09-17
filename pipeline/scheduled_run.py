# -*- coding: utf-8 -*-
"""One-shot scheduled runner for Windows Task Scheduler (or cron): grow Comtrade coverage a little,
refresh every source cache, rebuild the parquets. National customs data is monthly, so a WEEKLY cadence
keeps it fresh with headroom while the Comtrade rotation slowly widens coverage. Appends a timestamped
transcript to pipeline/data/scheduled.log so you can see what each run did.

Register (daily, 03:00). The execution-time limit MUST be larger than a run: a full night is
pull_comtrade (~19 min) + refresh + build, and the 30-minute default killed every run from
2026-09-06 to 2026-09-17 silently.
  schtasks /create /tn "CMA-trade-refresh" /tr "\"<python.exe>\" \"<repo>\pipeline\scheduled_run.py\"" /sc daily /st 03:00 /f
  powershell -c "Set-ScheduledTask -TaskName CMA-trade-refresh -Settings (New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 3) -StartWhenAvailable)"
Remove:  schtasks /delete /tn "CMA-trade-refresh" /f
Run now: schtasks /run /tn "CMA-trade-refresh"
Health:  the last lines of pipeline/data/scheduled.log should be a recent "run finished, exits".
"""
import os, sys, subprocess, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PY = sys.executable
LOG = os.path.join(HERE, 'data', 'scheduled.log')


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
    _log('===== scheduled run finished, exits %s =====' % (codes,))
    print(f"scheduled run complete {stamp}  ->  {LOG}")


if __name__ == '__main__':
    main()

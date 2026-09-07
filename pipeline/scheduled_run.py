# -*- coding: utf-8 -*-
"""One-shot scheduled runner for Windows Task Scheduler (or cron): grow Comtrade coverage a little,
refresh every source cache, rebuild the parquets. National customs data is monthly, so a WEEKLY cadence
keeps it fresh with headroom while the Comtrade rotation slowly widens coverage. Appends a timestamped
transcript to pipeline/data/scheduled.log so you can see what each run did.

Register (weekly, Sunday 03:00):
  schtasks /create /tn "CMA-trade-refresh" /tr "\"<python.exe>\" \"<repo>\pipeline\scheduled_run.py\"" /sc weekly /d SUN /st 03:00 /f
Remove:  schtasks /delete /tn "CMA-trade-refresh" /f
Run now: schtasks /run /tn "CMA-trade-refresh"
"""
import os, sys, subprocess, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PY = sys.executable
LOG = os.path.join(HERE, 'data', 'scheduled.log')


def _run(args):
    r = subprocess.run([PY] + args, cwd=REPO, capture_output=True, text=True)
    return (r.stdout or '') + (r.stderr or '')


def main():
    stamp = datetime.datetime.now().isoformat(timespec='seconds')
    parts = [f"\n===== scheduled run {stamp} =====",
             # ALL reporters, one month per run. The goal is maximum country coverage, and with
             # the measured pause that is ~19 minutes at 3am rather than 3 minutes - which buys
             # a whole month of the BACI gap per night instead of an eighth of one.
             _run(['pipeline/pull_comtrade.py', 'all']),
             # --periods 3: refresh used to take only the newest period a source offered, which
             # with an overwriting cache meant the caches could never hold more than one month.
             # Both are fixed; asking for several is what actually builds the series.
             _run(['pipeline/refresh.py', 'all', '--periods', '3']),
             _run(['pipeline/build.py'])]                 # assemble flows / flows_best / flows_reconciled
    with open(LOG, 'a', encoding='utf8') as f:
        f.write('\n'.join(parts) + '\n')
    print(f"scheduled run complete {stamp}  ->  {LOG}")


if __name__ == '__main__':
    main()

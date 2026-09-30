# -*- coding: utf-8 -*-
"""Tell somebody when the nightly data refresh stops working.

WHY THIS EXISTS. The refresh is the only thing that moves the Comtrade months past BACI's cutoff,
and it fails without a symptom: Task Scheduler killed eleven consecutive nightly runs in September
2026 at the old 30-minute limit, and nothing anywhere said so - the site stayed correct, the repo
stayed pushed, and the caches just quietly stopped ageing forward. The step-by-step log added after
that makes a killed run VISIBLE, and check.py's `refresh` check reads it, but both need somebody to
go and look. 25 Sep 2026 died mid-refresh and 27 Sep never ran at all, and both were found only by
reading the log by hand a week later. A trace nobody reads is not an alert.

So this runs on its own schedule, asks check.py the question, and pushes the answer OUT: a Windows
toast when something is wrong, and a one-line status file either way that can be read without
running anything.

    python pipeline/refresh_watch.py            # toast on trouble, always write the status file
    python pipeline/refresh_watch.py --quiet    # status file only, no toast

Register (daily, 13:00 - late enough that a run started at 03:00, or started late because the
machine was off, has had time to finish):
  schtasks /create /tn "CMA-refresh-watch" /tr "\"<python.exe>\" \"<repo>\pipeline\refresh_watch.py\"" /sc daily /st 13:00 /f
Remove:  schtasks /delete /tn "CMA-refresh-watch" /f
Status:  type pipeline\data\refresh_status.txt

It always exits 0. A watcher whose own failure needs watching is not worth having.
"""
import datetime
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
STATUS = os.path.join(HERE, 'data', 'refresh_status.txt')
# The toast has to be attributed to a registered AppID or Windows drops it silently. Windows
# Terminal is present on this machine and is where the refresh runs from, so it is the honest
# attribution as well as the working one.
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


def ask_check():
    """What check.py's refresh check says. Returns (warnings, raw output)."""
    r = subprocess.run([sys.executable, 'check.py', 'refresh'], cwd=REPO,
                       capture_output=True, text=True)
    out = (r.stdout or '') + (r.stderr or '')
    warns = [ln.split('refresh:', 1)[1].strip()
             for ln in out.splitlines() if ln.strip().startswith('warn  refresh:')]
    return warns, out


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
    warns, raw = ask_check()
    stamp = datetime.datetime.now().isoformat(timespec='seconds')
    if warns:
        head = 'NOT HEALTHY - %d warning(s)' % len(warns)
        shown = toast('Atlas nightly refresh', warns[0]) if not quiet else False
    else:
        head = 'healthy'
        shown = False
    lines = ['%s  nightly refresh: %s' % (stamp, head)]
    lines += ['  - ' + w for w in warns]
    if warns and not quiet:
        lines.append('  (toast %s)' % ('shown' if shown else 'could NOT be raised'))
    lines.append('  asked: python check.py refresh   log: pipeline/data/scheduled.log')
    text = '\n'.join(lines) + '\n'
    with io.open(STATUS, 'w', encoding='utf8') as fh:
        fh.write(text)
    # pythonw.exe - which is what the scheduled task uses, so no console window appears - has no
    # stdout, and writing to it raised, so the task reported LastTaskResult 1 while having done its
    # job perfectly. A watcher that reports its own failure falsely is worse than none.
    try:
        sys.stdout.write(text)
    except Exception:
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main())

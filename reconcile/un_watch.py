# -*- coding: utf-8 -*-
"""Watch for UN Comtrade's reply about premium access, and say so the moment it lands.

Why this exists. The whole shape of the crawl depends on one email that has not arrived: the UN
granted a complimentary one-year premium account with bulk file access on 8 Oct 2026, asked which
address to register, was answered on 9 Oct, and has been silent since. Premium turns a ~644-day
crawl into a few hours of downloads, so nothing about the plan is settled until it appears. Up to
now the only way to know was to open the mailbox and look, which means the answer arrives when
somebody thinks to ask rather than when the mail does.

Where it looks, and why two places:

  Yahoo, through classic Outlook  the address given to the UN for the premium account is
                                 a personal address, so the provisioning mail lands THERE, not
                                 in the company mailbox. Outlook COM reads it with no browser and
                                 no session to keep alive, which makes it the reliable half.
  contact@, through robot Edge    a reply to the request thread goes to the company mailbox, which
                                 is not in the Outlook profile. This half needs Edge up on CDP
                                 9222, so it is best-effort: when Edge is away the run still
                                 reports, and says which half it could not see.

It announces each message ONCE. Without that it would toast the same mail every two hours until
somebody turned it off, and a watcher people turn off is worse than none.

It never exits non-zero. A watcher whose task shows "failed" gets ignored, and then the thing it
was watching is unwatched again - see reference_scheduled_task_silent_death.
"""
import io
import json
import os
import re
import subprocess
import sys
import time

# Mail subjects carry accents, emoji and Outlook's invisible layout characters, and this console
# is cp1252. Without this the status text raised UnicodeEncodeError on the way to the screen, and
# because that write is deliberately wrapped so it cannot fail the task, the run printed nothing
# at all on precisely the runs that had a new message to announce.
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass                # pythonw.exe has no stdout buffer to wrap, which is fine

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
STATE = os.path.join(REPO, 'raw', 'comtrade_full', '_un_watch.json')
STATUS = os.path.join(REPO, 'raw', 'comtrade_full', '_un_status.txt')
LOG = os.path.join(REPO, 'raw', 'comtrade_full', '_un_watch.log')

APPID = 'Microsoft.WindowsTerminal_8wekyb3d8bbwe!App'
DAYS_BACK = 14

# What counts as the mail we are waiting for.
#
# The first version also matched 'premium', 'bulk', 'subscription' and 'api key' in a subject from
# anyone, on the theory that provisioning might come from a billing system rather than a person.
# Run once against the real mailboxes it immediately flagged "Upcoming changes to your Microsoft
# 365 subscription" - and a watcher that cries wolf every two hours gets switched off, which
# leaves the thing unwatched. So: the sender must look like the UN, or the subject must actually
# say Comtrade, or it must be a reply on the existing thread.
SENDER_RE = re.compile(r'(@un\.org|unstats|comtradeplus|comtrade@)', re.I)
SUBJECT_RE = re.compile(r'(comtrade|research access request)', re.I)

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

# Inbox (6) and Junk (23). A grant mail with a link in it is exactly the shape a spam filter
# dislikes, so Junk is not optional. GetFirst/GetNext rather than foreach: the COM collection is
# not a stable snapshot and foreach skips items on it.
PS_OUTLOOK = r'''
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ol = New-Object -ComObject Outlook.Application
$ns = $ol.GetNamespace("MAPI")
$cut = (Get-Date).AddDays(-1 * [int]$env:CMA_DAYS)
foreach ($st in $ns.Stores) {
  foreach ($fid in @(6, 23)) {
    try { $f = $st.GetDefaultFolder($fid) } catch { continue }
    try { $items = $f.Items; $items.Sort("[ReceivedTime]", $true) } catch { continue }
    $m = $items.GetFirst(); $n = 0
    while ($m -ne $null -and $n -lt 250) {
      $n++
      try {
        if ($m.ReceivedTime -lt $cut) { break }
        $from = "$($m.SenderEmailAddress)"
        $name = "$($m.SenderName)"
        $subj = "$($m.Subject)"
        $id   = "$($m.EntryID)"
        $when = $m.ReceivedTime.ToString("yyyy-MM-ddTHH:mm:ss")
        "$($st.DisplayName)`t$when`t$from`t$name`t$subj`t$id"
      } catch {}
      $m = $items.GetNext()
    }
  }
}
'''


def log(msg):
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with io.open(LOG, 'a', encoding='utf-8') as fh:
            fh.write('%s  %s\n' % (time.strftime('%Y-%m-%dT%H:%M:%S'), msg))
    except Exception:
        pass


def toast(title, body):
    """Best effort. A notification that cannot be raised must not take the run down."""
    env = dict(os.environ, CMA_TOAST_TITLE=title, CMA_TOAST_BODY=body[:220], CMA_TOAST_APPID=APPID)
    try:
        r = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', PS_TOAST],
                           capture_output=True, text=True, env=env, timeout=60,
                           encoding='utf-8', errors='replace')
        return r.returncode == 0
    except Exception:
        return False


def load_seen():
    try:
        return set(json.load(io.open(STATE, encoding='utf-8')).get('announced') or [])
    except Exception:
        return set()


def save_seen(seen):
    try:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        tmp = STATE + '.tmp'
        json.dump({'announced': sorted(seen), 'checked': time.strftime('%Y-%m-%dT%H:%M:%S')},
                  io.open(tmp, 'w', encoding='utf-8'))
        os.replace(tmp, STATE)
    except Exception as e:
        log('could not save state: %s' % type(e).__name__)


def matches(sender, name, subject):
    return bool(SENDER_RE.search('%s %s' % (sender, name)) or SUBJECT_RE.search(subject))


def from_outlook():
    """(hits, note). Yahoo and the other Outlook accounts, via COM."""
    env = dict(os.environ, CMA_DAYS=str(DAYS_BACK))
    try:
        r = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', PS_OUTLOOK],
                           capture_output=True, text=True, env=env, timeout=300,
                           encoding='utf-8', errors='replace')
    except Exception as e:
        return [], 'Outlook could not be read (%s)' % type(e).__name__
    if r.returncode != 0:
        return [], 'Outlook returned an error (%s)' % (r.stderr or '')[:90].replace('\n', ' ')
    hits = []
    for line in (r.stdout or '').splitlines():
        parts = line.rstrip('\n').split('\t')
        if len(parts) != 6:
            continue
        store, when, sender, name, subject, eid = parts
        if matches(sender, name, subject):
            hits.append({'where': store, 'when': when, 'from': sender or name,
                         'subject': subject, 'id': 'ol:' + eid[-40:]})
    return hits, None


def from_company_mailbox():
    """(hits, note). contact@, via the robot Edge. Best effort: Edge may simply not be running."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return [], 'playwright not available, company mailbox not checked'
    try:
        with sync_playwright() as p:
            b = p.chromium.connect_over_cdp('http://127.0.0.1:9222')
            pg = b.contexts[0].new_page()
            try:
                hits = []
                for folder in ('', 'junkemail'):
                    pg.goto('https://outlook.cloud.microsoft/mail/' + folder,
                            wait_until='domcontentloaded', timeout=60000)
                    pg.wait_for_timeout(9000)
                    for row in pg.query_selector_all('[role="option"], div[data-convid]'):
                        t = ' '.join((row.inner_text() or '').split())
                        # A row reads: sender, then subject, then a preview of the body. Matching
                        # the whole thing made our own delivery-test mail a hit, because its body
                        # quotes omtrade@un.org. The head is the sender plus the subject's start.
                        head = t[:60]
                        if t and matches(head, '', head):
                            hits.append({'where': 'contact@ (%s)' % (folder or 'inbox'),
                                         'when': '', 'from': '', 'subject': t[:150],
                                         'id': 'm365:' + head})
                return hits, None
            finally:
                pg.close()
    except Exception as e:
        return [], 'company mailbox not checked (Edge on CDP 9222 unreachable: %s)' % type(e).__name__


def main():
    quiet = '--quiet' in sys.argv
    seen = load_seen()
    notes = []

    ol_hits, ol_note = from_outlook()
    if ol_note:
        notes.append(ol_note)
    m365_hits, m365_note = from_company_mailbox()
    if m365_note:
        notes.append(m365_note)

    hits = ol_hits + m365_hits
    fresh = [h for h in hits if h['id'] not in seen]

    stamp = time.strftime('%Y-%m-%dT%H:%M:%S')
    lines = ['%s  UN Comtrade reply watch' % stamp]
    if fresh:
        lines.append('  *** %d NEW message(s) that look like the UN reply ***' % len(fresh))
        for h in fresh:
            lines.append('   - [%s] %s  %s | %s' % (h['where'], h['when'], h['from'], h['subject']))
    else:
        lines.append('  nothing new. %d known message(s) already seen in the last %d days'
                     % (len(hits), DAYS_BACK))
    for n in notes:
        lines.append('  note: %s' % n)
    lines.append('  waiting on: premium account provisioning (registered to a personal address)')
    text = '\n'.join(lines) + '\n'

    if fresh and not quiet:
        first = fresh[0]
        toast('UN Comtrade replied', '%s | %s' % (first['from'] or first['where'],
                                                  first['subject'][:150]))
    for h in fresh:
        log('NEW %s | %s | %s' % (h['where'], h['from'], h['subject'][:120]))
        seen.add(h['id'])
    if not fresh:
        log('nothing new (%d known)%s' % (len(hits), ' - ' + '; '.join(notes) if notes else ''))
    save_seen(seen)

    try:
        with io.open(STATUS, 'w', encoding='utf-8') as fh:
            fh.write(text)
    except Exception:
        pass
    try:
        sys.stdout.write(text)
    except Exception:
        pass            # pythonw.exe has no stdout; writing to it must not fail the task
    return 0


if __name__ == '__main__':
    sys.exit(main())

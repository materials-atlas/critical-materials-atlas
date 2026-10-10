# Register the UN Comtrade reply watch with Task Scheduler.
#
# Everything about the crawl's shape depends on one email that has not arrived: the UN granted a
# complimentary premium account with bulk file access on 8 Oct 2026 and has been silent since the
# reply on 9 Oct. Premium turns a ~644-day crawl into hours of downloads. Until this task existed
# the only way to know was to go and look, so the answer arrived when somebody thought to ask
# rather than when the mail did.
#
# Every two hours between 08:00 and 22:00, rather than once a day: the point is to hear within the
# working half-day, and the check is cheap - it reads two mailboxes and writes a line.
#
# pythonw.exe to match the other tasks (no console window). It has no stdout, which is why
# un_watch.py wraps its own print and never exits non-zero: a task that reports failure gets
# ignored, and then the thing it watches is unwatched again.

$ErrorActionPreference = 'Stop'

$TaskName = 'CMA-un-watch'
$Pythonw  = 'C:\Users\tomas\AppData\Local\Programs\Python\Python311\pythonw.exe'
$Root     = 'C:\Toma\critical-materials-atlas'
$Script   = Join-Path $Root 'reconcile\un_watch.py'

if (-not (Test-Path $Pythonw)) { throw "pythonw not found at $Pythonw" }
if (-not (Test-Path $Script))  { throw "script not found at $Script" }

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
  "unregistered the previous $TaskName"
}

$action = New-ScheduledTaskAction -Execute $Pythonw -Argument "`"$Script`"" -WorkingDirectory $Root

# A daily trigger that repeats: 08:00, then every 2 hours for 14 hours, so the last check is 22:00.
$trigger = New-ScheduledTaskTrigger -Daily -At 08:00
$trigger.Repetition = (New-ScheduledTaskTrigger -Once -At 08:00 `
                        -RepetitionInterval (New-TimeSpan -Hours 2) `
                        -RepetitionDuration (New-TimeSpan -Hours 14)).Repetition

# StartWhenAvailable so a check missed while the laptop slept runs on waking; no WakeToRun,
# because waking a sleeping laptop every two hours to read a mailbox is not worth it. Battery is
# allowed: this costs seconds.
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 20) `
              -StartWhenAvailable `
              -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
              -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
  -Settings $settings -Description 'Watch for UN Comtrade premium/bulk access reply (Yahoo via Outlook + contact@ via Edge)' | Out-Null

$t = Get-ScheduledTask -TaskName $TaskName
$i = $t | Get-ScheduledTaskInfo
"registered $TaskName"
"  state      : $($t.State)"
"  limit      : $($t.Settings.ExecutionTimeLimit)"
"  next run   : $($i.NextRunTime)"
"  repetition : every $($t.Triggers[0].Repetition.Interval) for $($t.Triggers[0].Repetition.Duration)"

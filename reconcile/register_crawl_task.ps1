# Register the daily full-universe Comtrade crawl with Task Scheduler.
#
# NOT RUN AUTOMATICALLY. Running this arms the crawl: from the next 05:00 it will start calling the
# UN Comtrade API every day until the universe is down. Run it when you want the crawl to begin.
#
#   powershell -ExecutionPolicy Bypass -File reconcile\register_crawl_task.ps1
#   powershell -ExecutionPolicy Bypass -File reconcile\register_crawl_task.ps1 -Unregister
#
# 05:00 is deliberate: CMA-trade-refresh runs at 03:00 with a 3-hour limit and pulls Comtrade from
# the SAME key (#1) against the same 500/day allowance. The crawl leaves it ~120 there.
#
# Two keys since 6 Oct 2026: 880/day = 380 on key #1 (500 less the refresh reserve) + 500 on key #2.
# That is 2.3x the one-key rate, not 2x, because only key #1 carries the reserve.
#
# pythonw.exe is used to match the existing tasks (no console window). It has no stdout, which is
# why the work goes through crawl_scheduled.py and the log is a file.

param([switch]$Unregister)

$ErrorActionPreference = 'Stop'
$TaskName = 'CMA-comtrade-universe'
$Root     = Split-Path -Parent $PSScriptRoot
$Pythonw  = 'C:\Users\tomas\AppData\Local\Programs\Python\Python311\pythonw.exe'
$Script   = Join-Path $Root 'reconcile\crawl_scheduled.py'

if ($Unregister) {
  if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Output "removed $TaskName"
  } else {
    Write-Output "$TaskName was not registered"
  }
  return
}

if (-not (Test-Path $Pythonw)) { throw "pythonw not found at $Pythonw" }
if (-not (Test-Path $Script))  { throw "crawl_scheduled.py not found at $Script" }

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
  Write-Output "$TaskName already exists - removing it first"
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$action  = New-ScheduledTaskAction -Execute $Pythonw -Argument "`"$Script`"" -WorkingDirectory $Root
$trigger = New-ScheduledTaskTrigger -Daily -At 05:00
# 8 hours. The first armed run, 6 Oct 2026, finished in 131 minutes: 881 calls at ~8.2s each.
#
# Mid-run I read the first 42 minutes (120 calls, ~21s each) and projected ~5 hours from it. That
# was wrong - the opening is slow because the crawl starts at 2026, where almost nothing is filed
# yet and the sizing calls earn little, and it speeds up markedly once it reaches years with data.
# A 42-minute sample of a 2-hour job is not a measurement of that job. The number here is from a
# completed run, not an extrapolation.
#
# So 4 hours would in fact have been enough. 8 stays anyway: the cost of spare headroom is zero,
# and the cost of being wrong is a run killed mid-day with no END line - the silent death that
# cost this repository eleven nights of refresh in September 2026.
# StartWhenAvailable catches up after a day the machine was off.
# WakeToRun because "never sleep" is not enough on a modern laptop: this machine entered Modern
# Standby (connected standby, S0ix) at 00:51 on 7 Oct 2026 with the sleep timeout set to Never, and
# the 05:00 trigger simply did not fire. StartWhenAvailable caught it up at 08:38 when the lid was
# opened, so nothing was lost that day - but a day nobody opens the laptop loses its whole
# allowance, and unused calls do not carry over.
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 8) `
              -MultipleInstances IgnoreNew -StartWhenAvailable -WakeToRun `
              -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
  -Settings $settings -Description 'Full-universe UN Comtrade monthly crawl, 880 calls/day across 2 keys' | Out-Null

Write-Output "registered $TaskName - daily 05:00, 880 calls, log at raw\comtrade_full\_crawl.log"
Write-Output "first run: tomorrow 05:00. To start one now:  python reconcile\crawl_scheduled.py --budget 50"

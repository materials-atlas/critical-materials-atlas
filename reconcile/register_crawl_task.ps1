# Register the daily full-universe Comtrade crawl with Task Scheduler.
#
# NOT RUN AUTOMATICALLY. Running this arms the crawl: from the next 05:00 it will start calling the
# UN Comtrade API every day until the universe is down. Run it when you want the crawl to begin.
#
#   powershell -ExecutionPolicy Bypass -File reconcile\register_crawl_task.ps1
#   powershell -ExecutionPolicy Bypass -File reconcile\register_crawl_task.ps1 -Unregister
#
# 05:00 is deliberate: CMA-trade-refresh runs at 03:00 with a 3-hour limit and pulls Comtrade from
# the SAME key against the same 500/day allowance. The crawl takes 380 and leaves it ~120.
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
# 4 hours: 380 calls at ~1.3s plus response time is well under an hour, but a slow day must not be
# killed mid-write. StartWhenAvailable catches up after a day the machine was off.
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 4) `
              -MultipleInstances IgnoreNew -StartWhenAvailable `
              -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
  -Settings $settings -Description 'Full-universe UN Comtrade monthly crawl, 380 calls/day' | Out-Null

Write-Output "registered $TaskName - daily 05:00, 380 calls, log at raw\comtrade_full\_crawl.log"
Write-Output "first run: tomorrow 05:00. To start one now:  python reconcile\crawl_scheduled.py --budget 50"

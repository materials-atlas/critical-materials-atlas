# refresh.ps1 - one command to rebuild the whole atlas from the live Comext API.
# Downloads every atlas material (value + quantity) into raw/, then regenerates index.html
# and all charts via build_static.R. Re-run whenever Eurostat Comext posts a new year:
# -EndPeriod defaults to the current year, so new data is picked up with no edits.
# After it finishes:  git add -A; git commit -m "Refresh atlas"; git push
#
#   powershell -File refresh.ps1                 # rebuild through the current year
#   powershell -File refresh.ps1 -EndPeriod 2025 # pin an explicit end year

param([int]$EndPeriod = (Get-Date).Year, [int]$StartPeriod = 2010)

$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
Set-Location $here

# The atlas: CN8 code -> short label. This is the canonical product list; the display
# titles and notes live in build_static.R. Add or remove a material here and there.
$atlas = [ordered]@{
  '85051110' = 'magnets';   '81041100' = 'magnesium'; '81129295' = 'germanium'
  '25049000' = 'graphite';  '81129289' = 'gallium';   '81019400' = 'tungsten'
  '28220000' = 'cobalt';    '28369100' = 'lithium';   '81101000' = 'antimony'
  '71101100' = 'platinum';  '81082000' = 'titanium';  '28046900' = 'silicon'
  '25280000' = 'boron';     '72029300' = 'niobium';   '71102100' = 'palladium'
  '25292200' = 'fluorspar'; '72029200' = 'vanadium';  '26020000' = 'manganese'
  '26060000' = 'bauxite';   '25101000' = 'phosphate'; '25111000' = 'baryte'
  '25291000' = 'feldspar'
}

Write-Output ("Refreshing {0} materials, periods {1}-{2} ..." -f $atlas.Count, $StartPeriod, $EndPeriod)
foreach ($code in $atlas.Keys) {
  & (Join-Path $here 'download_data.ps1') -Product $code -Label $atlas[$code] `
      -StartPeriod $StartPeriod -EndPeriod $EndPeriod > $null
  Write-Output ("  fetched {0} ({1})" -f $atlas[$code], $code)
}

# Locate Rscript - not always on PATH on Windows.
$rscript = (Get-Command Rscript -ErrorAction SilentlyContinue).Source
if (-not $rscript) {
  $rscript = (Get-ChildItem 'C:\Program Files\R\*\bin\Rscript.exe' -ErrorAction SilentlyContinue |
              Select-Object -Last 1).FullName
}
if (-not $rscript) { throw "Rscript not found - install R or add it to PATH." }

Write-Output "Rebuilding the static atlas ..."
& $rscript (Join-Path $here 'build_static.R')

Write-Output ""
Write-Output "Done. Review index.html, then publish:  git add -A; git commit -m 'Refresh atlas'; git push"

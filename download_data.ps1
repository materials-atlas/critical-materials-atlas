# download_data.ps1
# Fetches Comext extra-EU import data (value + quantity) for one product into raw/.
# R cannot reach Eurostat through some proxies (SSL error), so the download is done here
# in PowerShell, with the Accept-Encoding: identity header that prevents the
# gzip-as-text corruption. Run from anywhere; raw/ is derived from the script location.
#
# Parameterised by product so the same pipeline serves any CN8 code:
#   .\download_data.ps1                                  # default: magnets 85051110
#   .\download_data.ps1 -Product 81129231 -Label gallium
#   .\download_data.ps1 -Product 81129289 -Label germanium -StartPeriod 2015

param(
  [string]$Product     = '85051110',
  [string]$Label       = 'magnets',
  [int]   $StartPeriod = 2010,
  [int]   $EndPeriod   = 2024
)

# Write raw/ next to this script, which is where the R pipeline (run from the repo
# root) looks for it. $PSScriptRoot keeps the two halves in sync wherever the repo lives.
$repoDir = $PSScriptRoot
$raw = Join-Path $repoDir 'raw'
New-Item -ItemType Directory -Path $raw -Force | Out-Null

$base   = 'https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/'
$period = "?startPeriod=$StartPeriod&endPeriod=$EndPeriod&format=SDMX-CSV"

$urlVal = $base + 'A...' + $Product + '.1.VALUE_IN_EUROS'    + $period
$urlQty = $base + 'A...' + $Product + '.1.QUANTITY_IN_100KG' + $period

$outVal = Join-Path $raw ($Label + '_' + $Product + '_value.csv')
$outQty = Join-Path $raw ($Label + '_' + $Product + '_qty.csv')

Invoke-WebRequest -Uri $urlVal -OutFile $outVal -UseBasicParsing -Headers @{ 'Accept-Encoding' = 'identity' }
Write-Output ('Value file:    ' + (Get-Item $outVal).Length + ' bytes  ->  ' + $outVal)

Invoke-WebRequest -Uri $urlQty -OutFile $outQty -UseBasicParsing -Headers @{ 'Accept-Encoding' = 'identity' }
Write-Output ('Quantity file: ' + (Get-Item $outQty).Length + ' bytes  ->  ' + $outQty)

Write-Output ("Done (" + $Label + " " + $Product + "). Run: Rscript comext-magnet-dependency-demo.R  (or open the Shiny app)")

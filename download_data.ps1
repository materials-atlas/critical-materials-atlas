# download_data.ps1
# Fetches Comext extra-EU import data (value + quantity) for one product into raw/.
# R cannot reach Eurostat through the BdF proxy (SSL error), so the download is done
# here in PowerShell, with the Accept-Encoding: identity header that prevents the
# gzip-as-text corruption. Run from anywhere; paths are derived from your profile.

$repoDir = Join-Path (Join-Path (Join-Path $env:USERPROFILE 'Documents') 'projects') 'eu-trade-dependency'
$raw = Join-Path $repoDir 'raw'
New-Item -ItemType Directory -Path $raw -Force | Out-Null

$product = '85051110'
$base   = 'https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/'
$period = '?startPeriod=2010&endPeriod=2024&format=SDMX-CSV'

$urlVal = $base + 'A...' + $product + '.1.VALUE_IN_EUROS' + $period
$urlQty = $base + 'A...' + $product + '.1.QUANTITY_IN_100KG' + $period

$outVal = Join-Path $raw ('magnets_' + $product + '_value.csv')
$outQty = Join-Path $raw ('magnets_' + $product + '_qty.csv')

Invoke-WebRequest -Uri $urlVal -OutFile $outVal -UseBasicParsing -Headers @{ 'Accept-Encoding' = 'identity' }
Write-Output ('Value file:    ' + (Get-Item $outVal).Length + ' bytes')

Invoke-WebRequest -Uri $urlQty -OutFile $outQty -UseBasicParsing -Headers @{ 'Accept-Encoding' = 'identity' }
Write-Output ('Quantity file: ' + (Get-Item $outQty).Length + ' bytes')

Write-Output 'Done. Now run: Rscript comext-magnet-dependency-demo.R'

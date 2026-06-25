<#  download_flows.ps1
    Real bilateral trade flows for each material, from UN Comtrade (public preview API).
    For each material we pull the real exports (flowCode=X) of its HS6 product from the
    major producers/refiners we already know, to ALL partners, for one year. We keep the
    top destinations per exporter. Output: out/flows.json = { year, centroids{ISO2:[lat,lng]},
    materials:{ label:[ {from,to,value} ] } } consumed by the map in index.html.

    Honest scope: this is the traded PRODUCT (mostly the refined good we already track),
    exporter -> customer. Background "where it's mined" comes from the USGS choropleth.
#>
param(
  [int]$Year = 2023,
  [int]$TopDest = 8,        # keep this many destinations per exporter
  [string[]]$Only = @(),   # limit to these material labels (testing); empty = all
  [double]$Throttle = 1.4  # seconds between API calls
)
$ProgressPreference='SilentlyContinue'
$root = $PSScriptRoot
$data = Get-Content "$root\out\data.json" -Raw | ConvertFrom-Json

Write-Host "Loading Comtrade code reference..."
$rep = Invoke-RestMethod 'https://comtradeapi.un.org/files/v1/app/reference/Reporters.json' -TimeoutSec 40
$m49toIso=@{}; $isoToM49=@{}
foreach($a in $rep.results){ if($a.reporterCodeIsoAlpha2 -and $a.reporterCodeIsoAlpha2 -ne 'null'){ $m49toIso[[string]$a.id]=$a.reporterCodeIsoAlpha2; $isoToM49[$a.reporterCodeIsoAlpha2]=[string]$a.id } }

Write-Host "Loading country centroids..."
$cenCsv = Invoke-RestMethod 'https://raw.githubusercontent.com/google/dspl/master/samples/google/canonical/countries.csv' -TimeoutSec 40
$centroid=@{}; $cName=@{}
foreach($line in ($cenCsv -split "`n" | Select-Object -Skip 1)){
  $p = $line.Trim() -split ','
  if($p.Count -ge 4 -and $p[0]){ $centroid[$p[0]] = @([double]$p[1], [double]$p[2]); $cName[$p[0]] = (($p[3..($p.Count-1)] -join ',').Trim('"')) }  # ISO2 -> [lat,lng], name
}
"  centroids: $($centroid.Count) countries"

function Get-Flows($m49, $hs6){
  $u = "https://comtradeapi.un.org/public/v1/preview/C/A/HS?reporterCode=$m49&period=$Year&partnerCode=&cmdCode=$hs6&flowCode=X"
  for($try=0; $try -lt 4; $try++){
    try { $r = Invoke-RestMethod -Uri $u -TimeoutSec 45; return $r.data }
    catch {
      $code = $_.Exception.Response.StatusCode.value__
      if($code -eq 429){ Start-Sleep (3 + $try*3); continue }
      return @()
    }
  }
  return @()
}

$out = [ordered]@{}
$usedIso = [System.Collections.Generic.HashSet[string]]::new()
$mats = $data.materials
if($Only.Count){ $mats = $mats | Where-Object { $_.label -in $Only } }
$calls=0

foreach($m in $mats){
  $inside = ([regex]::Match($m.title,'\(([^)]*)\)')).Groups[1].Value
  $code = ($inside -replace '\D','')         # "(CN 8505 11 10)" -> "85051110"
  if($code.Length -lt 6){ continue }
  $hs6 = $code.Substring(0,6)
  # exporters to pull: refined country + top-2 mine + top EU origin (dedup), as ISO2 we can resolve
  $exp = [System.Collections.Generic.List[string]]::new()
  if($m.refined){ foreach($x in $m.refined){ [void]$exp.Add($x.c) } }
  if($m.mined){ foreach($x in ($m.mined | Select-Object -First 2)){ [void]$exp.Add($x.c) } }
  if($m.top_partner){ [void]$exp.Add($m.top_partner) }
  $exp = $exp | Select-Object -Unique | Where-Object { $isoToM49.ContainsKey($_) }
  $flows=@{}
  foreach($iso in $exp){
    $m49=$isoToM49[$iso]
    Start-Sleep $Throttle; $calls++
    $rows = Get-Flows $m49 $hs6
    $dest = $rows | Where-Object { $_.partnerCode -ne 0 -and $_.primaryValue -gt 0 -and $m49toIso.ContainsKey([string]$_.partnerCode) } |
            Sort-Object primaryValue -Descending | Select-Object -First $TopDest
    foreach($d in $dest){
      $toIso=$m49toIso[[string]$d.partnerCode]
      if($toIso -eq $iso){ continue }
      $k="$iso>$toIso"; $flows[$k]=[double]$d.primaryValue
      [void]$usedIso.Add($iso); [void]$usedIso.Add($toIso)
    }
  }
  $list=@(); foreach($k in $flows.Keys){ $ab=$k -split '>'; $list += [ordered]@{ from=$ab[0]; to=$ab[1]; value=[math]::Round($flows[$k]) } }
  $out[$m.label] = @($list | Sort-Object { -$_.value })
  "{0,-12} hs6={1} exporters={2} flows={3}" -f $m.label, $hs6, ($exp -join '/'), $list.Count | Write-Host
}

$cenUsed=[ordered]@{}; $nameUsed=[ordered]@{}
foreach($iso in ($usedIso | Sort-Object)){ if($centroid.ContainsKey($iso)){ $cenUsed[$iso]=$centroid[$iso]; $nameUsed[$iso]=$cName[$iso] } }
$result=[ordered]@{ year=$Year; centroids=$cenUsed; names=$nameUsed; iso=$m49toIso; materials=$out }
$result | ConvertTo-Json -Depth 8 -Compress | Out-File "$root\out\flows.json" -Encoding utf8
"`nAPI calls: $calls. Wrote out/flows.json ($([math]::Round((Get-Item "$root\out\flows.json").Length/1KB)) KB, $($cenUsed.Count) centroids)."
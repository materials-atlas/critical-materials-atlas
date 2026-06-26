<#  build_flows_years.ps1
    Multi-year version of build_baci_flows.ps1. Builds out/flows_<YEAR>.json for a range of years
    from ONE BACI nomenclature (default HS17, which spans 2017-2023) so the time series is internally
    consistent — no cross-vintage stitching. One crosswalk only: hafnium's HS2022 code 811231 did not
    exist before HS2022, so it folds into the broad 811292 group (gallium/germanium/hafnium/indium/
    niobium/rhenium/vanadium) — which gallium/germanium already are, so the effect on them is negligible.
#>
param([int[]]$Years=@(2018,2019,2020,2021,2022,2023,2024),[int]$TopPerSide=6,[string]$Ver='V202601',[string]$Hs='HS17')
$ProgressPreference='SilentlyContinue'
$root=$PSScriptRoot
$ccCsv="$root\raw\baci\country_codes_${Ver}.csv"

# HS6 -> material label(s), from data.json titles (HS22 codes), then crosswalk to $Hs
$data = Get-Content "$root\out\data.json" -Raw | ConvertFrom-Json
$code2labels=@{}
foreach($m in $data.materials){ $c=(([regex]::Match($m.title,'\(([^)]*)\)')).Groups[1].Value -replace '\D',''); if($c.Length -ge 6){ $h=$c.Substring(0,6); if(-not $code2labels.ContainsKey($h)){ $code2labels[$h]=@() }; $code2labels[$h]+=$m.label } }
if($Hs -eq 'HS17' -and $code2labels.ContainsKey('811231')){           # hafnium: no distinct pre-HS2022 code -> broad 811292 group
  if(-not $code2labels.ContainsKey('811292')){ $code2labels['811292']=@() }
  $code2labels['811292']+=$code2labels['811231']; $code2labels.Remove('811231') }
$codes=New-Object 'System.Collections.Generic.HashSet[string]'; $code2labels.Keys | ForEach-Object { [void]$codes.Add($_) }

# country code -> ISO2 (load once)
$cc=Import-Csv $ccCsv
$num2iso=@{}; foreach($r in $cc){ if($r.country_iso2 -and $r.country_iso2 -ne 'NA'){ $num2iso[$r.country_code]=$r.country_iso2 } }
$ccName=@{}; foreach($r in $cc){ if($r.country_iso2){ $ccName[$r.country_iso2]=$r.country_name } }
$isoMap=[ordered]@{}; foreach($r in $cc){ if($r.country_iso2 -and $r.country_iso2 -ne 'NA'){ $isoMap[$r.country_code]=$r.country_iso2 } }

# centroids + names (fetch once)
$cenCsv=Invoke-RestMethod 'https://raw.githubusercontent.com/google/dspl/master/samples/google/canonical/countries.csv' -TimeoutSec 40
$cen=@{}; $nm=@{}
foreach($l in ($cenCsv -split "`n" | Select-Object -Skip 1)){ $q=$l.Trim() -split ','; if($q.Count -ge 4 -and $q[0]){ $cen[$q[0]]=@([double]$q[1],[double]$q[2]); $nm[$q[0]]=(($q[3..($q.Count-1)] -join ',').Trim('"')) } }

foreach($Year in $Years){
  $baci="$root\raw\baci\BACI_${Hs}_Y${Year}_${Ver}.csv"
  if(-not (Test-Path $baci)){ Write-Host "skip $Year (no $baci)"; continue }
  $edges=@{}
  $sr=New-Object System.IO.StreamReader($baci); [void]$sr.ReadLine(); $n=0
  while($null -ne ($line=$sr.ReadLine())){
    $n++; $p=$line.Split(',')
    if(-not $codes.Contains($p[3])){ continue }
    $from=$num2iso[$p[1]]; $to=$num2iso[$p[2]]
    if(-not $from -or -not $to -or $from -eq $to){ continue }
    $val=[double]$p[4]*1000.0; if($val -le 0){ continue }
    foreach($lab in $code2labels[$p[3]]){
      if(-not $edges.ContainsKey($lab)){ $edges[$lab]=@{} }
      $key="$from>$to"
      if($edges[$lab].ContainsKey($key)){ $edges[$lab][$key]=$edges[$lab][$key]+$val } else { $edges[$lab][$key]=$val }
    }
  }
  $sr.Close()
  $used=New-Object 'System.Collections.Generic.HashSet[string]'
  $materials=[ordered]@{}
  foreach($lab in $edges.Keys){
    $list=foreach($k in $edges[$lab].Keys){ $ab=$k.Split('>'); [pscustomobject]@{from=$ab[0];to=$ab[1];value=$edges[$lab][$k]} }
    $keep=@{}
    $list | Group-Object to   | ForEach-Object { $_.Group | Sort-Object value -Descending | Select-Object -First $TopPerSide | ForEach-Object { $keep["$($_.from)>$($_.to)"]=$_.value } }
    $list | Group-Object from | ForEach-Object { $_.Group | Sort-Object value -Descending | Select-Object -First $TopPerSide | ForEach-Object { $keep["$($_.from)>$($_.to)"]=$_.value } }
    $arr=foreach($k in $keep.Keys){ $ab=$k.Split('>'); [void]$used.Add($ab[0]); [void]$used.Add($ab[1]); [ordered]@{from=$ab[0];to=$ab[1];value=[math]::Round($keep[$k])} }
    $materials[$lab]=@($arr | Sort-Object { -$_.value })
  }
  $centroids=[ordered]@{}; $names=[ordered]@{}
  foreach($iso in ($used | Sort-Object)){ if($cen.ContainsKey($iso)){ $centroids[$iso]=$cen[$iso]; $nv=if($nm[$iso]){$nm[$iso]}elseif($ccName[$iso]){$ccName[$iso]}else{$iso}; $names[$iso]=$nv } }
  $out=[ordered]@{ year=$Year; source="UN Comtrade (primary) via CEPII BACI $Hs $Ver"; centroids=$centroids; names=$names; iso=$isoMap; materials=$materials }
  [System.IO.File]::WriteAllText("$root\out\flows_${Year}.json", ($out | ConvertTo-Json -Depth 8 -Compress), (New-Object System.Text.UTF8Encoding $false))
  $tot=0; $materials.Values | ForEach-Object { $tot+=$_.Count }
  Write-Host ("Year $Year : rows=$n materials=$($materials.Count) flows=$tot countries=$($centroids.Count) size=" + [math]::Round((Get-Item "$root\out\flows_${Year}.json").Length/1KB) + "KB")
}
Write-Host "DONE."

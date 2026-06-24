<#  build_baci_flows.ps1
    Rebuild out/flows.json from CEPII BACI (complete bilateral trade, all countries, both
    directions). BACI is the reconciled form of the PRIMARY source, UN Comtrade.
    Streams the yearly BACI csv (t,i,j,k,v,q), filters to our 32 material HS6 codes, maps
    BACI numeric country codes -> ISO2, and keeps each material's top suppliers-per-importer
    and top customers-per-exporter (so every country is covered while the file stays small).
#>
param([int]$Year=2023,[int]$TopPerSide=6,[string]$Ver='V202501')
$ProgressPreference='SilentlyContinue'
$root='eu_trade_dependency'
$baci="$root\raw\baci\BACI_HS22_Y${Year}_${Ver}.csv"
$ccCsv="$root\raw\baci\country_codes_${Ver}.csv"

# HS6 -> material label(s)
$data = Get-Content "$root\out\data.json" -Raw | ConvertFrom-Json
$code2labels=@{}
foreach($m in $data.materials){ $c=(([regex]::Match($m.title,'\(([^)]*)\)')).Groups[1].Value -replace '\D',''); if($c.Length -ge 6){ $h=$c.Substring(0,6); if(-not $code2labels.ContainsKey($h)){ $code2labels[$h]=@() }; $code2labels[$h]+=$m.label } }
$codes=New-Object 'System.Collections.Generic.HashSet[string]'; $code2labels.Keys | ForEach-Object { [void]$codes.Add($_) }

# BACI country_code -> ISO2
$cc=Import-Csv $ccCsv
$num2iso=@{}; foreach($r in $cc){ if($r.country_iso2 -and $r.country_iso2 -ne 'NA'){ $num2iso[$r.country_code]=$r.country_iso2 } }

# stream + accumulate per-label edge value sums (USD)
$edges=@{}
$sr=New-Object System.IO.StreamReader($baci)
[void]$sr.ReadLine()
$n=0
while($null -ne ($line=$sr.ReadLine())){
  $n++
  $p=$line.Split(',')
  if(-not $codes.Contains($p[3])){ continue }
  $from=$num2iso[$p[1]]; $to=$num2iso[$p[2]]
  if(-not $from -or -not $to -or $from -eq $to){ continue }
  $val=[double]$p[4]*1000.0
  if($val -le 0){ continue }
  foreach($lab in $code2labels[$p[3]]){
    if(-not $edges.ContainsKey($lab)){ $edges[$lab]=@{} }
    $key="$from>$to"
    if($edges[$lab].ContainsKey($key)){ $edges[$lab][$key]=$edges[$lab][$key]+$val } else { $edges[$lab][$key]=$val }
  }
}
$sr.Close()
Write-Host "scanned $n rows"

# per material: top suppliers per importer + top customers per exporter (coverage + cap)
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

# centroids + names for used ISO2 (lat/lng from Google canonical countries)
$cenCsv=Invoke-RestMethod 'https://raw.githubusercontent.com/google/dspl/master/samples/google/canonical/countries.csv' -TimeoutSec 40
$cen=@{}; $nm=@{}
foreach($l in ($cenCsv -split "`n" | Select-Object -Skip 1)){ $q=$l.Trim() -split ','; if($q.Count -ge 4 -and $q[0]){ $cen[$q[0]]=@([double]$q[1],[double]$q[2]); $nm[$q[0]]=(($q[3..($q.Count-1)] -join ',').Trim('"')) } }
$ccName=@{}; foreach($r in $cc){ if($r.country_iso2){ $ccName[$r.country_iso2]=$r.country_name } }
$centroids=[ordered]@{}; $names=[ordered]@{}
foreach($iso in ($used | Sort-Object)){ if($cen.ContainsKey($iso)){ $centroids[$iso]=$cen[$iso]; $nv=if($nm[$iso]){$nm[$iso]}elseif($ccName[$iso]){$ccName[$iso]}else{$iso}; $names[$iso]=$nv } }
$isoMap=[ordered]@{}; foreach($r in $cc){ if($r.country_iso2 -and $r.country_iso2 -ne 'NA'){ $isoMap[$r.country_code]=$r.country_iso2 } }

$out=[ordered]@{ year=$Year; source="UN Comtrade (primary) via CEPII BACI HS22 $Ver"; centroids=$centroids; names=$names; iso=$isoMap; materials=$materials }
$out | ConvertTo-Json -Depth 8 -Compress | Out-File "$root\out\flows.json" -Encoding utf8
$tot=0; $materials.Values | ForEach-Object { $tot+=$_.Count }
Write-Host ("DONE. materials=$($materials.Count) flows=$tot countries=$($centroids.Count) size=" + [math]::Round((Get-Item "$root\out\flows.json").Length/1KB) + "KB")
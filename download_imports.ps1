<#  download_imports.ps1
    Complete INBOUND flows: for a curated set of major importer countries, pull each one's
    real imports (flowCode=M) of every material's HS6 from ALL partners, and MERGE the
    resulting origin->importer edges into out/flows.json. This makes the "into: <country>"
    scope complete for these importers (vs the export-only approximation).

    Adds out/flows.json -> importers:[ISO2 we have complete inbound for]; merges edges into
    materials{label:[{from,to,value}]} (deduped, keeping the larger value). Resilient:
    retry+backoff on timeout/429 so it survives Comtrade's anonymous-tier throttling.
#>
param([Parameter(Mandatory=$true)][string]$Key,[int]$Year=2023,[int]$TopPartner=8,[double]$Throttle=5,[int]$ChunkSize=40)
$ProgressPreference='SilentlyContinue'
$root='eu_trade_dependency'
$f = Get-Content "$root\out\flows.json" -Raw | ConvertFrom-Json
$num2iso=@{}; foreach($p in $f.iso.PSObject.Properties){ $num2iso[$p.Name]=$p.Value }

# curated importer countries (ISO2 -> M49 numeric)
$IMP=[ordered]@{ DE=276;FR=250;IT=380;NL=528;BE=56;ES=724;PL=616;SE=752;AT=40;CZ=203;
  US=842;GB=826;CN=156;JP=392;KR=410;IN=356;TW=490;TR=792;CA=124;MX=484;BR=76;CH=756;AU=36;ZA=710;SG=702;TH=764;NO=578;FI=246 }

# HS6 -> material labels (a code can map to several materials)
$data = Get-Content "$root\out\data.json" -Raw | ConvertFrom-Json
$code2labels=@{}
foreach($m in $data.materials){ $inside=([regex]::Match($m.title,'\(([^)]*)\)')).Groups[1].Value; $c=($inside -replace '\D',''); if($c.Length -ge 6){ $h=$c.Substring(0,6); if(-not $code2labels.ContainsKey($h)){ $code2labels[$h]=@() }; $code2labels[$h]+=$m.label } }
$codes=@($code2labels.Keys)

function Get-Imp($m49,$codeList){
  $cc=$codeList -join ','
  $u="https://comtradeapi.un.org/data/v1/get/C/A/HS?reporterCode=$m49&period=$Year&cmdCode=$cc&flowCode=M&partner2Code=0&motCode=0&customsCode=C00"
  for($t=0;$t -lt 5;$t++){ try{ $r=Invoke-RestMethod -Uri $u -Headers @{'Ocp-Apim-Subscription-Key'=$Key} -TimeoutSec 90; if($r.data -and @($r.data).Count){ return $r.data } }catch{}; Start-Sleep (10+$t*20) }
  return $null   # null = exception OR soft rate-limit (200 with empty data)
}

$imp=@{}; $calls=0; $fail=0; $consec=0; $abort=$false
foreach($iso in $IMP.Keys){
  if($abort){ break }
  $m49=$IMP[$iso]
  for($i=0;$i -lt $codes.Count;$i+=$ChunkSize){
    $chunk=$codes[$i..([Math]::Min($i+$ChunkSize-1,$codes.Count-1))]
    Start-Sleep $Throttle; $calls++
    $rows=Get-Imp $m49 $chunk
    if($null -eq $rows){ $fail++; $consec++; if($consec -ge 14){ $abort=$true; break }; continue }
    $consec=0
    foreach($hs in $chunk){
      $dest=$rows | Where-Object { ([string]$_.cmdCode) -eq $hs -and $_.partnerCode -ne 0 -and $_.primaryValue -gt 0 -and $num2iso.ContainsKey([string]$_.partnerCode) } |
            Sort-Object primaryValue -Descending | Select-Object -First $TopPartner
      foreach($d in $dest){ $fromIso=$num2iso[[string]$d.partnerCode]; if($fromIso -eq $iso){ continue }
        foreach($lab in $code2labels[$hs]){ if(-not $imp.ContainsKey($lab)){ $imp[$lab]=@{} }
          $k="$fromIso>$iso"; if(-not $imp[$lab].ContainsKey($k) -or $imp[$lab][$k] -lt $d.primaryValue){ $imp[$lab][$k]=[double]$d.primaryValue } } }
    }
  }
  Write-Host "$iso done (calls=$calls fail=$fail)"
}

# top up centroids/names for any new ISO2 endpoints
$used=New-Object System.Collections.Generic.HashSet[string]
foreach($lab in $imp.Keys){ foreach($k in $imp[$lab].Keys){ $ab=$k -split '>'; [void]$used.Add($ab[0]); [void]$used.Add($ab[1]) } }
$cenCsv = Invoke-RestMethod 'https://raw.githubusercontent.com/google/dspl/master/samples/google/canonical/countries.csv' -TimeoutSec 40
$cen=@{}; $nm=@{}
foreach($line in ($cenCsv -split "`n" | Select-Object -Skip 1)){ $p=$line.Trim() -split ','; if($p.Count -ge 4 -and $p[0]){ $cen[$p[0]]=@([double]$p[1],[double]$p[2]); $nm[$p[0]]=(($p[3..($p.Count-1)] -join ',').Trim('"')) } }

$centroids=[ordered]@{}; foreach($pp in $f.centroids.PSObject.Properties){ $centroids[$pp.Name]=$pp.Value }
$names=[ordered]@{};     foreach($pp in $f.names.PSObject.Properties){ $names[$pp.Name]=$pp.Value }
foreach($iso in $used){ if(-not $centroids.Contains($iso) -and $cen.ContainsKey($iso)){ $centroids[$iso]=$cen[$iso]; $names[$iso]=$nm[$iso] } }

$materials=[ordered]@{}
foreach($pp in $f.materials.PSObject.Properties){ $arr=New-Object System.Collections.ArrayList
  foreach($fl in $pp.Value){ [void]$arr.Add([ordered]@{from=$fl.from;to=$fl.to;value=$fl.value}) }
  $materials[$pp.Name]=$arr }
foreach($lab in $imp.Keys){
  if(-not $materials.Contains($lab)){ $materials[$lab]=New-Object System.Collections.ArrayList }
  $existing=@{}; foreach($fl in $materials[$lab]){ $existing["$($fl.from)>$($fl.to)"]=$true }
  foreach($k in $imp[$lab].Keys){ if(-not $existing.ContainsKey($k)){ $ab=$k -split '>'; [void]$materials[$lab].Add([ordered]@{from=$ab[0];to=$ab[1];value=[math]::Round($imp[$lab][$k])}) } } }

$importersDone=New-Object System.Collections.Generic.HashSet[string]
foreach($lab in $imp.Keys){ foreach($k in $imp[$lab].Keys){ [void]$importersDone.Add(($k -split '>')[1]) } }
if($f.importers){ foreach($x in $f.importers){ [void]$importersDone.Add($x) } }   # accumulate across runs
if($importersDone.Count -eq 0){ "ABORTED - Comtrade throttled, no data fetched. flows.json left unchanged. Rerun later."; return }
$out=[ordered]@{ year=$f.year; centroids=$centroids; names=$names; iso=$f.iso; importers=@($importersDone); materials=$materials }
$out | ConvertTo-Json -Depth 8 -Compress | Out-File "$root\out\flows.json" -Encoding utf8
"DONE. calls=$calls fail=$fail. importers complete=$($importersDone.Count)/$($IMP.Count). flows.json $([math]::Round((Get-Item "$root\out\flows.json").Length/1KB)) KB."
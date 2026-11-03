# FINDING 181 — investigation, diagnosis and remedy — codex — 2026-08-28

## 1. Verdict

The root implementation mechanism is **not identified**, but the retained files now localise it and exclude a previously live branch. For `it__IT.MidClim.SFH-TH.07.Gen.ReEx.001.001__f100`, three content-identical expanded inputs produce different sizing traces before the annual run, then different values in the engine-written `eplusout.eso` at the first reported run-period hour; within each replicate the 8,760 ESO heating records sum exactly to the value parsed from the 8,760-row ReadVarsESO CSV. Thus H1 (ReadVarsESO, truncation, or the parent reading a live CSV) is excluded for this discriminator, H4 is excluded for its model content, and the phenomenon is inside EnergyPlus no later than sizing/initialisation. H2 and H3 remain observationally indistinguishable: this can be sensitive dependence of the unenclosed equivalent-envelope heat balance, an EnergyPlus 23.1 defect such as uninitialised state, or both. The retained failures independently show two real EnergyPlus fatal paths, not harness-assigned or timeout failures. I therefore do **not** claim that `FixViewFactors`, windows, autosizing, or any implementation detail is the root cause.

## 2. Investigation — what I read

1. Prompt and required context: `docs/docs_ACTIVE/europeanLocations/debugs/DONE/PROMPT_finding181_investigation_2026-08-28.md`; `STATE_european_locations_v2.md` §3; `implementation/previous/PLAN_finding181-stability-2026-08-28.md` §7; `implementation/PLAN_deu27-timestep12-rerun-2026-08-28.md` §5 and execution notes; and `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`, especially the FINDING 181 family near lines 1665–1669. I did not open the pre-existing Gemini report whose filename appeared in `git status`.
2. Runner and model code: `openubem/campaign/eu_cell_runner.py`, including weather verification, IDF construction, CSV extraction, invocation and status logic; `openubem/semantic/european_schedules.py:88-123`; `openubem/idf/european_box.py:46-62,177-375`; and `scripts/campaign/run_eu_certified_rerun.py:1-172`.
3. Tables: all 1,530 rows of `docs/docs_ACTIVE/europeanLocations/outputs/deu27_rerun_cells.csv`, grouped by cell and replicate; and the selected cell entry in `openubem/data/campaign/eu_campaign_cell_spec_v1.1.json`. I did not inspect the unavailable ten-replicate tables from the other repository.
4. Retained run artifacts: for the principal Italian discriminator, all three `eplusout.csv`, `.eso`, `.expidf`, `.err`, `.end`, `.eio`, `epluszsz.csv`, `.audit`, `.dbg`, `.shd`, `.bnd`, and `.mtd` files, plus all three emitted schedule CSVs and the pinned EPW. For failure classification I opened all 156 failed `.err` and `.end` pairs. For object-count screening I opened the rep1 `.expidf` for all 395 attempted cells. I also inspected artifact inventories for the five named cells used during selection and the three `.err`/`.end` pairs for `es__ES.ME.AB.02.Gen.ReEx.001.001__f015`.

<details><summary>Read-only commands, verbatim (PowerShell; all ran from the repository root)</summary>

```powershell
Get-Content -LiteralPath 'C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\europeanLocations\debugs\DONE\PROMPT_finding181_investigation_2026-08-28.md' -Raw
```

```powershell
rg -n "FINDING 181|Finding 181|T01|T02|T03|T04|T05|timestep|non-determin|stabil|open item" docs/docs_ACTIVE/europeanLocations/STATE_european_locations_v2.md docs/docs_ACTIVE/europeanLocations/implementation/previous/PLAN_finding181-stability-2026-08-28.md docs/docs_ACTIVE/europeanLocations/implementation/PLAN_deu27-timestep12-rerun-2026-08-28.md
rg -n "def run_campaign_cell|def _parse_heating|def _energyplus_exe|subprocess.run|ENGINE_FAILED|fatal_count|heating_kwh|Schedule:File|EquivalentEnvelope|FixViewFactors|inside surface heat balance|converg|ReadVarsESO|eplusout.csv" openubem/campaign/eu_cell_runner.py openubem/semantic/european_schedules.py openubem/idf/european_box.py docs/docs_EXPLANATION/OpenUBEM_debug_References.md
rg -n "ProcessPoolExecutor|replicate|run_root|workers|run_campaign_cell" scripts/campaign/run_eu_certified_rerun.py
```

```powershell
$targets = @(
  @{Path='docs/docs_ACTIVE/europeanLocations/STATE_european_locations_v2.md'; Start=115; End=240},
  @{Path='docs/docs_ACTIVE/europeanLocations/implementation/previous/PLAN_finding181-stability-2026-08-28.md'; Start=211; End=291},
  @{Path='docs/docs_ACTIVE/europeanLocations/implementation/PLAN_deu27-timestep12-rerun-2026-08-28.md'; Start=40; End=175},
  @{Path='docs/docs_EXPLANATION/OpenUBEM_debug_References.md'; Start=1658; End=1674},
  @{Path='openubem/campaign/eu_cell_runner.py'; Start=390; End=630},
  @{Path='openubem/semantic/european_schedules.py'; Start=80; End=125},
  @{Path='openubem/idf/european_box.py'; Start=40; End=70},
  @{Path='openubem/idf/european_box.py'; Start=170; End=380},
  @{Path='scripts/campaign/run_eu_certified_rerun.py'; Start=1; End=175}
)
foreach ($target in $targets) {
  $lines = Get-Content -LiteralPath $target.Path
  for ($n = $target.Start; $n -le [Math]::Min($target.End, $lines.Count); $n++) {
    '{0}:{1}:{2}' -f $target.Path, $n, $lines[$n-1]
  }
}
```

```powershell
$csvPath = 'docs/docs_ACTIVE/europeanLocations/outputs/deu27_rerun_cells.csv'
$rows = Import-Csv -LiteralPath $csvPath
$attempted = $rows | Where-Object { $_.class -eq 'ATTEMPTED' }
$groups = $attempted | Group-Object cell_id
$statusMixed = $groups | Where-Object { ($_.Group.completed | Sort-Object -Unique).Count -gt 1 }
$heatingMixed = $groups | Where-Object {
  $values = $_.Group | Where-Object { $_.completed -eq 'True' -and $_.heating_kwh -notin @('', 'None') } | ForEach-Object heating_kwh | Sort-Object -Unique
  $values.Count -gt 1
}
"rows=$($rows.Count) attempted=$($attempted.Count) cells=$($groups.Count) status_mixed=$($statusMixed.Count) heating_mixed=$($heatingMixed.Count)"
'STATUS_MIXED_SAMPLE'
$statusMixed | Select-Object -First 12 | ForEach-Object {
  $detail = $_.Group | Sort-Object {[int]$_.replicate} | ForEach-Object { "rep$($_.replicate):completed=$($_.completed),status=$($_.completion_status),rc=$($_.return_code),sev=$($_.severe_count),fatal=$($_.fatal_count),heat=$($_.heating_kwh),runtime=$($_.runtime_s),error=$($_.error)" }
  "$($_.Name) :: $($detail -join ' | ')"
}
'HEATING_MIXED_SAMPLE'
$heatingMixed | Select-Object -First 12 | ForEach-Object {
  $detail = $_.Group | Sort-Object {[int]$_.replicate} | ForEach-Object { "rep$($_.replicate):completed=$($_.completed),heat=$($_.heating_kwh),runtime=$($_.runtime_s)" }
  "$($_.Name) :: $($detail -join ' | ')"
}
'ERROR_COUNTS'
$attempted | Group-Object error | Sort-Object Count -Descending | ForEach-Object { "count=$($_.Count) error=$($_.Name)" }
'COMPLETION_COUNTS'
$attempted | Group-Object completion_status,return_code,fatal_count | Sort-Object Count -Descending | ForEach-Object { "count=$($_.Count) key=$($_.Name)" }
```

```powershell
$rows = Import-Csv -LiteralPath 'docs/docs_ACTIVE/europeanLocations/outputs/deu27_rerun_cells.csv'
$ids = @(
  'uk__GB.ENG.AB.03.Gen.ReEx.001.001__f000',
  'uk__GB.ENG.AB.04.Gen.ReEx.001.001__f050',
  'it__IT.MidClim.SFH.07.Gen.ReEx.001.001__f000',
  'es__ES.ME.AB.02.Gen.ReEx.001.001__f015',
  'es__ES.ME.AB.02.Gen.ReEx.001.001__f050'
)
$rows | Where-Object { $_.cell_id -in $ids } | Sort-Object cell_id,{[int]$_.replicate} | Format-Table cell_id,replicate,completed,completion_status,return_code,severe_count,fatal_count,heating_kwh,runtime_s,marker_psy,marker_inside_hb,marker_calchb,error -AutoSize
$root = 'openubem/outputs/eu_certified_rerun_2026-08-28'
foreach ($id in $ids) {
  foreach ($rep in 1..3) {
    $dir = Join-Path $root "rep$rep/$id"
    $files = Get-ChildItem -LiteralPath $dir -File -ErrorAction SilentlyContinue
    "$id rep$rep :: $($files.Name -join ', ')"
  }
}
```

```powershell
$rows = Import-Csv -LiteralPath 'docs/docs_ACTIVE/europeanLocations/outputs/deu27_rerun_cells.csv' | Where-Object { $_.class -eq 'ATTEMPTED' }
$candidates = foreach ($group in ($rows | Group-Object cell_id)) {
  $completed = @($group.Group | Where-Object { $_.completed -eq 'True' -and $_.severe_count -eq '0' -and $_.fatal_count -eq '0' -and $_.marker_psy -eq 'False' -and $_.marker_inside_hb -eq 'False' -and $_.marker_calchb -eq 'False' })
  $values = @($completed | ForEach-Object { [double]$_.heating_kwh } | Sort-Object -Unique)
  if ($completed.Count -eq 3 -and $values.Count -gt 1) {
    $min = ($values | Measure-Object -Minimum).Minimum
    $max = ($values | Measure-Object -Maximum).Maximum
    [pscustomobject]@{cell_id=$group.Name; distinct=$values.Count; min=$min; max=$max; rel_pct=(100*($max-$min)/$min); values=($values -join ',')}
  }
}
$candidates | Sort-Object rel_pct -Descending | Select-Object -First 20 | Format-Table -AutoSize
"count=$(@($candidates).Count)"
```

```powershell
$cell = 'it__IT.MidClim.SFH-TH.07.Gen.ReEx.001.001__f100'
$root = 'openubem/outputs/eu_certified_rerun_2026-08-28'
foreach ($rep in 1..3) {
  $dir = Join-Path $root "rep$rep/$cell"
  "rep$rep"
  Get-Item -LiteralPath (Join-Path $dir 'eplusout.csv'),(Join-Path $dir 'eplusout.eso'),(Join-Path $dir 'eplusout.expidf'),(Join-Path $dir 'eplusout.err'),(Join-Path $dir 'eplusout.end') | Select-Object Name,Length
  Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $dir 'eplusout.csv'),(Join-Path $dir 'eplusout.eso'),(Join-Path $dir 'eplusout.expidf') | Select-Object Path,Hash
}
$csv = Join-Path $root "rep1/$cell/eplusout.csv"
Get-Content -LiteralPath $csv -TotalCount 3
$eso = Join-Path $root "rep1/$cell/eplusout.eso"
Get-Content -LiteralPath $eso -TotalCount 35
```

```powershell
$cell = 'it__IT.MidClim.SFH-TH.07.Gen.ReEx.001.001__f100'
$root = 'openubem/outputs/eu_certified_rerun_2026-08-28'
$csvSeries = @{}
$esoSeries = @{}
foreach ($rep in 1..3) {
  $dir = Join-Path $root "rep$rep/$cell"
  $csvPath = Join-Path $dir 'eplusout.csv'
  $csvRows = @(Import-Csv -LiteralPath $csvPath)
  $heatingColumn = @($csvRows[0].PSObject.Properties.Name | Where-Object { $_.ToLowerInvariant().Contains('zone ideal loads zone total heating energy') -and $_.ToLowerInvariant().Contains('[j]') -and $_.ToLowerInvariant().Contains('(hourly)') })
  $csvSeries[$rep] = @($csvRows | ForEach-Object { [double]$_.$($heatingColumn[0]) })
  $esoPath = Join-Path $dir 'eplusout.eso'
  $inData = $false
  $currentTime = $null
  $esoValues = [System.Collections.Generic.List[double]]::new()
  $esoTimes = [System.Collections.Generic.List[string]]::new()
  foreach ($line in [System.IO.File]::ReadLines((Resolve-Path -LiteralPath $esoPath))) {
    if ($line -eq 'End of Data Dictionary') { $inData = $true; continue }
    if (-not $inData) { continue }
    if ($line.StartsWith('2,')) { $currentTime = $line; continue }
    if ($line.StartsWith('556,')) {
      $esoValues.Add([double]::Parse($line.Substring(4),[Globalization.CultureInfo]::InvariantCulture))
      $esoTimes.Add($currentTime)
    }
  }
  $esoSeries[$rep] = @($esoValues)
  $sumCsv = ($csvSeries[$rep] | Measure-Object -Sum).Sum / 3600000
  $sumEso = ($esoSeries[$rep] | Measure-Object -Sum).Sum / 3600000
  "rep$rep csv_rows=$($csvRows.Count) heating_columns=$($heatingColumn.Count) eso_records=$($esoValues.Count) csv_kwh=$sumCsv eso_kwh=$sumEso"
}
$firstCsv = 0..($csvSeries[1].Count-1) | Where-Object { $csvSeries[1][$_] -ne $csvSeries[2][$_] -or $csvSeries[1][$_] -ne $csvSeries[3][$_] } | Select-Object -First 1
$firstEso = 0..($esoSeries[1].Count-1) | Where-Object { $esoSeries[1][$_] -ne $esoSeries[2][$_] -or $esoSeries[1][$_] -ne $esoSeries[3][$_] } | Select-Object -First 1
"first_csv_difference_zero_based=$firstCsv values_J=$($csvSeries[1][$firstCsv]),$($csvSeries[2][$firstCsv]),$($csvSeries[3][$firstCsv])"
"first_eso_difference_zero_based=$firstEso values_J=$($esoSeries[1][$firstEso]),$($esoSeries[2][$firstEso]),$($esoSeries[3][$firstEso])"
$firstCsvRows = @((Import-Csv -LiteralPath (Join-Path $root "rep1/$cell/eplusout.csv")),(Import-Csv -LiteralPath (Join-Path $root "rep2/$cell/eplusout.csv")),(Import-Csv -LiteralPath (Join-Path $root "rep3/$cell/eplusout.csv")))
"csv_timestamp=$($firstCsvRows[0][$firstCsv].'Date/Time')"
"eso_timestamp_record=$($esoTimes[$firstEso])"
```

```powershell
$cell = 'it__IT.MidClim.SFH-TH.07.Gen.ReEx.001.001__f100'
$root = 'openubem/outputs/eu_certified_rerun_2026-08-28'
foreach ($rep in 1..3) {
  $dir = Join-Path $root "rep$rep/$cell"
  "rep$rep"
  foreach ($name in 'eplusout.csv','eplusout.eso','eplusout.expidf','eplusout.err','eplusout.end','eplusout.eio') {
    $item = Get-Item -LiteralPath (Join-Path $dir $name)
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $item.FullName).Hash
    "$name bytes=$($item.Length) sha256=$hash"
  }
  Select-String -LiteralPath (Join-Path $dir 'eplusout.err') -Pattern 'Warmup','Converg','FixViewFactors','Severe','Fatal','Elapsed Time' | ForEach-Object { "err:$($_.LineNumber):$($_.Line)" }
  Get-Content -LiteralPath (Join-Path $dir 'eplusout.end') | ForEach-Object { "end:$($_)" }
  Select-String -LiteralPath (Join-Path $dir 'eplusout.expidf') -Pattern 'Schedule:File','f100.csv','\.epw','Timestep,' | ForEach-Object { "expidf:$($_.LineNumber):$($_.Line)" }
}
```

```powershell
$targets = @(
  @{Path='openubem/campaign/eu_cell_runner.py'; Start=1; End=180},
  @{Path='openubem/campaign/eu_cell_runner.py'; Start=390; End=630},
  @{Path='openubem/idf/european_box.py'; Start=40; End=70},
  @{Path='openubem/idf/european_box.py'; Start=170; End=380},
  @{Path='openubem/semantic/european_schedules.py'; Start=88; End=123}
)
foreach ($target in $targets) {
  $lines = Get-Content -LiteralPath $target.Path
  for ($n = $target.Start; $n -le [Math]::Min($target.End, $lines.Count); $n++) {
    '{0}:{1}:{2}' -f $target.Path, $n, $lines[$n-1]
  }
}
```

```powershell
$targets = @(
  @{Path='openubem/campaign/eu_cell_runner.py'; Start=175; End=215},
  @{Path='openubem/campaign/eu_cell_runner.py'; Start=330; End=405},
  @{Path='openubem/campaign/eu_cell_runner.py'; Start=452; End=630},
  @{Path='openubem/idf/european_box.py'; Start=46; End=62},
  @{Path='openubem/idf/european_box.py'; Start=261; End=325}
)
foreach ($target in $targets) {
  $lines = Get-Content -LiteralPath $target.Path
  for ($n = $target.Start; $n -le $target.End; $n++) {
    '{0}:{1}:{2}' -f $target.Path, $n, $lines[$n-1]
  }
}
```

The next command was read-only but its two in-memory `HashData` calls failed because that method is unavailable in this PowerShell runtime; schedule, EPW, spec and expanded-IDF lines were still read, nothing was written, and the equality test was repeated successfully by the following command.

```powershell
$cellId = 'it__IT.MidClim.SFH-TH.07.Gen.ReEx.001.001__f100'
$root = 'openubem/outputs/eu_certified_rerun_2026-08-28'
$spec = Get-Content -LiteralPath 'openubem/data/campaign/eu_campaign_cell_spec_v1.1.json' -Raw | ConvertFrom-Json
$cell = $spec.cells | Where-Object { $_.cell_id -eq $cellId }
"spec_epw_path=$($cell.epw_path)"
"spec_weather_sha256=$($cell.weather_sha256)"
"spec_idf_path=$($cell.idf_path)"
"spec_gain_csv_path=$($cell.gain_csv_path)"
$epw = Join-Path (Get-Location) $cell.epw_path
"current_epw_sha256=$((Get-FileHash -Algorithm SHA256 -LiteralPath $epw).Hash)"
$normalizedExpidf = @{}
$normalizedErr = @{}
foreach ($rep in 1..3) {
  $expidf = Join-Path $root "rep$rep/$cellId/eplusout.expidf"
  $text = (Get-Content -LiteralPath $expidf -Raw).Replace("\rep$rep\",'\repN\')
  $bytes = [Text.Encoding]::UTF8.GetBytes($text)
  $normalizedExpidf[$rep] = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
  $schedule = Join-Path $root "rep$rep/$($cell.gain_csv_path)"
  "rep$rep normalized_expidf_sha256=$($normalizedExpidf[$rep]) schedule_bytes=$((Get-Item -LiteralPath $schedule).Length) schedule_sha256=$((Get-FileHash -Algorithm SHA256 -LiteralPath $schedule).Hash)"
  $err = Join-Path $root "rep$rep/$cellId/eplusout.err"
  $errText = (Get-Content -LiteralPath $err -Raw) -replace 'Elapsed Time=\d+hr \d+min\s+[\d.]+sec','Elapsed Time=<runtime>'
  $normalizedErr[$rep] = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($errText)))
  "rep$rep normalized_err_sha256=$($normalizedErr[$rep])"
}
"normalized_expidf_unique=$(@($normalizedExpidf.Values | Sort-Object -Unique).Count)"
"normalized_err_unique=$(@($normalizedErr.Values | Sort-Object -Unique).Count)"
foreach ($rep in 1..3) {
  $expidf = Join-Path $root "rep$rep/$cellId/eplusout.expidf"
  Select-String -LiteralPath $expidf -Pattern 'Outside Boundary Condition' | Select-Object -First 12 | ForEach-Object { "rep$rep expidf:$($_.LineNumber):$($_.Line.Trim())" }
}
```

```powershell
$cellId = 'it__IT.MidClim.SFH-TH.07.Gen.ReEx.001.001__f100'
$root = 'openubem/outputs/eu_certified_rerun_2026-08-28'
$normalizedExpidf = @{}
$normalizedErr = @{}
foreach ($rep in 1..3) {
  $expidf = Join-Path $root "rep$rep/$cellId/eplusout.expidf"
  $normalizedExpidf[$rep] = (Get-Content -LiteralPath $expidf) | ForEach-Object { $_ -replace '\\rep[123]\\','\repN\' }
  $err = Join-Path $root "rep$rep/$cellId/eplusout.err"
  $normalizedErr[$rep] = (Get-Content -LiteralPath $err) | ForEach-Object { $_ -replace 'Elapsed Time=\d+hr \d+min\s+[\d.]+sec','Elapsed Time=<runtime>' }
}
"expidf_rep1_vs_rep2_diff_lines=$(@(Compare-Object $normalizedExpidf[1] $normalizedExpidf[2] -SyncWindow 1000).Count)"
"expidf_rep1_vs_rep3_diff_lines=$(@(Compare-Object $normalizedExpidf[1] $normalizedExpidf[3] -SyncWindow 1000).Count)"
"err_rep1_vs_rep2_diff_lines=$(@(Compare-Object $normalizedErr[1] $normalizedErr[2] -SyncWindow 1000).Count)"
"err_rep1_vs_rep3_diff_lines=$(@(Compare-Object $normalizedErr[1] $normalizedErr[3] -SyncWindow 1000).Count)"
```

```powershell
$root = 'openubem/outputs/eu_certified_rerun_2026-08-28'
$failed = Import-Csv -LiteralPath 'docs/docs_ACTIVE/europeanLocations/outputs/deu27_rerun_cells.csv' | Where-Object { $_.class -eq 'ATTEMPTED' -and $_.completed -eq 'False' }
$fatalLines = [System.Collections.Generic.List[string]]::new()
$severeLines = [System.Collections.Generic.List[string]]::new()
$endLines = [System.Collections.Generic.List[string]]::new()
$missing = [System.Collections.Generic.List[string]]::new()
foreach ($row in $failed) {
  $dir = Join-Path $root "rep$($row.replicate)/$($row.cell_id)"
  $errPath = Join-Path $dir 'eplusout.err'
  $endPath = Join-Path $dir 'eplusout.end'
  if (-not (Test-Path -LiteralPath $errPath) -or -not (Test-Path -LiteralPath $endPath)) { $missing.Add("$($row.cell_id)/rep$($row.replicate)"); continue }
  foreach ($line in Get-Content -LiteralPath $errPath) {
    if ($line -match '\*\*\s+Fatal\s+\*\*') { $fatalLines.Add(($line.Trim() -replace '"[^\"]+"','"<object>"' -replace '=[-+]?\d+(\.\d+)?','=<n>')) }
    if ($line -match '\*\*\s+Severe\s+\*\*') { $severeLines.Add(($line.Trim() -replace '"[^\"]+"','"<object>"' -replace '[-+]?\d+(\.\d+)?\s*C','<n> C' -replace '=[-+]?\d+(\.\d+)?','=<n>')) }
  }
  $endLines.Add(((Get-Content -LiteralPath $endPath -Raw).Trim() -replace 'Elapsed Time=.*$','Elapsed Time=<runtime>'))
}
"failed_rows=$($failed.Count) missing_err_or_end=$($missing.Count) fatal_lines=$($fatalLines.Count) severe_lines=$($severeLines.Count)"
'FATAL_GROUPS'
$fatalLines | Group-Object | Sort-Object Count -Descending | ForEach-Object { "count=$($_.Count) line=$($_.Name)" }
'SEVERE_GROUPS'
$severeLines | Group-Object | Sort-Object Count -Descending | ForEach-Object { "count=$($_.Count) line=$($_.Name)" }
'END_GROUPS'
$endLines | Group-Object | Sort-Object Count -Descending | ForEach-Object { "count=$($_.Count) line=$($_.Name)" }
```

```powershell
$root = 'openubem/outputs/eu_certified_rerun_2026-08-28'
$failed = @(Import-Csv -LiteralPath 'docs/docs_ACTIVE/europeanLocations/outputs/deu27_rerun_cells.csv' | Where-Object { $_.class -eq 'ATTEMPTED' -and $_.completed -eq 'False' })
$classed = foreach ($row in $failed) {
  $errPath = Join-Path $root "rep$($row.replicate)/$($row.cell_id)/eplusout.err"
  $text = Get-Content -LiteralPath $errPath -Raw
  $fatalType = if ($text.Contains('Program halted because of convergence error in SolveForWindowTemperatures')) { 'SolveForWindowTemperatures' } elseif ($text.Contains('Program terminates due to preceding condition')) { 'preceding_condition' } else { 'other' }
  [pscustomobject]@{
    fatal_type=$fatalType
    fold=$row.survey_fold
    runtime=[double]$row.runtime_s
    has_inside_hb=$text.Contains('Inside surface heat balance did not converge')
    has_calchb=$text.Contains('CalcHeatBalanceInsideSurf')
    has_temp_bounds=$text.Contains('Temperature (high) out of bounds') -or $text.Contains('Temperature (low) out of bounds')
  }
}
"failed=$($failed.Count) nonzero_return=$(@($failed | Where-Object return_code -ne '0').Count) fatal_count_one=$(@($failed | Where-Object fatal_count -eq '1').Count) csv_missing=$(@($failed | Where-Object heating_kwh -eq 'None').Count) nonblank_driver_error=$(@($failed | Where-Object error -ne '').Count)"
$classed | Group-Object fatal_type | Sort-Object Count -Descending | ForEach-Object {
  $runtimes = @($_.Group.runtime | Sort-Object)
  $median = if ($runtimes.Count % 2) { $runtimes[[int]($runtimes.Count/2)] } else { ($runtimes[$runtimes.Count/2-1]+$runtimes[$runtimes.Count/2])/2 }
  "fatal_type=$($_.Name) count=$($_.Count)/$($failed.Count) runtime_min=$($runtimes[0]) runtime_median=$median runtime_max=$($runtimes[-1]) inside_hb=$(@($_.Group | Where-Object has_inside_hb).Count) calchb=$(@($_.Group | Where-Object has_calchb).Count) temp_bounds=$(@($_.Group | Where-Object has_temp_bounds).Count)"
}
'FOLD_BY_FATAL'
$classed | Group-Object fold,fatal_type | Sort-Object Name | ForEach-Object { "count=$($_.Count) key=$($_.Name)" }
$allAttempted = @(Import-Csv -LiteralPath 'docs/docs_ACTIVE/europeanLocations/outputs/deu27_rerun_cells.csv' | Where-Object class -eq 'ATTEMPTED')
"all_attempted_runtime_max=$((($allAttempted | ForEach-Object {[double]$_.runtime_s}) | Measure-Object -Maximum).Maximum) timeout_seconds=900"
```

```powershell
$cell = 'it__IT.MidClim.SFH-TH.07.Gen.ReEx.001.001__f100'
$root = 'openubem/outputs/eu_certified_rerun_2026-08-28'
foreach ($name in 'eplusout.eio','epluszsz.csv') {
  "$name DIFFERENCES rep1 vs rep2"
  $a = Get-Content -LiteralPath (Join-Path $root "rep1/$cell/$name")
  $b = Get-Content -LiteralPath (Join-Path $root "rep2/$cell/$name")
  Compare-Object $a $b -SyncWindow 1000 | Select-Object -First 20 | Format-Table InputObject,SideIndicator -Wrap
  "$name DIFFERENCES rep1 vs rep3"
  $c = Get-Content -LiteralPath (Join-Path $root "rep3/$cell/$name")
  Compare-Object $a $c -SyncWindow 1000 | Select-Object -First 20 | Format-Table InputObject,SideIndicator -Wrap
}
foreach ($rep in 1..3) {
  $path = Join-Path $root "rep$rep/$cell/epluszsz.csv"
  "rep$rep epluszsz bytes=$((Get-Item -LiteralPath $path).Length) sha256=$((Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash)"
  Get-Content -LiteralPath $path -TotalCount 8
}
```

```powershell
$cell = 'it__IT.MidClim.SFH-TH.07.Gen.ReEx.001.001__f100'
$root = 'openubem/outputs/eu_certified_rerun_2026-08-28'
foreach ($rep in 1..3) {
  $dir = Join-Path $root "rep$rep/$cell"
  "rep$rep"
  foreach ($name in 'eplusout.audit','eplusout.dbg','eplusout.shd','eplusout.bnd','eplusout.mtd') {
    $path = Join-Path $dir $name
    "$name bytes=$((Get-Item -LiteralPath $path).Length) sha256=$((Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash)"
  }
  Select-String -LiteralPath (Join-Path $dir 'eplusout.eio'),(Join-Path $dir 'eplusout.audit'),(Join-Path $dir 'eplusout.dbg') -Pattern 'View Factor','ViewFactor','Converg','Sizing Information' | Select-Object -First 30 | ForEach-Object { "$($_.Path):$($_.LineNumber):$($_.Line)" }
}
```

```powershell
$root = 'openubem/outputs/eu_certified_rerun_2026-08-28'
$rows = Import-Csv -LiteralPath 'docs/docs_ACTIVE/europeanLocations/outputs/deu27_rerun_cells.csv' | Where-Object class -eq 'ATTEMPTED'
$features = foreach ($group in ($rows | Group-Object cell_id)) {
  $path = Join-Path $root "rep1/$($group.Name)/eplusout.expidf"
  $lines = Get-Content -LiteralPath $path
  $values = @($group.Group | Where-Object completed -eq 'True' | ForEach-Object heating_kwh | Sort-Object -Unique)
  [pscustomobject]@{
    cell_id=$group.Name
    fold=$group.Group[0].survey_fold
    any_failed=@($group.Group | Where-Object completed -eq 'False').Count -gt 0
    heat_divergent=$values.Count -gt 1
    surfaces=@($lines | Where-Object { $_ -match '^BUILDINGSURFACE:DETAILED,' }).Count
    windows=@($lines | Where-Object { $_ -match '^FENESTRATIONSURFACE:DETAILED,' }).Count
    other_side=@($lines | Where-Object { $_ -match '^SURFACEPROPERTY:OTHERSIDECOEFFICIENTS,' }).Count
    internal_mass=@($lines | Where-Object { $_ -match '^INTERNALMASS,' }).Count
    ideal_loads=@($lines | Where-Object { $_ -match '^ZONEHVAC:IDEALLOADSAIRSYSTEM,' }).Count
  }
}
"cells=$($features.Count) any_failed=$(@($features | Where-Object any_failed).Count) heat_divergent=$(@($features | Where-Object heat_divergent).Count)"
'BY_WINDOWS'
$features | Group-Object windows | Sort-Object {[int]$_.Name} | ForEach-Object { "windows=$($_.Name) cells=$($_.Count) any_failed=$(@($_.Group | Where-Object any_failed).Count)/$($_.Count) heat_divergent=$(@($_.Group | Where-Object heat_divergent).Count)/$($_.Count)" }
'BY_SURFACES'
$features | Group-Object surfaces | Sort-Object {[int]$_.Name} | ForEach-Object { "surfaces=$($_.Name) cells=$($_.Count) any_failed=$(@($_.Group | Where-Object any_failed).Count)/$($_.Count) heat_divergent=$(@($_.Group | Where-Object heat_divergent).Count)/$($_.Count)" }
'BY_OTHER_SIDE'
$features | Group-Object other_side | Sort-Object {[int]$_.Name} | ForEach-Object { "other_side=$($_.Name) cells=$($_.Count) any_failed=$(@($_.Group | Where-Object any_failed).Count)/$($_.Count) heat_divergent=$(@($_.Group | Where-Object heat_divergent).Count)/$($_.Count)" }
'CONSTANT_COUNTS'
foreach ($field in 'internal_mass','ideal_loads') { $features | Group-Object $field | ForEach-Object { "$field=$($_.Name) cells=$($_.Count)" } }
```

```powershell
$root = 'openubem/outputs/eu_certified_rerun_2026-08-28'
$rows = Import-Csv -LiteralPath 'docs/docs_ACTIVE/europeanLocations/outputs/deu27_rerun_cells.csv' | Where-Object class -eq 'ATTEMPTED'
$features = foreach ($group in ($rows | Group-Object cell_id)) {
  $lines = Get-Content -LiteralPath (Join-Path $root "rep1/$($group.Name)/eplusout.expidf")
  $values = @($group.Group | Where-Object completed -eq 'True' | ForEach-Object heating_kwh | Sort-Object -Unique)
  [pscustomobject]@{
    fold=$group.Group[0].survey_fold
    windows=@($lines | Where-Object { $_ -match '^FENESTRATIONSURFACE:DETAILED,' }).Count
    other_side=@($lines | Where-Object { $_ -match '^SURFACEPROPERTY:OTHERSIDECOEFFICIENTS,' }).Count
    any_failed=@($group.Group | Where-Object completed -eq 'False').Count -gt 0
    heat_divergent=$values.Count -gt 1
  }
}
$features | Group-Object fold,windows | Sort-Object Name | ForEach-Object { "key=$($_.Name) cells=$($_.Count) any_failed=$(@($_.Group | Where-Object any_failed).Count)/$($_.Count) heat_divergent=$(@($_.Group | Where-Object heat_divergent).Count)/$($_.Count)" }
```

```powershell
$cell = 'es__ES.ME.AB.02.Gen.ReEx.001.001__f015'
$root = 'openubem/outputs/eu_certified_rerun_2026-08-28'
foreach ($rep in 1..3) {
  "rep$rep"
  $dir = Join-Path $root "rep$rep/$cell"
  foreach ($name in 'eplusout.err','eplusout.end') {
    $lines = Get-Content -LiteralPath (Join-Path $dir $name)
    for ($n=1; $n -le $lines.Count; $n++) {
      if ($lines[$n-1] -match 'Severe|Fatal|Warmup|Sizing|Completed|Terminated|SolveForWindow|Inside surface heat balance|CalcHeatBalance') {
        "$name`:$n`:$($lines[$n-1])"
      }
    }
  }
}
```

The final pre-write command was:

```powershell
$report = 'docs/docs_ACTIVE/europeanLocations/debugs/docs/FINDING181_REPORT_codex_2026-08-28.md'
"report_exists=$((Test-Path -LiteralPath $report))"
git status --short
```

The post-write verification command was:

```powershell
$report = 'docs/docs_ACTIVE/europeanLocations/debugs/docs/FINDING181_REPORT_codex_2026-08-28.md'
Get-Item -LiteralPath $report | Select-Object FullName,Length,LastWriteTime
rg -n "^# FINDING 181|^## [1-7]\.|MEASURED|INFERRED|H1|H2|H3|H4|H5|H6|20 EnergyPlus runs|Files I created" $report
git status --short -- $report
```

</details>

## 3. Diagnosis — the evidence

1. **MEASURED — H1 is excluded for the principal discriminator.** Each replicate has one matching heating column, 8,760 CSV rows and 8,760 ESO records. ESO and CSV sums agree exactly within each replicate: rep1 `13140.9350530242`, rep2 `14757.7495793352`, rep3 `10128.9780836611`. The first unequal ESO record is zero-based record 0, `01/01 01:00`, with `19901053.9129168`, `20063057.2644545`, and `19328134.0425132` J; the CSV contains those same three values. The source is the three retained `eplusout.eso`/`.csv` pairs; command in §2. The runner also uses synchronous `subprocess.run` before opening the CSV (`eu_cell_runner.py:433-448`), so its parent cannot read the CSV while that process is live.
2. **MEASURED — divergence exists during sizing, before the annual output.** The same cell’s first `epluszsz.csv` row at sizing time `00:05:00` already differs: design heat loads `7568.456`, `7594.040`, and `7485.111` W in reps 1–3. The final `Zone Sizing Information` heat load in `eplusout.eio:95` is respectively `7602.47426`, `7626.57413`, and `7524.24469` W. All four warmup convergence flags in each `eio:107` are `Pass`, although their load-difference diagnostics differ. The discriminator is therefore sizing/initialisation, not a perturbation first appearing mid-year.
3. **MEASURED — model content is identical for that discriminator.** After replacing only `\rep1\`, `\rep2\`, or `\rep3\` in the absolute `Schedule:File` path with `\repN\`, `Compare-Object` reports 0 differing lines for rep1 vs rep2 and 0 for rep1 vs rep3 in `eplusout.expidf`. All three emitted schedule files are 119,988 bytes with SHA-256 `DB28D74A7C505AD2E186937866F38F78FC4838454AC1F5C3FB88F76A5C2B6DCA`. The cell spec pins `openubem/data/weather/it_bologna_2013_2014_y2014.epw` to SHA-256 `ab631c...25fa`, and `verify_weather()` checks that digest before every build (`eu_cell_runner.py:175-185`). **INFERRED —** H4 is excluded for this exemplar’s content, though the path strings are intentionally different and the historical IDF digest is not a model identity.
4. **MEASURED — static expansion/geometry artifacts remain stable while thermal sizing moves.** For the same three runs, `eplusout.dbg`, `.shd`, `.bnd`, and `.mtd` each have one common hash across all three replicas; `eplusout.eio` and `epluszsz.csv` have three distinct hashes. After normalising elapsed time, the three `.err` files differ by 0 lines: each reports two `FixViewFactors` warnings, 0 warmup warnings, 0 warmup severe errors, and successful completion. **INFERRED —** the branching happens after static geometry processing and is silent in the ordinary error summary.
5. **MEASURED — all retained `ENGINE_FAILED` rows are genuine EnergyPlus fatal exits, not timeouts or Python exceptions.** Of 156/1,185 attempted replicate rows marked failed, 156/156 have return code 1, fatal count 1, no heating CSV value, a retained `.err` and `.end`, and a blank driver `error`; 0/156 carry a driver exception. The longest runtime anywhere among all 1,185 attempted rows is 5.604 s against a 900 s timeout. Fatal classification is 117/156 `SolveForWindowTemperatures` and 39/156 “preceding condition”; among the latter, 37/39 mention inside-surface heat-balance non-convergence and temperature bounds, and 2/39 mention `CalcHeatBalanceInsideSurf`. Source: `deu27_rerun_cells.csv` plus every failed `.err`/`.end`, grouped by the command described in §2.
6. **MEASURED — one identical cell takes three qualitatively different paths.** `es__ES.ME.AB.02.Gen.ReEx.001.001__f015` rep1 dies during sizing at `01/01 08:45–08:50` with a window-temperature convergence fatal (`rep1/eplusout.err:10-20`); rep2 completes (`rep2/eplusout.err:35-37`); rep3 proceeds past sizing, accumulates inside-surface heat-balance differences up to `259.339` C and out-of-bounds surface temperatures, then terminates on the preceding condition (`rep3/eplusout.err:22-201`). **INFERRED —** random `completed` is the engine selecting between numerical trajectories, not the status layer inventing a failure.
7. **MEASURED — object counts are associated with instability but do not isolate a necessary or sufficient amplifier.** Across 395 attempted cells, every expanded IDF has exactly one `InternalMass` and one `ZoneHVAC:IdealLoadsAirSystem`, so neither count can discriminate. By fenestration count, status failure / heating divergence are 31/80 and 40/80 for two windows, 23/170 and 22/170 for three, and 67/145 and 73/145 for four. The relationship is non-monotone and fold-confounded; even the UK’s single three-window group has 12/95 cells with a failure and 10/95 with divergent completed values. Building-surface/`OtherSideCoefficients` counts are likewise non-monotone. **INFERRED —** H6 is observationally plausible as amplification by topology, but no single counted object class is the mechanism.
8. **MEASURED — there is a prompt/source conflict that blocks a window-boundary diagnosis.** The prompt says the windows sit on hosts using `OtherSideCoefficients`; current `european_box.py:280-284` explicitly assigns each opening host `Outside Boundary Condition = Outdoors`, and the retained expanded IDFs show both kinds: floor/roof/equivalent opaque faces use `OtherSideCoefficients`, while opening hosts use `Outdoors`. I use the retained expanded input as the statement of what was simulated and make no inference about which description was intended.

## 4. Hypotheses

| Hypothesis | Test and status | Discriminator |
|---|---|---|
| H1 — post-simulation harness / ReadVarsESO | **Tested; excluded for the clean Italian discriminator.** | ESO already differs at the first annual record; each ESO sum equals its complete 8,760-row CSV sum; synchronous child completion precedes parsing. |
| H2 — sensitive iterative solution of the unenclosed zone | **Tested indirectly; supported but not proved.** | Expanded input is fixed; sizing trace, sizing result, warmup-load diagnostic and first annual record differ; the same cell can complete or enter either of two convergence-fatal paths. Exact solver state is not retained. |
| H3 — genuinely non-deterministic EnergyPlus 23.1 build | **Tested as a black box; supported at the engine boundary, implementation cause inconclusive.** | Fixed expanded input and static geometry artifacts yield different EnergyPlus sizing/ESO artifacts. No debugger, trace, memory diagnostic, or controlled second build exists on disk. |
| H4 — different inputs | **Tested; excluded by content for the discriminator.** | Normalised expanded IDFs match line-for-line, schedules have one digest, and weather is digest-guarded before each run. Absolute schedule paths alone differ. |
| H5 — environment / timeout / filesystem | **Partly tested; timeout and harness exception excluded; other environment causes inconclusive.** | Maximum observed runtime 5.604/900 s; all 156/156 failed retained rows contain EnergyPlus fatal artifacts. Captured stdout/stderr and historical platform metadata were not retained. |
| H6 — one object class as amplifier | **Tested observationally; inconclusive.** | `InternalMass` and Ideal Loads counts are constant; window and other-side/surface counts associate non-monotonically and do not separate stable from unstable cells. |
| H7 — failure first emerges in the annual simulation | **Tested; excluded for the discriminator.** | `epluszsz.csv` differs at its first sizing timestep and final design heating load differs before `01/01 01:00`. |

## 5. How to solve it

**Option A — make the model/engine path deterministic by redesigning the equivalent envelope.** Replace independently located, unenclosed heat-transfer faces with a physically closed one-zone prism (or another closed surrogate) while preserving declared area and transmission coefficients through an explicit, reviewed mapping; keep one declared thermal-capacity object and make every opening host relationship physically valid. Cost: a design ruling, implementation, coefficient/readback regression work, and a full diagnostic and campaign rerun because the physical model changes. It would prove whether removing the ill-posed geometry removes nondeterminism and would provide a defensible simulation model if it does. It would **not** prove which EnergyPlus 23.1 code defect or solver branch caused the old behaviour, and matching aggregate coefficients would not prove matching old heating results.

**Option B — make the harness statistically tolerant.** Treat each cell execution as a draw: use a predeclared replicate count, retain ESO plus stderr, reject cells/folds with excessive failure or dispersion, and report replicated fold distributions/intervals rather than selecting a lucky unanimous triplet. Cost: the chosen replicate multiplier in compute and storage, plus changed gate semantics. It would measure operational uncertainty and prevent a single draw from masquerading as a cell attribute. It would **not** make EnergyPlus deterministic, make an ill-posed model correct, or license any cell-level value.

**Option C — declare the limitation and quote only what demonstrably survives.** Freeze the current engine/model, prohibit all cell quotations and rankings, and permit only predeclared fold aggregates whose uncertainty is estimated from independent full-fold reruns and is acceptable for the intended claim; otherwise quote nothing. Cost: fewer usable claims and repeated fold-level diagnostics when the software or environment changes. It would make the evidence honest about this engine’s behaviour. It would **not** repair the engine, validate the equivalent-envelope design, or guarantee transfer to another host/build.

**Recommendation:** adopt Option A as the remedy and Option C as the standing publication rule until the redesigned model passes replication, because replication can quantify this failure but cannot turn an unidentified numerical trajectory into a physically trustworthy cell result.

## 6. What I could NOT determine

I could not identify the EnergyPlus source-level cause, decide between uninitialised/build-dependent state and sensitive dependence of the equivalent-envelope solver, recover captured process stdout/stderr or historical platform metadata, inspect the ten-replicate artifacts held in the other repository, or reconcile the prompt’s “window hosts use `OtherSideCoefficients`” statement with the retained/current `Outdoors` hosts. The single cheapest credible experiment is a two-condition sizing discriminator on one retained high-divergence cell: ten direct baseline runs of the exact expanded input, and ten runs with sizing/autosizing removed by hard-sizing from one retained sizing result, all in fresh isolated directories with ESO, EIO, stdout and stderr retained — **20 EnergyPlus runs**. Stability only in the hard-sized arm would make the sizing/autosizing path necessary; instability in both arms would exclude it as the sole mechanism. It would not by itself distinguish an EnergyPlus memory/order defect from sensitivity elsewhere in the heat balance, nor validate the model’s physics.

## 7. Files I created

1. `docs/docs_ACTIVE/europeanLocations/debugs/docs/FINDING181_REPORT_codex_2026-08-28.md`

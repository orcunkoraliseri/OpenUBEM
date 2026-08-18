$pid_to_watch = 22164
$log = "C:\Users\o_iseri\Desktop\OpenUBEM\t08_monitor.log"
$main_log = "C:\Users\o_iseri\Desktop\OpenUBEM\t08_local_remainder.log"
$csv = "C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons\t08_local_remainder_eui.csv"

function Write-Status {
    param($msg)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$ts  $msg" | Add-Content -Path $log
}

Write-Status "Monitoring started: PID=$pid_to_watch"

while ($true) {
    Start-Sleep -Seconds 1800   # 30 minutes

    $proc = Get-Process -Id $pid_to_watch -ErrorAction SilentlyContinue
    if (-not $proc) {
        Write-Status "PROCESS EXITED. Checking outputs..."
        if (Test-Path $csv) {
            $rows = (Get-Content $csv | Measure-Object -Line).Lines
            Write-Status "CSV exists: $rows rows"
        } else {
            Write-Status "CSV NOT found yet."
        }
        $last10 = Get-Content $main_log -Tail 10 -ErrorAction SilentlyContinue
        Write-Status ("Last log lines: " + ($last10 -join " | "))
        Write-Status "DONE. Process has finished."
        break
    }

    # Still running -- log progress snapshot
    $cpu = [math]::Round($proc.CPU, 1)
    $mem_mb = [math]::Round($proc.WorkingSet / 1MB, 0)
    $last5 = Get-Content $main_log -Tail 5 -ErrorAction SilentlyContinue
    $summary = if ($last5) { ($last5 -join " | ") } else { "(no output yet)" }
    $csv_rows = if (Test-Path $csv) { (Get-Content $csv | Measure-Object -Line).Lines } else { 0 }
    Write-Status "RUNNING cpu=${cpu}s mem=${mem_mb}MB csv_rows=$csv_rows | $summary"
}

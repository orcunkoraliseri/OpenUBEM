# Run this ONCE as Administrator to register the daily auto-commit scheduled task.
# Required elevation: Run PowerShell as Administrator, then execute this script.

$TaskName   = "OpenUBEM-AutoCommit"
$ScriptPath = "C:\Users\o_iseri\Desktop\OpenUBEM\scripts\auto_commit.ps1"

# Remove any existing task with the same name to allow re-registration
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NonInteractive -ExecutionPolicy Bypass -File `"$ScriptPath`""

# Daily at 23:00
$trigger = New-ScheduledTaskTrigger -Daily -At "23:00"

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -MultipleInstances IgnoreNew

# Run as the current logged-in user (limited, not SYSTEM)
$principal = New-ScheduledTaskPrincipal `
    -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -RunLevel Limited `
    -LogonType S4U

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Daily auto-commit and push for OpenUBEM to GitHub (origin/main)"

Write-Host "Scheduled task '$TaskName' registered. Runs daily at 23:00." -ForegroundColor Green
Write-Host "Logs will appear in: C:\Users\o_iseri\Desktop\OpenUBEM\tmp\auto_commit.log"

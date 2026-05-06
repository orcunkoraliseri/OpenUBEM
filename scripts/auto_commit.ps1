# Auto daily commit and push for OpenUBEM
# Target repo: https://github.com/orcunkoraliseri/OpenUBEM.git  branch: main

$ProjectRoot = "C:\Users\o_iseri\Desktop\OpenUBEM"
$LogFile     = "$ProjectRoot\tmp\auto_commit.log"
$Date        = Get-Date -Format "yyyy-MM-dd"
$Timestamp   = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Ensure log directory exists
$null = New-Item -ItemType Directory -Path "$ProjectRoot\tmp" -Force

Set-Location $ProjectRoot

# Stage all changes (respects .gitignore)
git add -A

# Check for staged changes
$status = git status --porcelain
if (-not $status) {
    Add-Content -Path $LogFile -Value "[$Timestamp] Nothing to commit"
    exit 0
}

# Commit
git commit -m "chore: auto daily commit $Date"
if ($LASTEXITCODE -ne 0) {
    Add-Content -Path $LogFile -Value "[$Timestamp] COMMIT FAILED"
    exit 1
}

# Push
git push origin main
if ($LASTEXITCODE -eq 0) {
    Add-Content -Path $LogFile -Value "[$Timestamp] SUCCESS"
} else {
    Add-Content -Path $LogFile -Value "[$Timestamp] PUSH FAILED"
    exit 1
}

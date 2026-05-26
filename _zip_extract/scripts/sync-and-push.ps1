# Sync with remote, commit (optional), and push to GitHub.
# Usage:
#   .\scripts\sync-and-push.ps1                          # push only
#   .\scripts\sync-and-push.ps1 -Message "fix routing"   # commit + push

param(
    [string]$Message = ""
)

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

# Non-interactive SSH (if remote uses git@github.com)
$env:GIT_SSH_COMMAND = "ssh -o StrictHostKeyChecking=accept-new -o BatchMode=yes"

function Invoke-Git {
    param([string[]]$GitArgs)
    Write-Host ">> git $($GitArgs -join ' ')" -ForegroundColor Cyan
    & git @GitArgs
    if ($LASTEXITCODE -ne 0) { throw "git failed: git $($GitArgs -join ' ')" }
}

Write-Host "`n=== HDWS GitHub Sync & Push ===`n" -ForegroundColor Green

# Step 1: verify (optional but recommended)
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "Running verify.py ..." -ForegroundColor Yellow
    python verify.py
    if ($LASTEXITCODE -ne 0) { throw "verify.py failed - fix before pushing" }
}

# Step 2: fetch + rebase
$maxRetries = 3
for ($i = 1; $i -le $maxRetries; $i++) {
    try {
        Invoke-Git @("fetch", "origin")
        Invoke-Git @("pull", "origin", "main", "--rebase")
        break
    } catch {
        if ($i -eq $maxRetries) {
            Write-Host "`nNetwork error after $maxRetries attempts." -ForegroundColor Red
            Write-Host "Try: configure proxy/VPN, or upload via GitHub web UI." -ForegroundColor Yellow
            throw
        }
        Write-Host "Retry $i/$maxRetries in 3s ..." -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
}

# Step 3: commit if message provided
if ($Message -ne "") {
    Invoke-Git @("add", "-A")
    $status = git status --porcelain
    if ($status) {
        Invoke-Git @("commit", "-m", $Message)
    } else {
        Write-Host "Nothing to commit." -ForegroundColor Yellow
    }
}

# Step 4: push
for ($i = 1; $i -le $maxRetries; $i++) {
    try {
        Invoke-Git @("push", "origin", "main")
        Write-Host "`nPush succeeded!" -ForegroundColor Green
        exit 0
    } catch {
        if ($i -eq $maxRetries) { throw }
        Write-Host "Push retry $i/$maxRetries in 3s ..." -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
}

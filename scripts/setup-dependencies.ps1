param(
    [string]$RootDir = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
)

$SetupMarker = Join-Path $RootDir ".deps_installed"
if (Test-Path $SetupMarker) {
    Write-Host "✓ Dependencies already set up. Delete '.deps_installed' to re-run setup." -ForegroundColor Green
    exit 0
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  Bank Reconciliation System - Setup"     -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will install required runtimes and dependencies."
Write-Host ""

# ── Helper: find or install via winget ──────────────────────────────────────
$NeedsRefresh = $false

function Install-Missing {
    param([string]$Label, [string]$DetectCmd, [string]$WingetId, [string]$CheckFile)
    Write-Host "» Checking $Label..." -ForegroundColor Yellow
    if ($CheckFile -and (Test-Path $CheckFile)) { return $true }
    try {
        $null = Get-Command $DetectCmd -ErrorAction Stop
        Write-Host "  ✓ $Label found" -ForegroundColor Green
        return $true
    } catch { }
    Write-Host "  ⚠ $Label not found. Installing via winget..." -ForegroundColor Magenta
    try {
        $proc = Start-Process -Wait -PassThru -NoNewWindow `
            -FilePath "winget" `
            -ArgumentList "install --id $WingetId --accept-source-agreements --accept-package-agreements --scope machine"
        if ($proc.ExitCode -eq 0 -or $proc.ExitCode -eq 17025) {
            Write-Host "  ✓ $Label installed" -ForegroundColor Green
            $script:NeedsRefresh = $true
            return $true
        } else {
            # Retry as user scope
            $proc2 = Start-Process -Wait -PassThru -NoNewWindow `
                -FilePath "winget" `
                -ArgumentList "install --id $WingetId --accept-source-agreements --accept-package-agreements --scope user"
            if ($proc2.ExitCode -eq 0 -or $proc2.ExitCode -eq 17025) {
                Write-Host "  ✓ $Label installed (user scope)" -ForegroundColor Green
                $script:NeedsRefresh = $true
                return $true
            }
            Write-Host "  ✖ Failed to install $Label (exit: $($proc2.ExitCode))" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "  ✖ Failed to install $Label : $_" -ForegroundColor Red
        return $false
    }
}

# ── 1. Python ───────────────────────────────────────────────────────────────
Install-Missing -Label "Python" -DetectCmd "python" -WingetId "Python.Python.3.12"
Install-Missing -Label "Python" -DetectCmd "python3" -WingetId "Python.Python.3.12"

# ── 2. Node.js ──────────────────────────────────────────────────────────────
Install-Missing -Label "Node.js" -DetectCmd "node" -WingetId "OpenJS.NodeJS.LTS"

# ── 3. Refresh environment variables ────────────────────────────────────────
if ($NeedsRefresh) {
    Write-Host "» Refreshing environment variables..." -ForegroundColor Yellow
    # Reload PATH from registry for the current process
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath    = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath;$env:Path"
    # Let the OS refresh too
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "Process")
}

# ── 5. Backend uv sync ──────────────────────────────────────────────────────
$BackendDir = Join-Path $RootDir "backend"

Write-Host "`n» Setting up backend environment with uv..." -ForegroundColor Yellow
if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Write-Host "  ⚠ uv not found. Installing uv..." -ForegroundColor Magenta
    try {
        $proc = Start-Process -Wait -PassThru -NoNewWindow `
            -FilePath "powershell" `
            -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command `"irm https://astral.sh/uv/install.ps1 | iex`""
        if ($proc.ExitCode -ne 0) {
            Write-Host "  ✖ Failed to install uv" -ForegroundColor Red
            exit 1
        }
        $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
        Write-Host "  ✓ uv installed" -ForegroundColor Green
    } catch {
        Write-Host "  ✖ Failed to install uv : $_" -ForegroundColor Red
        exit 1
    }
}

Push-Location $BackendDir
& "uv" sync
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✖ Failed to sync backend dependencies" -ForegroundColor Red
    Pop-Location
    exit 1
}
Pop-Location
Write-Host "  ✓ Backend dependencies installed" -ForegroundColor Green

# ── 6. Frontend npm install ─────────────────────────────────────────────────
$FrontendDir = Join-Path $RootDir "frontend"
$NodeModules = Join-Path $FrontendDir "node_modules"

if (-not (Test-Path $NodeModules)) {
    Write-Host "`n» Installing frontend Node.js dependencies..." -ForegroundColor Yellow
    Push-Location $FrontendDir
    & "npm" install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✖ Failed to install frontend dependencies" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Pop-Location
    Write-Host "  ✓ Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  ✓ Frontend node_modules already exists" -ForegroundColor Green
}

# ── 7. Marker ───────────────────────────────────────────────────────────────
"Installed on $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -Encoding utf8 $SetupMarker
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  ✓ Setup complete! Ready to start."       -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

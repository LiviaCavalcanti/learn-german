#Requires -Version 5.1
<#
.SYNOPSIS
  Sprachheft - one-command setup (Windows).

.DESCRIPTION
  Installs every dependency the app needs and (optionally) starts it:
    * uv            - Python package/venv manager (installs Python 3.12 itself)
    * backend deps  - FastAPI service + optional extras (llm, embeddings, ...)
    * Node.js       - resolved from PATH / a portable install / winget (needs >= 20.19)
    * frontend deps - npm ci (reproducible install)
    * backend\.env  - created from .env.example if missing
    * dictionary    - offline WikDict database (data\dict.sqlite)

  Safe to re-run: every step is idempotent.

.PARAMETER Run
  After installing, start the backend and frontend in two new windows.

.PARAMETER Minimal
  Backend base + dev only (skip the llm / embeddings / phonetics extras).

.PARAMETER WithTranscribe
  Also install the transcribe extra (yt-dlp + faster-whisper; needs ffmpeg on PATH).

.PARAMETER SkipDict
  Do not download / build the offline dictionary.

.EXAMPLE
  .\setup.ps1
.EXAMPLE
  .\setup.ps1 -Run
#>
[CmdletBinding()]
param(
    [switch]$Run,
    [switch]$Minimal,
    [switch]$WithTranscribe,
    [switch]$SkipDict,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Root = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }

$NodeMinMajor = 20
$NodeMinMinor = 19

# --- pretty logging ----------------------------------------------------------
function Write-Step($m) { Write-Host "`n==> $m" -ForegroundColor Cyan }
function Write-Info($m) { Write-Host "     $m" -ForegroundColor DarkGray }
function Write-Ok($m)   { Write-Host "  [OK] $m" -ForegroundColor Green }
function Write-Warn($m) { Write-Host "  [!]  $m" -ForegroundColor Yellow }

function Show-Usage {
    Write-Host @"
Sprachheft setup (Windows)

  .\setup.ps1                 full install (recommended)
  .\setup.ps1 -Run            install, then start backend + frontend
  .\setup.ps1 -Minimal        backend base + dev only (skip llm/embeddings/phonetics)
  .\setup.ps1 -WithTranscribe also install yt-dlp + faster-whisper (needs ffmpeg)
  .\setup.ps1 -SkipDict       don't download/build the offline dictionary
  .\setup.ps1 -Help

Tip: double-click setup.bat to run this without opening a terminal.
"@
}

if ($Help) { Show-Usage; exit 0 }

# --- 1. uv (Python toolchain) ------------------------------------------------
function Install-Uv {
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        Write-Ok ("uv " + ((uv --version) 2>$null) + " found")
        return
    }
    Write-Step 'Installing uv (Python package manager)'
    try {
        Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    } catch {
        throw "Failed to install uv automatically. Install it manually from https://docs.astral.sh/uv/ then re-run. ($_)"
    }
    $uvBin = Join-Path $env:USERPROFILE '.local\bin'
    if (Test-Path (Join-Path $uvBin 'uv.exe')) { $env:Path = "$uvBin;$env:Path" }
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        throw 'uv installed but not found on PATH - open a new terminal and re-run.'
    }
    Write-Ok 'uv installed'
}

# --- 2. backend dependencies -------------------------------------------------
function Install-Backend {
    $extras = @('dev')
    if (-not $Minimal) { $extras += @('llm', 'embeddings', 'phonetics') }
    if ($WithTranscribe) { $extras += 'transcribe' }

    $uvArgs = @('sync')
    foreach ($e in $extras) { $uvArgs += @('--extra', $e) }

    Write-Step "Installing backend dependencies (uv $($uvArgs -join ' '))"
    Write-Info 'uv will download Python 3.12 automatically if it is missing.'
    Push-Location (Join-Path $Root 'backend')
    try {
        & uv @uvArgs
        if ($LASTEXITCODE -ne 0) { throw "uv sync failed (exit $LASTEXITCODE)." }
    } finally { Pop-Location }
    Write-Ok "Backend ready (extras: $($extras -join ', '))"
}

# --- 3. Node.js (frontend runtime) -------------------------------------------
function Resolve-NodeDir {
    $cmd = Get-Command node -ErrorAction SilentlyContinue
    if ($cmd) { return (Split-Path $cmd.Source) }

    # Portable install used by this repo's run-dev.ps1: %USERPROFILE%\.local\node\<ver>\
    $portable = Join-Path $env:USERPROFILE '.local\node'
    if (Test-Path $portable) {
        $found = Get-ChildItem -Path $portable -Filter node.exe -Recurse -ErrorAction SilentlyContinue |
            Select-Object -First 1 -ExpandProperty FullName
        if ($found) { return (Split-Path $found) }
    }
    foreach ($p in @((Join-Path $env:ProgramFiles 'nodejs\node.exe'),
                     (Join-Path ${env:ProgramFiles(x86)} 'nodejs\node.exe'))) {
        if ($p -and (Test-Path $p)) { return (Split-Path $p) }
    }
    return $null
}

function Test-NodeVersion {
    $v = (& node -v) 2>$null
    if (-not $v) { return $false }
    $v = ($v -replace '^v', '')
    $parts = $v.Split('.')
    $maj = [int]$parts[0]; $min = [int]$parts[1]
    return ($maj -gt $NodeMinMajor) -or ($maj -eq $NodeMinMajor -and $min -ge $NodeMinMinor)
}

function Install-Node {
    $dir = Resolve-NodeDir
    if ($dir) { $env:Path = "$dir;$env:Path" }
    if (Test-NodeVersion) { Write-Ok "Node $(& node -v) found"; return $true }

    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Step 'Installing Node.js LTS via winget'
        try {
            winget install -e --id OpenJS.NodeJS.LTS --silent `
                --accept-package-agreements --accept-source-agreements | Out-Null
        } catch { Write-Warn "winget install failed: $_" }
        $dir = Resolve-NodeDir
        if ($dir) { $env:Path = "$dir;$env:Path" }
    }

    if (Test-NodeVersion) { Write-Ok "Node $(& node -v) ready"; return $true }

    Write-Warn "Node.js >= $NodeMinMajor.$NodeMinMinor not found - skipping frontend."
    Write-Info 'Install Node from https://nodejs.org or run:'
    Write-Info '  winget install -e --id OpenJS.NodeJS.LTS'
    return $false
}

# --- 4. frontend dependencies ------------------------------------------------
function Install-Frontend {
    Write-Step 'Installing frontend dependencies (npm)'
    Push-Location (Join-Path $Root 'frontend')
    try {
        if (Test-Path 'package-lock.json') {
            & npm ci
            if ($LASTEXITCODE -ne 0) {
                Write-Warn 'npm ci failed - falling back to npm install'
                & npm install
            }
        } else {
            & npm install
        }
        if ($LASTEXITCODE -ne 0) { throw "npm install failed (exit $LASTEXITCODE)." }
    } finally { Pop-Location }
    Write-Ok 'Frontend ready'
}

# --- 5. configuration file ---------------------------------------------------
function Set-EnvFile {
    Write-Step 'Configuration (backend\.env)'
    $envPath = Join-Path $Root 'backend\.env'
    $example = Join-Path $Root 'backend\.env.example'
    if (Test-Path $envPath) {
        Write-Info 'backend\.env already exists - left untouched.'
    } else {
        Copy-Item $example $envPath
        Write-Ok "Created backend\.env from .env.example (offline 'fake' LLM by default)."
    }
}

# --- 6. offline dictionary ---------------------------------------------------
function Build-Dictionary {
    if ($SkipDict) { Write-Info 'Skipping dictionary build (-SkipDict).'; return }
    if (Test-Path (Join-Path $Root 'data\dict.sqlite')) {
        Write-Ok 'Offline dictionary already built (data\dict.sqlite).'
        return
    }
    Write-Step 'Building offline dictionary (WikDict, ~25 MB download, CC BY-SA)'
    Push-Location (Join-Path $Root 'backend')
    try {
        & uv run python -m sprachheft.dictionary.loader
        if ($LASTEXITCODE -ne 0) {
            Write-Warn 'Dictionary build failed (offline?). Re-run later:'
            Write-Info '  cd backend; uv run python -m sprachheft.dictionary.loader'
        } else {
            Write-Ok 'Dictionary built.'
        }
    } finally { Pop-Location }
}

# --- optional: start the app -------------------------------------------------
function Start-App {
    Write-Step 'Starting Sprachheft in two new windows'
    $uvBin   = Join-Path $env:USERPROFILE '.local\bin'
    $nodeDir = Resolve-NodeDir
    Start-Process powershell -ArgumentList '-NoExit', '-Command', `
        "`$env:Path = '$uvBin;' + `$env:Path; Set-Location '$Root\backend'; uv run python main.py"
    Start-Process powershell -ArgumentList '-NoExit', '-Command', `
        "`$env:Path = '$nodeDir;' + `$env:Path; Set-Location '$Root\frontend'; npm run dev"
    Write-Host '  Backend : http://127.0.0.1:8000/health'
    Write-Host '  Frontend: http://localhost:5173'
}

# --- run ---------------------------------------------------------------------
try {
    Write-Host "Sprachheft setup  ($Root)" -ForegroundColor Cyan

    Install-Uv
    Install-Backend

    $frontendOk = Install-Node
    if ($frontendOk) { Install-Frontend }

    Set-EnvFile
    Build-Dictionary

    Write-Step 'Setup complete'
    Write-Info 'Start the app:'
    Write-Info '  .\setup.ps1 -Run           (backend + frontend together)'
    Write-Info '  cd backend;  uv run python main.py    -> http://127.0.0.1:8000'
    Write-Info '  cd frontend; npm run dev             -> http://localhost:5173'
    Write-Info 'Configure the LLM and ports in backend\.env'
    if (-not $frontendOk) {
        Write-Warn "Frontend was skipped - install Node >= $NodeMinMajor.$NodeMinMinor and re-run."
    }

    if ($Run) {
        if ($frontendOk) { Start-App }
        else { throw 'Cannot -Run without a working Node.js/frontend.' }
    }
} catch {
    Write-Host "`n  [x] Setup failed: $_" -ForegroundColor Red
    exit 1
}

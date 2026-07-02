# Sprachheft dev launcher — starts the FastAPI backend and the Vite frontend
# in two new PowerShell windows.
#
#   powershell -ExecutionPolicy Bypass -File .\run-dev.ps1

$root = $PSScriptRoot
$node = "C:\Users\z0050s2b\.local\node\node-v24.18.0-win-x64"
$uvbin = "$env:USERPROFILE\.local\bin"

Start-Process powershell -ArgumentList '-NoExit', '-Command', (
  "`$env:Path = `"$uvbin;`" + `$env:Path; Set-Location `"$root\backend`"; uv run python main.py"
)
Start-Process powershell -ArgumentList '-NoExit', '-Command', (
  "`$env:Path = `"$node;`" + `$env:Path; Set-Location `"$root\frontend`"; npm run dev"
)

Write-Host "Backend:  http://127.0.0.1:8000/health"
Write-Host "Frontend: http://localhost:5173"
Write-Host "First time only: run 'uv run python -m sprachheft.dictionary.loader' in backend to build the dictionary."

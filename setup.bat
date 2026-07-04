@echo off
setlocal EnableExtensions
REM ===========================================================================
REM  Sprachheft — Windows setup launcher ("exec").
REM
REM  Double-click this file to install everything, or run it from a terminal
REM  and pass options through to setup.ps1, e.g.:
REM
REM      setup.bat -Run
REM      setup.bat -Minimal -SkipDict
REM      setup.bat -Help
REM
REM  It just invokes setup.ps1 with an execution-policy bypass (preferring
REM  PowerShell 7 "pwsh" when available, otherwise Windows PowerShell).
REM ===========================================================================

set "PS=powershell"
where pwsh >nul 2>&1 && set "PS=pwsh"

"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1" %*
set "RC=%ERRORLEVEL%"

REM Keep the window open only when the script was double-clicked (so output is
REM readable); stay quiet when invoked from an existing terminal.
echo %cmdcmdline% | find /i "%~nx0" >nul
if not errorlevel 1 (
    echo.
    pause
)

exit /b %RC%

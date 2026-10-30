$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot/..
if (!(Test-Path .venv/Scripts/python.exe)) { throw 'Run scripts/run.ps1 to set up the environment and source data first.' }
if (!(Test-Path data/olist.duckdb)) { throw 'Run scripts/run.ps1 to build the analytical database first.' }
Write-Host 'Open http://127.0.0.1:8765 in your browser. Keep this terminal open; Ctrl+C stops the dashboard.'
& .venv/Scripts/python.exe -m src.dashboard
if ($LASTEXITCODE) { throw 'Dashboard stopped with an error. Check whether port 8765 is already in use.' }

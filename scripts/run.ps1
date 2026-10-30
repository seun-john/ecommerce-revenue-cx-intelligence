$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot/..
if (!(Test-Path .venv/Scripts/python.exe)) { py -3 -m venv .venv }
& .venv/Scripts/python.exe -m pip install -e '.[dev]'
if ($LASTEXITCODE) { throw 'Dependency installation failed' }
& .venv/Scripts/python.exe -m src.acquire
if ($LASTEXITCODE) { throw 'Dataset acquisition failed; see docs/REPRODUCE.md' }
& .venv/Scripts/python.exe -m src.pipeline
if ($LASTEXITCODE) { throw 'Pipeline failed' }
& .venv/Scripts/python.exe -m pytest -q
if ($LASTEXITCODE) { throw 'Tests failed' }

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$projectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) {
    throw 'Virtual environment missing. Follow RELEASE_GUIDE.md and run setup.ps1.'
}
& $projectPython -m streamlit run app.py --server.address 127.0.0.1

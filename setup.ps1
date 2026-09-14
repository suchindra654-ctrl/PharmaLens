$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (!(Test-Path '.venv\Scripts\python.exe')) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.12 -m venv .venv
    } else {
        Write-Error 'Install Python 3.12 from python.org, reopen VS Code, then run setup.ps1 again.'
    }
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 was not found. Install it from python.org and reopen VS Code.' }
}
& .\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
if (!(Test-Path '.env')) { Copy-Item '.env.example' '.env' }
& .\.venv\Scripts\python.exe prepare_library.py
if ($LASTEXITCODE -ne 0) { throw 'PDF indexing failed.' }
Write-Host 'Setup complete. Add GEMINI_API_KEY to .env for AI answers.'
Write-Host 'Create your first admin: .\.venv\Scripts\python.exe create_admin.py'
Write-Host 'Start: .\.venv\Scripts\python.exe -m streamlit run app.py'

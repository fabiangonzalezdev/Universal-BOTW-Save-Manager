$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create Python environment.' }
}
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $python -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& $python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
& $python main.py --smoke-test
if ($LASTEXITCODE -ne 0) { throw 'UI smoke test failed.' }
& $python build.py
if ($LASTEXITCODE -ne 0) { throw 'Build failed.' }
$exe = Join-Path $PSScriptRoot 'dist\Universal-BOTW-Save-Manager.exe'
$p = Start-Process -FilePath $exe -ArgumentList '--self-test' -Wait -PassThru -WindowStyle Hidden
if ($p.ExitCode -ne 0) { throw 'Packaged resources failed.' }
& $python package_release.py --platform windows-x64
if ($LASTEXITCODE -ne 0) { throw 'Packaging failed.' }
Write-Host 'Done / Listo: see releases/ for the versioned ZIP, SHA-256 and README.'

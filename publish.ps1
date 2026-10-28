param([string]$Owner, [switch]$SkipRelease)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$gh = Get-Command gh -ErrorAction SilentlyContinue
if (-not $gh) { throw 'Install GitHub CLI first: https://cli.github.com/ . Then run gh auth login.' }
& $gh.Source auth status
if ($LASTEXITCODE -ne 0) { throw 'Run gh auth login first. Never paste a token into the README or chat.' }
if (-not $Owner) { $Owner = & $gh.Source api user --jq .login }
$repo = "$Owner/Universal-BOTW-Save-Manager"
if (-not (Test-Path -LiteralPath '.git')) { git init -b main }
if (-not (git status --porcelain)) {
    Write-Host 'Working tree already committed.'
} else {
    git add .
    git commit -m 'Create cross-platform BOTW save manager preview'
    if ($LASTEXITCODE -ne 0) { throw 'Commit failed; configure your Git author name/email.' }
}
& $gh.Source repo view $repo --json name 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    & $gh.Source repo create $repo --public --source . --remote origin --push --description 'Offline Wii U and Switch BOTW save converter. Windows first; native desktop UI.'
} else {
    $remote = git remote get-url origin 2>$null
    if (-not $remote -or $remote -notmatch [regex]::Escape($repo)) { throw 'Existing repository/remote must be checked manually before pushing.' }
    git push -u origin main
}
if ($LASTEXITCODE -ne 0) { throw 'Repository publication failed.' }
if (-not $SkipRelease) {
    & $gh.Source release create v0.3.0-alpha.1 --repo $repo --target main --prerelease --title 'Universal-BOTW-Save Manager v0.3.0-alpha.1' --notes-file RELEASE_NOTES.md 'releases/v0.3.0-alpha.1/Universal-BOTW-Save-Manager-v0.3.0-alpha.1-windows-x64.zip' 'releases/v0.3.0-alpha.1/Universal-BOTW-Save-Manager-v0.3.0-alpha.1-windows-x64.sha256'
    if ($LASTEXITCODE -ne 0) { throw 'Release publication failed. Check existing releases before retrying.' }
}

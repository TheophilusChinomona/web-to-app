param(
  [switch]$DryRun,
  [switch]$Force,
  [switch]$NoAutoInstall,
  [string]$TargetDir = "$HOME/.web-to-app-cli",
  [string]$Repo = "https://github.com/TheophilusChinomona/web-to-app.git",
  [string]$Branch = "expo-cross-platform"
)

$ErrorActionPreference = 'Stop'

function Log($msg) { Write-Host "[install] $msg" }
function Run($cmd) {
  if ($DryRun) { Write-Host "[dry-run] $cmd" }
  else { Invoke-Expression $cmd }
}
function Has-Cmd($name) {
  return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}
function Install-WithWinget($id) {
  Run "winget install --id $id --silent --accept-package-agreements --accept-source-agreements"
}
function Install-WithChoco($pkg) {
  Run "choco install $pkg -y"
}

function Ensure-Dependency($cmdName) {
  if (Has-Cmd $cmdName) { return }
  if ($NoAutoInstall) { throw "Missing dependency: $cmdName" }

  Log "Missing dependency detected: $cmdName"

  if (Has-Cmd "winget") {
    switch ($cmdName) {
      "git"  { Install-WithWinget "Git.Git" }
      "node" { Install-WithWinget "OpenJS.NodeJS.LTS" }
      "npm"  { Install-WithWinget "OpenJS.NodeJS.LTS" }
      default { throw "No winget mapping for: $cmdName" }
    }
  }
  elseif (Has-Cmd "choco") {
    switch ($cmdName) {
      "git"  { Install-WithChoco "git" }
      "node" { Install-WithChoco "nodejs-lts" }
      "npm"  { Install-WithChoco "nodejs-lts" }
      default { throw "No choco mapping for: $cmdName" }
    }
  }
  else {
    throw "No supported package manager found (winget/choco) to auto-install '$cmdName'."
  }

  if (-not (Has-Cmd $cmdName)) {
    $env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')
  }

  if (-not (Has-Cmd $cmdName)) {
    throw "Dependency install attempted, but '$cmdName' is still missing. Restart shell and retry."
  }

  Log "Dependency ready: $cmdName"
}

Ensure-Dependency git
Ensure-Dependency node
Ensure-Dependency npm

if (Test-Path $TargetDir) {
  if ($Force) {
    Log "Removing existing directory: $TargetDir"
    Run "Remove-Item -Recurse -Force \"$TargetDir\""
  }
  else {
    throw "Target directory already exists: $TargetDir. Re-run with -Force"
  }
}

Log "Cloning $Repo into $TargetDir"
Run "git clone --depth 1 --branch \"$Branch\" \"$Repo\" \"$TargetDir\""

Log "Installing Expo wrapper dependencies"
Run "cd \"$TargetDir/expo-wrapper\"; npm install"

Log "Running tests"
Run "cd \"$TargetDir/expo-wrapper\"; npm test -- --runInBand"

Write-Host ""
Write-Host "✅ web-to-app CLI setup complete."
Write-Host ""
Write-Host "Location:"
Write-Host "  $TargetDir"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  cd \"$TargetDir/expo-wrapper\""
Write-Host "  `$env:EXPO_PUBLIC_WEBSITE_URL = 'https://your-site.com'"
Write-Host "  npm run start"
Write-Host ""
Write-Host "Optional:"
Write-Host "  npm run android"
Write-Host "  npm run ios"
Write-Host ""
Write-Host "Uninstall:"
Write-Host "  pwsh -File \"$TargetDir/scripts/uninstall-web-to-app-cli.ps1\" -TargetDir \"$TargetDir\""

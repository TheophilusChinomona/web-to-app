param(
  [switch]$DryRun,
  [string]$TargetDir = "$HOME/.web-to-app-cli"
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $TargetDir)) {
  Write-Host "Nothing to remove at: $TargetDir"
  exit 0
}

if ($DryRun) {
  Write-Host "[dry-run] Remove-Item -Recurse -Force \"$TargetDir\""
} else {
  Remove-Item -Recurse -Force "$TargetDir"
  Write-Host "✅ Removed: $TargetDir"
}

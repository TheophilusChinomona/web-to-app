#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=0
TARGET_DIR="${WEB_TO_APP_CLI_DIR:-$HOME/.web-to-app-cli}"

print_help() {
  cat <<USAGE
Uninstall web-to-app CLI setup

Usage:
  uninstall-web-to-app-cli.sh [options]

Options:
  --dry-run              Print actions without executing
  --target-dir <path>    Install location (default: ~/.web-to-app-cli)
  -h, --help             Show this help
USAGE
}

run() {
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "[dry-run] $*"
  else
    eval "$@"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --target-dir) TARGET_DIR="$2"; shift 2 ;;
    -h|--help) print_help; exit 0 ;;
    *) echo "Unknown option: $1"; print_help; exit 1 ;;
  esac
done

if [[ ! -d "$TARGET_DIR" ]]; then
  echo "Nothing to remove at: $TARGET_DIR"
  exit 0
fi

run "rm -rf \"$TARGET_DIR\""
echo "✅ Removed: $TARGET_DIR"

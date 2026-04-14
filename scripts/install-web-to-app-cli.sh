#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=0
FORCE=0
TARGET_DIR="${WEB_TO_APP_CLI_DIR:-$HOME/.web-to-app-cli}"
REPO_URL="${WEB_TO_APP_CLI_REPO:-https://github.com/TheophilusChinomona/web-to-app.git}"
BRANCH="${WEB_TO_APP_CLI_BRANCH:-expo-cross-platform}"

print_help() {
  cat <<USAGE
Install web-to-app CLI + Expo wrapper tooling

Usage:
  install-web-to-app-cli.sh [options]

Options:
  --dry-run              Print actions without executing
  --force                Remove existing target dir first
  --target-dir <path>    Install location (default: ~/.web-to-app-cli)
  --repo <url>           Git repo URL
  --branch <name>        Branch/tag/commit to checkout (default: expo-cross-platform)
  -h, --help             Show this help

Examples:
  curl -fsSL <RAW_SCRIPT_URL> | bash
  curl -fsSL <RAW_SCRIPT_URL> | bash -s -- --dry-run
USAGE
}

log() { echo "[install] $*"; }
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
    --force) FORCE=1; shift ;;
    --target-dir) TARGET_DIR="$2"; shift 2 ;;
    --repo) REPO_URL="$2"; shift 2 ;;
    --branch) BRANCH="$2"; shift 2 ;;
    -h|--help) print_help; exit 0 ;;
    *) echo "Unknown option: $1"; print_help; exit 1 ;;
  esac
done

for cmd in git node npm; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "Missing dependency: $cmd"; exit 1; }
done

if [[ -d "$TARGET_DIR" ]]; then
  if [[ "$FORCE" == "1" ]]; then
    log "Removing existing directory: $TARGET_DIR"
    run "rm -rf \"$TARGET_DIR\""
  else
    echo "Target directory already exists: $TARGET_DIR"
    echo "Re-run with --force or set WEB_TO_APP_CLI_DIR"
    exit 1
  fi
fi

log "Cloning $REPO_URL into $TARGET_DIR"
run "git clone --depth 1 --branch \"$BRANCH\" \"$REPO_URL\" \"$TARGET_DIR\""

log "Installing Expo wrapper dependencies"
run "cd \"$TARGET_DIR/expo-wrapper\" && npm install"

log "Running tests"
run "cd \"$TARGET_DIR/expo-wrapper\" && npm test -- --runInBand"

cat <<DONE

✅ web-to-app CLI setup complete.

Location:
  $TARGET_DIR

Next steps:
  cd "$TARGET_DIR/expo-wrapper"
  export EXPO_PUBLIC_WEBSITE_URL="https://your-site.com"
  npm run start

Optional:
  npm run android
  npm run ios

Uninstall:
  bash "$TARGET_DIR/scripts/uninstall-web-to-app-cli.sh" --target-dir "$TARGET_DIR"
DONE

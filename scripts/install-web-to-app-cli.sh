#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=0
FORCE=0
AUTO_INSTALL=1
TARGET_DIR="${WEB_TO_APP_CLI_DIR:-$HOME/.web-to-app-cli}"
REPO_URL="${WEB_TO_APP_CLI_REPO:-https://github.com/TheophilusChinomona/web-to-app.git}"
BRANCH="${WEB_TO_APP_CLI_BRANCH:-expo-cross-platform}"

print_help() {
  cat <<USAGE
Install web-to-app CLI + Expo wrapper tooling

Usage:
  install-web-to-app-cli.sh [options]

Options:
  --dry-run                Print actions without executing
  --force                  Remove existing target dir first
  --no-auto-install        Fail on missing dependencies instead of installing
  --target-dir <path>      Install location (default: ~/.web-to-app-cli)
  --repo <url>             Git repo URL
  --branch <name>          Branch/tag/commit to checkout (default: expo-cross-platform)
  -h, --help               Show this help

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

resolve_node_cmd() {
  if command -v node >/dev/null 2>&1; then
    echo "node"
  elif command -v nodejs >/dev/null 2>&1; then
    echo "nodejs"
  else
    echo ""
  fi
}

need_sudo() {
  [[ "${EUID:-$(id -u)}" -ne 0 ]]
}

install_with_apt() {
  local pkg="$1"
  if need_sudo; then
    run "sudo apt-get update"
    run "sudo apt-get install -y $pkg"
  else
    run "apt-get update"
    run "apt-get install -y $pkg"
  fi
}

install_with_brew() {
  local pkg="$1"
  run "brew install $pkg"
}

auto_install_cmd() {
  local cmd="$1"

  if command -v "$cmd" >/dev/null 2>&1; then
    return 0
  fi

  if [[ "$AUTO_INSTALL" != "1" ]]; then
    echo "Missing dependency: $cmd"
    return 1
  fi

  log "Missing dependency detected: $cmd"

  if command -v apt-get >/dev/null 2>&1; then
    case "$cmd" in
      git) install_with_apt git ;;
      node|npm)
        install_with_apt curl ca-certificates gnupg
        if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
          if need_sudo; then
            run "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
            run "sudo apt-get install -y nodejs"
          else
            run "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -"
            run "apt-get install -y nodejs"
          fi
        fi
        ;;
      *) echo "No apt installer mapping for: $cmd"; return 1 ;;
    esac
  elif command -v brew >/dev/null 2>&1; then
    case "$cmd" in
      git) install_with_brew git ;;
      node|npm) install_with_brew node ;;
      *) echo "No brew installer mapping for: $cmd"; return 1 ;;
    esac
  else
    echo "No supported package manager found to auto-install '$cmd' (supports apt-get or brew)."
    return 1
  fi

  if [[ "$DRY_RUN" == "1" ]]; then
    log "Dry-run: assuming dependency would be installed: $cmd"
    return 0
  fi

  if [[ "$cmd" == "node" ]]; then
    if ! command -v node >/dev/null 2>&1 && ! command -v nodejs >/dev/null 2>&1; then
      echo "Dependency install attempted, but neither 'node' nor 'nodejs' is available."
      return 1
    fi
  elif ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Dependency install attempted, but '$cmd' is still missing."
    return 1
  fi

  log "Dependency ready: $cmd"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --force) FORCE=1; shift ;;
    --no-auto-install) AUTO_INSTALL=0; shift ;;
    --target-dir) TARGET_DIR="$2"; shift 2 ;;
    --repo) REPO_URL="$2"; shift 2 ;;
    --branch) BRANCH="$2"; shift 2 ;;
    -h|--help) print_help; exit 0 ;;
    *) echo "Unknown option: $1"; print_help; exit 1 ;;
  esac
done

for cmd in git node npm; do
  auto_install_cmd "$cmd"
done

NODE_CMD="$(resolve_node_cmd)"
if [[ -z "$NODE_CMD" ]]; then
  echo "Node runtime not found after dependency setup."
  exit 1
fi

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

Detected node runtime command:
  $NODE_CMD

Uninstall:
  bash "$TARGET_DIR/scripts/uninstall-web-to-app-cli.sh" --target-dir "$TARGET_DIR"
DONE

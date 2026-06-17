#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/setup_macos_codefuse_jdk.sh [options]

Options:
  --version 21|17      Prefer a specific Homebrew OpenJDK version.
  --print-env          Print export commands for the selected JDK.
  --apply-symlink      Register the selected JDK with macOS using sudo ln -sfn.
  --zshrc-snippet      Print a ~/.zshrc snippet; does not modify files.
  --check              Run scripts/check_codefuse_java_env.py with the selected JDK.
  -h, --help           Show this help.

Default mode is dry-run. sudo is used only with --apply-symlink.
EOF
}

VERSION=""
PRINT_ENV=0
APPLY_SYMLINK=0
ZSHRC_SNIPPET=0
RUN_CHECK=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version)
      [[ $# -ge 2 ]] || { echo "error: --version needs 21 or 17" >&2; exit 2; }
      VERSION="$2"
      [[ "$VERSION" == "21" || "$VERSION" == "17" ]] || { echo "error: --version must be 21 or 17" >&2; exit 2; }
      shift 2
      ;;
    --print-env)
      PRINT_ENV=1
      shift
      ;;
    --apply-symlink)
      APPLY_SYMLINK=1
      shift
      ;;
    --zshrc-snippet)
      ZSHRC_SNIPPET=1
      shift
      ;;
    --check)
      RUN_CHECK=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "error: this helper is for macOS only" >&2
  exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"

detect_brew_prefix() {
  if command -v brew >/dev/null 2>&1; then
    brew --prefix
    return
  fi
  if [[ -d /opt/homebrew ]]; then
    printf '%s\n' /opt/homebrew
    return
  fi
  if [[ -d /usr/local ]]; then
    printf '%s\n' /usr/local
    return
  fi
  return 1
}

BREW_PREFIX="$(detect_brew_prefix)" || {
  echo "error: cannot find Homebrew prefix" >&2
  exit 1
}

if [[ -n "$VERSION" ]]; then
  FORMULAE=("openjdk@$VERSION")
else
  FORMULAE=("openjdk@21" "openjdk@17" "openjdk")
fi

SELECTED_FORMULA=""
SELECTED_JDK_BUNDLE=""
SELECTED_HOME=""

for formula in "${FORMULAE[@]}"; do
  candidate_bundle="$BREW_PREFIX/opt/$formula/libexec/openjdk.jdk"
  candidate_home="$candidate_bundle/Contents/Home"
  if [[ -x "$candidate_home/bin/java" && -x "$candidate_home/bin/javac" && -f "$candidate_home/lib/modules" ]]; then
    SELECTED_FORMULA="$formula"
    SELECTED_JDK_BUNDLE="$candidate_bundle"
    SELECTED_HOME="$candidate_home"
    break
  fi
done

if [[ -z "$SELECTED_HOME" ]]; then
  echo "error: no usable Homebrew OpenJDK was found under $BREW_PREFIX/opt" >&2
  echo "checked:" >&2
  for formula in "${FORMULAE[@]}"; do
    echo "  $BREW_PREFIX/opt/$formula/libexec/openjdk.jdk/Contents/Home" >&2
  done
  exit 1
fi

case "$SELECTED_FORMULA" in
  openjdk@21) SYMLINK_NAME="openjdk-21.jdk"; REQUIRE_VERSION="21" ;;
  openjdk@17) SYMLINK_NAME="openjdk-17.jdk"; REQUIRE_VERSION="17" ;;
  *) SYMLINK_NAME="openjdk.jdk"; REQUIRE_VERSION="" ;;
esac
SYMLINK_TARGET="/Library/Java/JavaVirtualMachines/$SYMLINK_NAME"

echo "Selected JDK: $SELECTED_FORMULA"
echo "JDK bundle:   $SELECTED_JDK_BUNDLE"
echo "JAVA_HOME:    $SELECTED_HOME"
echo

if [[ "$PRINT_ENV" -eq 1 ]]; then
  printf 'export JAVA_HOME="%s"\n' "$SELECTED_HOME"
  printf 'export PATH="$JAVA_HOME/bin:$PATH"\n'
  echo
fi

if [[ "$ZSHRC_SNIPPET" -eq 1 ]]; then
  cat <<EOF
# CodeFuse/Sparrow JDK type model discovery
export JAVA_HOME="$SELECTED_HOME"
export PATH="\$JAVA_HOME/bin:\$PATH"
EOF
  echo
fi

echo "Optional macOS registration command:"
printf 'sudo ln -sfn "%s" "%s"\n' "$SELECTED_JDK_BUNDLE" "$SYMLINK_TARGET"
echo

if [[ "$APPLY_SYMLINK" -eq 1 ]]; then
  sudo ln -sfn "$SELECTED_JDK_BUNDLE" "$SYMLINK_TARGET"
  /usr/libexec/java_home -V || true
  if [[ -n "$REQUIRE_VERSION" ]]; then
    /usr/libexec/java_home -v "$REQUIRE_VERSION" || true
  fi
else
  echo "Dry-run: symlink was not applied. Pass --apply-symlink to run sudo ln -sfn."
fi

if [[ "$RUN_CHECK" -eq 1 ]]; then
  echo
  if [[ -n "$REQUIRE_VERSION" ]]; then
    JAVA_HOME="$SELECTED_HOME" PATH="$SELECTED_HOME/bin:$PATH" \
      python3 "$REPO_ROOT/scripts/check_codefuse_java_env.py" \
        --require-version "$REQUIRE_VERSION" --require-modules
  else
    JAVA_HOME="$SELECTED_HOME" PATH="$SELECTED_HOME/bin:$PATH" \
      python3 "$REPO_ROOT/scripts/check_codefuse_java_env.py" --require-modules
  fi
fi

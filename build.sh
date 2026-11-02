#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/tools/scripts/build-common.sh"

usage() {
    cat <<'HELP'
Usage: ./build.sh [Debug|RelWithDebInfo|Release] [options]
Default build type: RelWithDebInfo. Names are case-insensitive.

Basic commands:
  ./build.sh                    Download dependencies, configure and build
  ./build.sh release            Build Release
  ./build.sh release --rebuild  Fresh configure and compile; reuse dependencies
  ./build.sh release --fresh    Delete all out/ and download/build everything
  ./run.sh release              Run the Release build
  ./build.sh help               Show this help (also --help or -h)

Options:
  -j, --jobs JOBS  Parallel jobs (default: 8, or POB_BUILD_JOBS)
  --test          Build and run native C++ regression tests
  --rebuild       Reset only the selected build directory
  --fresh         Reset all out/, including tools, other builds and installers
  --verbose, -v   Show full build output
  --plain         Disable colors and animation

Saved builds:
  Copy build XML files into ~/.local/share/Path of Building/Builds/
  Settings: ~/.local/share/Path of Building/Settings.xml
  An absolute XDG_DATA_HOME replaces ~/.local/share.
  The app's "Build save path" setting can override the builds folder.
  Saves outside out/ survive --rebuild and --fresh.

Output: out/build/<build type>/bin/    Logs: out/logs/
More help: README.md and docs/linux-build.md
HELP
}
if [[ "${1:-}" == help || "${1:-}" == --help || "${1:-}" == -h ]]; then usage; exit 0; fi
config=RelWithDebInfo
if (( $# )) && [[ "$1" != -* ]]; then config="$1"; shift; fi
pob_select_config "$config"
jobs="${POB_BUILD_JOBS:-8}"
ui_options=()
while (( $# )); do
    case "$1" in
        help|--help|-h) usage; exit 0 ;;
        --test) ui_options+=(--test); shift ;;
        --rebuild) ui_options+=(--rebuild); shift ;;
        --fresh) ui_options+=(--fresh); shift ;;
        --verbose|-v) ui_options+=(--verbose); shift ;;
        --plain) ui_options+=(--plain); shift ;;
        -j|--jobs)
            if (( $# < 2 )); then usage >&2; exit 2; fi
            jobs="$2"; shift 2 ;;
        *) usage >&2; exit 2 ;;
    esac
done
if [[ ! "$jobs" =~ ^[1-9][0-9]*$ ]]; then
    printf 'Job count must be a positive integer.\n' >&2; exit 2
fi
if ! command -v python3 >/dev/null 2>&1; then
    printf 'Missing host prerequisite: python3 (3.12+). See docs/linux-build.md.\n' >&2
    exit 1
fi
exec python3 "$POB_ROOT/tools/scripts/build.py" --config "$POB_CONFIG" --jobs "$jobs" "${ui_options[@]}"

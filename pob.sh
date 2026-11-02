#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat <<'HELP'
Path of Building for Linux

USAGE
  ./pob.sh <command> [options]

COMMANDS
  build                     Download dependencies, configure and compile
  test                      Build and run native C++ regression tests
  run                       Start the application
  help, --help, -h          Show this help

BUILD TYPE                  Applies to build, run and test; choose one
  --release                 Optimized build (default)
  --debug                   Debug symbols, assertions and startup diagnostics
  --relwithdebinfo          Optimized build with debug symbols

BUILD OPTIONS
  --rebuild                 Fresh configure and compile; keep cached downloads
  --fresh                   Delete all out/ and download/build everything again
  -j, --jobs JOBS           Parallel jobs (default: 8, or POB_BUILD_JOBS)
  -v, --verbose             Show full compilation output
  --plain                   Disable colors and animation

RUN OPTIONS
  -v, --verbose             Stream full runtime output alongside status
  --plain                   Disable colors and animation

EXAMPLES
  ./pob.sh build
  ./pob.sh run
  ./pob.sh test
  ./pob.sh build --debug
  ./pob.sh run --debug
  ./pob.sh build --rebuild
  ./pob.sh build --fresh
  ./pob.sh build --release -j 8 --verbose
  ./pob.sh run -- <application arguments>

  Use the same build type for build and run.
  Choose either --rebuild or --fresh. --fresh removes all build types,
  downloaded tools, dependencies, logs and generated installers in out/.

SAVED BUILDS AND SETTINGS
  Copy build XML files to   ~/.local/share/Path of Building/Builds/
  Settings file             ~/.local/share/Path of Building/Settings.xml

  An absolute XDG_DATA_HOME replaces ~/.local/share.
  The app's "Build save path" setting can override the builds folder.
  Rebuilding and deleting out/ preserve user data at these locations.

OUTPUT AND DOCUMENTATION
  Binaries                  out/build/<build type>/bin/
  Build logs                out/logs/
  Quick start               README.md
  Detailed guide            docs/linux-build.md
HELP
}
command_name="${1:-help}"
if (( $# )); then shift; fi
case "$command_name" in
    help|--help|-h) usage; exit 0 ;;
    build|run|test) ;;
    *) printf 'Unknown command: %s\nUse ./pob.sh help.\n' "$command_name" >&2; exit 2 ;;
esac
config=Release
selected_config=
options=()
while (( $# )); do
    case "$1" in
        help|--help|-h) usage; exit 0 ;;
        --release|--debug|--relwithdebinfo)
            if [[ -n "$selected_config" && "$selected_config" != "$1" ]]; then
                printf 'Choose only one build type.\n' >&2; exit 2
            fi
            selected_config="$1"
            case "$1" in
                --release) config=Release ;;
                --debug) config=Debug ;;
                --relwithdebinfo) config=RelWithDebInfo ;;
            esac
            shift ;;
        --)
            if [[ "$command_name" != run ]]; then
                printf 'Application arguments are only supported by run.\n' >&2; exit 2
            fi
            options+=("$@")
            break ;;
        -j|--jobs)
            if [[ "$command_name" == run || $# -lt 2 ]]; then
                printf '%s requires a job count and build or test.\n' "$1" >&2; exit 2
            fi
            options+=("$1" "$2"); shift 2 ;;
        --verbose|-v|--plain) options+=("$1"); shift ;;
        --rebuild|--fresh)
            if [[ "$command_name" == run ]]; then
                printf '%s is a build option.\n' "$1" >&2; exit 2
            fi
            options+=("$1"); shift ;;
        *) printf 'Unknown option: %s\nUse ./pob.sh help.\n' "$1" >&2; exit 2 ;;
    esac
done
case "$command_name" in
    build) exec "$root/build.sh" "$config" "${options[@]}" ;;
    test) exec "$root/build.sh" "$config" --test "${options[@]}" ;;
    run) exec "$root/run.sh" "$config" "${options[@]}" ;;
esac

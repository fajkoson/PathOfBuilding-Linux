#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/tools/scripts/build-common.sh"
if [[ "${1:-}" == help || "${1:-}" == --help || "${1:-}" == -h ]]; then
    cat <<'HELP'
Usage: ./run.sh [Debug|RelWithDebInfo|Release] [--verbose] [--plain] [-- application arguments]
Default: RelWithDebInfo. Build first using ./build.sh with the same build type.

  ./run.sh           Run the default build
  ./run.sh release   Run Release
  ./run.sh --verbose Show full runtime output
  ./run.sh help      Show this help (also --help or -h)

Saved builds: ~/.local/share/Path of Building/Builds/ (copy build XML files here)
Settings: ~/.local/share/Path of Building/Settings.xml
An absolute XDG_DATA_HOME replaces ~/.local/share.
The app's "Build save path" setting can override the builds folder.
Build commands and options: ./build.sh help
HELP
    exit 0
fi
config=RelWithDebInfo
if (( $# )) && [[ "$1" != -* ]]; then config="$1"; shift; fi
pob_select_config "$config"
ui_options=()
while (( $# )); do
    case "$1" in
        --verbose|-v|--plain) ui_options+=("$1"); shift ;;
        --) shift; break ;;
        *) printf 'Unknown run option: %s\nUse ./pob.sh help.\n' "$1" >&2; exit 2 ;;
    esac
done
binary="$POB_ROOT/out/build/$POB_CONFIG/bin/pob-linux"
if [[ ! -x "$binary" ]]; then
    printf 'Build %s first: ./build.sh %s\n' "$POB_CONFIG" "$POB_CONFIG" >&2; exit 1
fi
exec python3 "$POB_ROOT/tools/scripts/run.py" --config "$POB_CONFIG" "${ui_options[@]}" -- "$@"

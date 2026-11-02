#!/usr/bin/env bash
# Shared by the Linux entry points; executed by Bash even when called from fish.
POB_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"

pob_select_config() {
    case "${1,,}" in
        debug) POB_CONFIG=Debug; POB_PRESET=linux-debug ;;
        relwithdebinfo) POB_CONFIG=RelWithDebInfo; POB_PRESET=linux-relwithdebinfo ;;
        release) POB_CONFIG=Release; POB_PRESET=linux-release ;;
        *) printf 'Unknown build type: %s\nUse Debug, RelWithDebInfo, or Release.\n' "$1" >&2; return 2 ;;
    esac
}


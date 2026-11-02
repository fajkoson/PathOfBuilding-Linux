#!/usr/bin/env bash
set -euo pipefail
pob_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
    printf 'Bootstrap requires Python 3.12 or newer.\n' >&2
    exit 1
fi
exec python3 "$pob_root/tools/scripts/bootstrap.py" "$@"

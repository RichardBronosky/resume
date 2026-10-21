#!/usr/bin/env bash
# Stable, cwd-independent entrypoint for this checkout's tools.
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
exec python3 "$ROOT/tools/commands.py" "$@"

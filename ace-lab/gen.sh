#!/usr/bin/env bash
# Text -> instrumental. Runs generate.py inside ACE-Step's uv env.
#   ./gen.sh "warm bonobo-ish ambient, rhodes, vinyl crackle" --duration 60
set -euo pipefail
cd "$(dirname "$0")"
exec uv run --project "${ACE_ROOT:-vendor/ACE-Step}" python generate.py "$@"

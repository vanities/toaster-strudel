#!/usr/bin/env bash
# Reference track -> instrumental in that style. Runs style_of.py in ACE-Step's uv env.
#   ./style.sh ~/Music/track_i_like.mp3 "make it ambient" --strength 0.2
set -euo pipefail
cd "$(dirname "$0")"
exec uv run --project "${ACE_ROOT:-vendor/ACE-Step}" python style_of.py "$@"

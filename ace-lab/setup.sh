#!/usr/bin/env bash
# Install ACE-Step's environment so the ace-lab scripts can run.
#
# This runs `uv sync` inside the vendored repo (big first-time install: torch,
# mlx, etc.). Model WEIGHTS (~several GB) download separately on your first
# generation, into vendor/ACE-Step/checkpoints/.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d vendor/ACE-Step ]; then
  echo "[setup] cloning ACE-Step (code only)…"
  GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/ace-step/ACE-Step vendor/ACE-Step
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "[setup] uv not found. Install it: curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi

echo "[setup] uv sync in vendor/ACE-Step (large first-time install)…"
( cd vendor/ACE-Step && uv sync )

echo
echo "[setup] done. Next:"
echo "  ./gen.sh \"warm bonobo-ish ambient, rhodes, vinyl crackle, 82 bpm\""
echo "  ./style.sh ~/Music/a_track_you_like.mp3 \"make it ambient\" --strength 0.2"
echo "(first generation downloads the model weights — be patient.)"

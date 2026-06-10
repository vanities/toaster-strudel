#!/usr/bin/env bash
# Run ace-lab work on the 5090 box ("ssh pc") instead of the Mac.
#
#   ./remote.sh push                          # sync lab code+briefs+datasets -> box
#   ./remote.sh brief briefs/<n>.json [args]  # push, generate on the 5090, pull output
#   ./remote.sh train <dataset> [variant] [epochs]   # push, train LoRA on the 5090, pull adapter
#   ./remote.sh pull                          # pull box outputs -> out-pc/ + lora_output-pc/
#   ./remote.sh sh '<command>'                # arbitrary command in the box lab dir
#
# Box layout (already in place): lab at $RLAB, ACE-Step checkout at $RACE
# (ACE_ROOT env — same contract _ace.py / gen.sh / train_lora.sh honor locally).
# Outputs pull into out-pc/ and lora_output-pc/ so box runs never clobber Mac runs.
# Use the 5090 for: LoRA training (~3-5x faster, no MPS quirks), many-seed brief
# rolls, XL-variant work, and (future) Stable Audio 3 LoRA (CUDA-only).
set -euo pipefail
cd "$(dirname "$0")"

HOST="${ACE_REMOTE_HOST:-pc}"
RLAB="git/work/me/toaster-strudel/ace-lab"   # relative to $HOME on the box
RACE='$HOME/ace-step-lab/ACE-Step'

CMD="${1:?usage: ./remote.sh push|pull|brief|train|sh ...}"
shift || true

push() {
  echo "[remote] push lab -> $HOST:$RLAB"
  ssh "$HOST" "mkdir -p ~/$RLAB"
  rsync -az --info=stats1 \
    --exclude vendor/ --exclude .venv/ --exclude out*/ --exclude lora_output*/ \
    --exclude preprocessed/ --exclude __pycache__/ --exclude '*.wav' --exclude .DS_Store \
    ./ "$HOST:$RLAB/"
  rsync -az --info=stats1 datasets "$HOST:$RLAB/" 2>/dev/null || true
}

pull() {
  echo "[remote] pull $HOST outputs -> out-pc/ + lora_output-pc/"
  mkdir -p out-pc lora_output-pc
  rsync -az --info=stats1 "$HOST:$RLAB/out/" out-pc/ 2>/dev/null || true
  rsync -az --info=stats1 "$HOST:$RLAB/lora_output/" lora_output-pc/ 2>/dev/null || true
}

rrun() {  # run a command in the box lab dir with ACE_ROOT set
  # single argument = a full shell script (loops/pipes ok); multiple = one command
  local script
  if [ $# -eq 1 ]; then script="$1"; else script="$(printf '%q ' "$@")"; fi
  ssh "$HOST" "cd ~/$RLAB && export ACE_ROOT=$RACE && bash -lc $(printf '%q' "$script")"
}

case "$CMD" in
  push) push ;;
  pull) pull ;;
  sh)   rrun "$@" ;;
  brief)
    push
    t0=$(date +%s)
    rrun ./brief.sh "$@"
    echo "[remote] brief wall: $(( $(date +%s) - t0 ))s"
    pull ;;
  train)
    push
    rrun ./train_lora.sh "$@"
    pull
    echo "[remote] adapter(s) in lora_output-pc/" ;;
  *) echo "unknown: $CMD (use push|pull|brief|train|sh)"; exit 1 ;;
esac

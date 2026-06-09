#!/usr/bin/env bash
# LoRA fine-tune ACE-Step on a prepped instrumental dataset.
#
#   ./train_lora.sh <dataset-name>
#
# Two stages (per vendor/ACE-Step/docs/en/LoRA_Training_Tutorial.md):
#   1) preprocess audio+sidecars -> tensors
#   2) train the LoRA adapter
#
# HARDWARE: comfortable on a 16GB+ GPU. Doable on an M-series Mac but slow —
# for a real run, rent a GPU box, train there, copy the adapter back.
#
# NOTE: the `fixed` train command below is verbatim from train.py's usage.
# The preprocess invocation + hyperparameters (epochs, rank, lr) may need a
# tweak for your build — ACE-Step also ships an INTERACTIVE wizard you can run
# instead:  (cd vendor/ACE-Step && uv run python train.py)
# Read the tutorial before a long run.
set -euo pipefail
cd "$(dirname "$0")"

NAME="${1:?usage: ./train_lora.sh <dataset-name>}"
ACE="$PWD/vendor/ACE-Step"
DATASET="$PWD/datasets/$NAME"
TENSORS="$PWD/preprocessed/$NAME"
OUT="$PWD/lora_output/$NAME"

[ -d "$DATASET" ] || { echo "no dataset at $DATASET — run prep_dataset.py first"; exit 1; }
mkdir -p "$(dirname "$TENSORS")" "$(dirname "$OUT")"

echo "[lora] 1/2 preprocess: $DATASET -> $TENSORS"
uv run --project "$ACE" python "$ACE/train.py" \
  --audio-dir "$DATASET" --tensor-output "$TENSORS"

echo "[lora] 2/2 train LoRA -> $OUT"
uv run --project "$ACE" python "$ACE/train.py" fixed \
  --checkpoint-dir "$ACE/checkpoints" --model-variant turbo \
  --dataset-dir "$TENSORS" --output-dir "$OUT"

echo "[lora] done. Adapter in: $OUT"
echo "[lora] load it at generation time (see the tutorial: docs/pics/08_load_lora.jpg)."

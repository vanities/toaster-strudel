#!/usr/bin/env bash
# LoRA fine-tune ACE-Step 1.5 on a prepped instrumental dataset.
# VERIFIED WORKING ON APPLE SILICON (M4 Max, MPS, bf16) — 2026-06.
# NB: fp16 (the MPS auto-default) breaks twice: GradScaler can't unscale fp16
# grads, and fp16 weights produce non-finite grad norms (upstream #619).
# bf16 everywhere (--precision bf16 + patches/0001) is the working combo.
#
#   ./train_lora.sh <dataset-name> [variant] [epochs]
#   ./train_lora.sh handpicked base 200
#
# Three stages:
#   0) bridge:     datasets/<name>/ sidecars -> preprocessed/<name>.json
#   1) preprocess: audio + json -> tensors    (~15s/track, resumable; skipped if done)
#   2) train:      LoRA adapter -> lora_output/<name>-<variant>/final
#
# VARIANT: base (default — the recommended LoRA target: strongest plasticity,
#   per Side-Step's author; turbo is distillation-trained = harder to tune)
#   | turbo | sft | xl-base | xl-sft | xl-turbo.
#   Tensors are VARIANT-SPECIFIC (pass 2 runs the variant's condition encoder):
#   changing variant re-preprocesses into preprocessed/<name>-<variant>/.
#
# Hard-won notes (each of these silently broke an earlier version):
#   - `train.py` with NO subcommand opens the interactive WIZARD — it never
#     preprocesses. Preprocess lives behind `--preprocess` on the module
#     entrypoint (acestep.training_v2.cli.train_fixed).
#   - The CLI preprocess reads --dataset-json ONLY. It does NOT read
#     .caption.txt/.lyrics.txt sidecars (those are a Dataset-Builder concept) —
#     hence the bridge stage. .json sidecars (bpm/keyscale) ride along.
#   - Path safety: acestep validates paths against the CWD at import time —
#     run everything from ace-lab/ so datasets/ + preprocessed/ are in scope.
#   - macOS: --num-workers 0 (torch_shm_manager crash, upstream #619) and
#     --no-pin-memory (CUDA-only DMA opt). Keep clips <=180s: MPS step time
#     cliffs ~10-20x above that (1.4s/step @120s, 2.3 @180s, 22-44 @240s).
#   - At inference the MLX DiT IGNORES loaded LoRAs (weights are converted
#     once at init) — generate.py forces the PyTorch DiT when --lora is set.
#
# Monitor:  uv run --project vendor/ACE-Step tensorboard --logdir lora_output/<name>-<variant>/runs
# Use it:   ./gen.sh "caption..." --variant base --lora lora_output/<name>-<variant>/final --lora-scale 0.6
#           (the base-trained adapter also applies to turbo at scale 0.2-0.7)
set -euo pipefail
cd "$(dirname "$0")"

NAME="${1:?usage: ./train_lora.sh <dataset-name> [variant] [epochs]}"
VARIANT="${2:-base}"
EPOCHS="${3:-200}"
LAB="$PWD"
ACE="${ACE_ROOT:-$LAB/vendor/ACE-Step}"
PY="$ACE/.venv/bin/python"
DATASET="$LAB/datasets/$NAME"
JSON="$LAB/preprocessed/$NAME.json"
TENSORS="$LAB/preprocessed/$NAME-$VARIANT"
OUT="$LAB/lora_output/$NAME-$VARIANT"

[ -d "$DATASET" ] || { echo "no dataset at $DATASET — run build_corpus.py / prep_dataset.py first"; exit 1; }
[ -x "$PY" ] || { echo "no venv at $ACE/.venv — run ./setup.sh first"; exit 1; }
mkdir -p "$LAB/preprocessed" "$LAB/lora_output"

echo "[lora] 0/3 bridge: $DATASET -> $JSON"
"$PY" - "$DATASET" "$JSON" <<'PYEOF'
import sys, time
from acestep.training.path_safety import set_safe_root
set_safe_root("/")  # we pass absolute, pre-trusted paths
from acestep.training.dataset_builder import DatasetBuilder
dataset, out = sys.argv[1], sys.argv[2]
t0 = time.perf_counter()
b = DatasetBuilder()
samples, status = b.scan_directory(dataset)
print(f"[bridge] {status.splitlines()[0]} in {time.perf_counter()-t0:.1f}s")
print("[bridge]", b.save_dataset(out).splitlines()[0])
missing = [s.filename for s in b.samples if not s.caption]
if missing:
    print(f"[bridge] WARNING: {len(missing)} samples have NO caption (will fall back to filename)")
PYEOF

echo "[lora] 1/3 preprocess: $JSON -> $TENSORS (variant=$VARIANT, resumable)"
# --precision fp32 is LOAD-BEARING on MPS: the auto default (fp16) overflows
# the Qwen3 condition-encoder's outlier channels -> identical Inf values in
# every sample's encoder_hidden_states -> "non-finite grad norm" at step 0.
"$PY" -m acestep.training_v2.cli.train_fixed \
  --preprocess \
  --checkpoint-dir "$ACE/checkpoints" --model-variant "$VARIANT" \
  --dataset-json "$JSON" \
  --tensor-output "$TENSORS" \
  --max-duration 180 --precision fp32

echo "[lora] 2/3 train: $TENSORS -> $OUT (epochs=$EPOCHS, rank 64/alpha 128, lr 1e-4)"
"$PY" "$ACE/train.py" --yes fixed \
  --checkpoint-dir "$ACE/checkpoints" --model-variant "$VARIANT" \
  --dataset-dir "$TENSORS" --output-dir "$OUT" \
  --epochs "$EPOCHS" --save-every 10 \
  --lr 1e-4 --rank 64 --alpha 128 --dropout 0.1 \
  --batch-size 1 --gradient-accumulation 4 \
  --num-workers 0 --no-pin-memory --precision bf16

echo "[lora] done. Adapter: $OUT/final"
echo "[lora] try:  ./gen.sh \"your caption\" --variant $VARIANT --lora $OUT/final --lora-scale 0.6"

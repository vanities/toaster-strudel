#!/usr/bin/env bash
# Run a generation BRIEF — the crank-style path for generative audio.
#
#   ./brief.sh briefs/skee-mask-terminal.json [extra gen.sh args...]
#   ./brief.sh briefs/bonobo-kong.json --lora lora_output/handpicked-base/final --lora-scale 0.4 --seed 7
#
# A brief = ONE reference track's measured DNA turned into generation inputs
# (turn-the-crank discipline, ported):
#   caption  -> multi-dimension descriptor stack (style+instruments+timbre+production;
#               NO bpm/key in the caption — those go as params)
#   script   -> the arrangement as structure/energy tags (the lyrics field is the
#               TEMPORAL SCRIPT; bare "[Instrumental]" = no arrangement at all)
#   bpm/key/duration -> dedicated params from the reference card
#   targets  -> measure-wav.py goals for the iterate loop (informational)
#
# Defaults to --variant turbo for LISTENING (community consensus: distilled turbo
# out-renders the base teacher; base is the LoRA TRAINING target, not the ear path).
# Outputs land in out/briefs/<name>/.
set -euo pipefail
cd "$(dirname "$0")"

BRIEF="${1:?usage: ./brief.sh briefs/<name>.json [extra gen.sh args...]}"
shift || true
[ -f "$BRIEF" ] || { echo "no brief at $BRIEF"; exit 1; }

eval "$(python3 - "$BRIEF" <<'PYEOF'
import json, shlex, sys
b = json.load(open(sys.argv[1]))
print(f"NAME={shlex.quote(b['name'])}")
print(f"CAPTION={shlex.quote(b['caption'])}")
print(f"SCRIPT={shlex.quote(b['script'])}")
print(f"BPM={int(b['bpm'])}")
print(f"KEY={shlex.quote(b['key'])}")
print(f"DURATION={int(b['duration'])}")
PYEOF
)"

OUT="out/briefs/$NAME"
mkdir -p "$OUT"
echo "[brief] $NAME -> $OUT  (bpm=$BPM key=$KEY dur=${DURATION}s)"
./gen.sh "$CAPTION" \
  --script "$SCRIPT" \
  --bpm "$BPM" --key "$KEY" --duration "$DURATION" \
  --variant turbo \
  --out "$OUT" \
  "$@"
echo "[brief] targets (for measure-wav.py): $(python3 -c "import json,sys;print(json.load(open('$BRIEF')).get('targets',{}))")"

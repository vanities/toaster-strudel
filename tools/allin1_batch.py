#!/usr/bin/env python3
"""Run All-In-One (allin1) over the reference tracks → functional section labels.

Runs on the GPU box's venv-allin1 (CPU torch — natten 0.14.6's ABI can't move to
the Blackwell CUDA build). Writes the results JSON incrementally and is
resumable (allin1 also caches its demix), so an interrupted run picks up where
it left off.

    ~/venv-allin1/bin/python tools/allin1_batch.py [manifest.json] [out.json]
"""
import json
import sys
from pathlib import Path

import allin1

mani_path = sys.argv[1] if len(sys.argv) > 1 else "tools/pc-manifest.json"
out_path = sys.argv[2] if len(sys.argv) > 2 else str(Path.home() / "allin1-results.json")

mani = json.loads(Path(mani_path).read_text())
done = {}
if Path(out_path).exists():
    for r in json.loads(Path(out_path).read_text()):
        done[r["label"]] = r

out = []
for i, e in enumerate(mani, 1):
    if e["label"] in done:
        out.append(done[e["label"]])
        print(f"[{i}/{len(mani)}] cached {e['label']}", flush=True)
        continue
    try:
        r = allin1.analyze(e["path"], device="cpu")
        segs = [[round(s.start, 3), round(s.end, 3), s.label] for s in r.segments]
        out.append({"label": e["label"], "path": e["path"], "bpm": r.bpm, "segments": segs})
        print(f"[{i}/{len(mani)}] OK {e['label']} — {len(segs)} segs: {[s[2] for s in segs]}", flush=True)
    except Exception as ex:
        print(f"[{i}/{len(mani)}] ERR {e['label']}: {repr(ex)[:180]}", flush=True)
    Path(out_path).write_text(json.dumps(out, indent=2))

print(f"done: {len(out)}/{len(mani)} -> {out_path}", flush=True)

#!/usr/bin/env python3
"""Augment analysis cards with BTC large-vocabulary chords.

transcribe.py writes cards with chroma-template (maj/min) chords. This pass
replaces them with BTC transformer chords (maj7/min7/7/dim/aug/sus/...), reusing
the sections already in each card — no demucs / transcription recompute. The BTC
model loads once and is reused across all tracks. Runs in the BTC venv:

    tools/.venv-btc/bin/python tools/augment_chords.py [--out references/analysis] [--only SUBSTR]
"""
import argparse
import json
import sys
from pathlib import Path

import torch
from btc_chords import load_model, chords as btc_chords
from transcribe import render_card, collapse, slugify

CACHE = Path(__file__).resolve().parent / ".cache-stems"

# BTC large-voca quality -> compact display (Cm7, Abmaj7, F7, Gsus4, ...)
QMAP = {"maj": "", "min": "m", "dim": "dim", "aug": "aug", "min6": "m6", "maj6": "6",
        "min7": "m7", "minmaj7": "mM7", "maj7": "maj7", "7": "7", "dim7": "dim7",
        "hdim7": "m7b5", "sus2": "sus2", "sus4": "sus4"}


def norm(lab: str) -> str:
    if lab in ("N", "X", None, ""):
        return "~"
    if ":" not in lab:
        return lab  # bare root = major triad
    root, q = lab.split(":", 1)
    return root + QMAP.get(q, q)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("references/analysis"))
    ap.add_argument("--only", default=None, help="substring filter on card label")
    ap.add_argument("--force", action="store_true", help="re-run even if already BTC")
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"loading BTC large-voca model on {device}…", file=sys.stderr)
    model_cfg = load_model(device)

    cards = sorted(p for p in args.out.rglob("*.json") if "_cache" not in p.parts)
    print(f"augmenting {len(cards)} cards with BTC chords", file=sys.stderr)
    ok = 0
    for jp in cards:
        r = json.loads(jp.read_text())
        if args.only and args.only.lower() not in r["label"].lower():
            continue
        if r.get("chord_method") == "btc" and not args.force:
            continue  # already upgraded — idempotent re-runs only touch new cards
        audio = Path(r["file"])
        if not audio.exists():
            print(f"  MISSING audio: {r['label']}", file=sys.stderr)
            continue
        try:
            raw = btc_chords(audio, device, model_cfg=model_cfg)
        except Exception as ex:
            print(f"  ERR {r['label']}: {ex}", file=sys.stderr)
            continue
        timed = [(s, e, norm(c)) for s, e, c in raw]
        # cache the raw timed chords so augment_sections can re-bucket them per allin1 section
        cbf = CACHE / slugify(r["label"]) / "btc_chords.json"
        cbf.parent.mkdir(parents=True, exist_ok=True)
        cbf.write_text(json.dumps([[round(s, 3), round(e, 3), c] for s, e, c in raw]))
        r["chord_method"] = "btc"
        r["chords"] = collapse([c for _s, _e, c in timed if c != "~"])[:24]
        for sec in r.get("sections", []):
            inseg = [c for s, _e, c in timed if sec["start"] <= s < sec["end"] and c != "~"]
            sec["chords"] = collapse(inseg)[:8]
        jp.write_text(json.dumps(r, indent=2))
        jp.with_suffix(".md").write_text(render_card(r))
        ok += 1
        print(f"  ✓ {r['label']}: {' '.join(r['chords'][:8])}", file=sys.stderr)
    print(f"\n  augmented {ok} cards", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

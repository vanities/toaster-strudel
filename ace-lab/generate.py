#!/usr/bin/env python3
"""Text -> INSTRUMENTAL music with ACE-Step 1.5 (no vocals, ever).

  ./gen.sh "warm bonobo-ish ambient, rhodes, vinyl crackle, 82 bpm"
  ./gen.sh "lush downtempo pad, lydian, hazy" --duration 90 --bpm 80 --key "F# minor"

The prompt is the *caption* (what you want it to sound like). instrumental=True
forces an instrumental result regardless of anything else.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from _ace import generate  # sets up sys.path for `acestep`


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prompt", help="caption: what it should sound like")
    ap.add_argument("--duration", type=float, default=60.0, help="seconds (10-600)")
    ap.add_argument("--bpm", type=int, default=None)
    ap.add_argument("--key", default="", help='e.g. "F# minor", "C major"')
    ap.add_argument("--steps", type=int, default=8, help="diffusion steps (8 = turbo)")
    ap.add_argument("--seed", type=int, default=-1, help="-1 = random")
    ap.add_argument("--lora", default=None, help="trained LoRA adapter dir (e.g. lora_output/downtempo/final)")
    ap.add_argument("--lora-scale", type=float, default=1.0, help="LoRA influence, 0-1")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "out" / "text2music"))
    args = ap.parse_args()

    logging.basicConfig(level="INFO", format="%(message)s")
    from acestep.inference import GenerationParams

    params = GenerationParams(
        task_type="text2music",
        caption=args.prompt,
        lyrics="[Instrumental]",
        instrumental=True,
        bpm=args.bpm,
        keyscale=args.key,
        vocal_language="unknown",
        duration=args.duration,
        inference_steps=args.steps,
        seed=args.seed,
        thinking=True,
    )
    generate(params, args.out, lora_path=args.lora, lora_scale=args.lora_scale)


if __name__ == "__main__":
    main()

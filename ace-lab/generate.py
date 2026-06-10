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

from _ace import VARIANTS, generate, set_variant, variant_defaults  # sets up sys.path for `acestep`


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prompt", help="caption: what it should sound like")
    ap.add_argument("--variant", default="turbo", choices=VARIANTS,
                    help="DiT: turbo=fast/8-step, base/sft=quality/50-step, xl-*=4B (default: turbo)")
    ap.add_argument("--duration", type=float, default=60.0, help="seconds (10-600)")
    ap.add_argument("--bpm", type=int, default=None)
    ap.add_argument("--key", default="", help='e.g. "F# minor", "C major"')
    ap.add_argument("--steps", type=int, default=None, help="diffusion steps (default: variant-correct — 8 turbo / 50 base+sft)")
    ap.add_argument("--shift", type=float, default=None, help="timestep shift (default: variant-correct — 3.0 turbo / 1.0 base+sft; mismatch = garbled output)")
    ap.add_argument("--guidance", type=float, default=None, help="CFG scale, base/sft only (default 7.0; sane 5-9, >9 harsh; turbo ignores)")
    ap.add_argument("--dcw", action="store_true", help="enable experimental DCW correction (default OFF — it garbles output on this setup)")
    ap.add_argument("--script", default=None,
                    help="arrangement script: structure/energy tags fed as the lyrics field "
                         "(file path or inline string). The temporal plan of the piece — e.g. "
                         '"[Intro - sparse rhodes]\\n[Build - breakbeat layers in]\\n[Drop]\\n'
                         '[Breakdown - ambient]\\n[Outro - fade out]". instrumental=True still '
                         "guarantees no vocals; tags steer the 5Hz LM's plan. Default: bare [Instrumental].")
    ap.add_argument("--seed", type=int, default=-1, help="-1 = random")
    ap.add_argument("--lora", default=None, help="trained LoRA adapter dir (e.g. lora_output/handpicked-base/final)")
    ap.add_argument("--lora-scale", type=float, default=0.6, help="LoRA influence; 0.2-0.7 recommended (1.0 often overcooks)")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "out"))
    args = ap.parse_args()

    logging.basicConfig(level="INFO", format="%(message)s")
    cfg = set_variant(args.variant)  # must happen before _ace loads the DiT
    dflt = variant_defaults(cfg)
    steps = args.steps if args.steps is not None else dflt["steps"]
    shift = args.shift if args.shift is not None else dflt["shift"]
    guidance = args.guidance if args.guidance is not None else dflt["guidance"]
    lyrics = "[Instrumental]"
    if args.script:
        s = args.script
        # only probe the filesystem for short, single-line values — Path.exists()
        # raises OSError (name too long) on a full inline script
        if "\n" not in s and len(s) < 250 and Path(s).expanduser().exists():
            lyrics = Path(s).expanduser().read_text(encoding="utf-8").strip()
        else:
            lyrics = s.replace("\\n", "\n")
        logging.getLogger("ace-lab").info("[gen] arrangement script: %d lines", lyrics.count("\n") + 1)
    logging.getLogger("ace-lab").info(
        "[gen] variant=%s steps=%d shift=%.1f guidance=%.1f", args.variant, steps, shift, guidance)
    from acestep.inference import GenerationParams

    params = GenerationParams(
        task_type="text2music",
        caption=args.prompt,
        lyrics=lyrics,
        instrumental=True,
        bpm=args.bpm,
        keyscale=args.key,
        vocal_language="unknown",
        duration=args.duration,
        inference_steps=steps,
        shift=shift,
        guidance_scale=guidance,
        dcw_enabled=args.dcw,
        seed=args.seed,
        thinking=True,
    )
    generate(params, args.out, lora_path=args.lora, lora_scale=args.lora_scale)


if __name__ == "__main__":
    main()

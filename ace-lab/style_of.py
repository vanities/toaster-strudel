#!/usr/bin/env python3
"""Generate INSTRUMENTAL music in the style of a reference track (ACE-Step "cover").

This is the "feed a song I like, do it in that vibe" feature — like Suno's Cover.

  ./style.sh ~/Music/some_track_i_love.mp3 "make it ambient, keep the mood"
  ./style.sh ref.wav "downtempo" --strength 0.2 --duration 60

--strength = audio_cover_strength (0.0-1.0):
  ~0.2  -> STYLE TRANSFER  (take the vibe, reinvent it)   [default]
  ~0.8  -> CLOSE COVER     (stay near the reference)
(The inference.py docstring: "set smaller (0.2) for style transfer tasks.")
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from _ace import VARIANTS, generate, set_variant, variant_defaults  # sets up sys.path for `acestep`


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reference", help="audio file to take the style from")
    ap.add_argument("prompt", nargs="?", default="", help="optional caption to steer it")
    ap.add_argument("--strength", type=float, default=0.2, help="0.2=style transfer, 0.8=close cover")
    ap.add_argument("--variant", default="turbo", choices=VARIANTS,
                    help="DiT: turbo=fast/8-step, base/sft=quality/50-step, xl-*=4B (default: turbo)")
    ap.add_argument("--duration", type=float, default=-1.0, help="seconds; -1 = match/auto")
    ap.add_argument("--steps", type=int, default=None, help="diffusion steps (default: variant-correct)")
    ap.add_argument("--shift", type=float, default=None, help="timestep shift (default: variant-correct)")
    ap.add_argument("--guidance", type=float, default=None, help="CFG scale, base/sft only (default 7.0)")
    ap.add_argument("--seed", type=int, default=-1)
    ap.add_argument("--lora", default=None, help="trained LoRA adapter dir")
    ap.add_argument("--lora-scale", type=float, default=0.6, help="LoRA influence; 0.2-0.7 recommended")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "out"))
    args = ap.parse_args()

    ref = Path(args.reference).expanduser().resolve()
    if not ref.exists():
        sys.exit(f"reference audio not found: {ref}")

    logging.basicConfig(level="INFO", format="%(message)s")
    cfg = set_variant(args.variant)  # must happen before _ace loads the DiT
    dflt = variant_defaults(cfg)
    steps = args.steps if args.steps is not None else dflt["steps"]
    shift = args.shift if args.shift is not None else dflt["shift"]
    guidance = args.guidance if args.guidance is not None else dflt["guidance"]
    logging.getLogger("ace-lab").info(
        "[style] variant=%s strength=%.2f steps=%d shift=%.1f guidance=%.1f",
        args.variant, args.strength, steps, shift, guidance)
    from acestep.inference import GenerationParams

    # task_type="cover" + reference_audio + audio_cover_strength is the documented
    # style-transfer path. If "cover" wants src_audio instead on your build, swap
    # reference_audio -> src_audio (see acestep/inference.py:79-85).
    params = GenerationParams(
        task_type="cover",
        reference_audio=str(ref),
        audio_cover_strength=args.strength,
        caption=args.prompt,
        lyrics="[Instrumental]",
        instrumental=True,
        duration=args.duration,
        inference_steps=steps,
        shift=shift,
        guidance_scale=guidance,
        seed=args.seed,
        thinking=True,
    )
    generate(params, args.out, lora_path=args.lora, lora_scale=args.lora_scale)


if __name__ == "__main__":
    main()

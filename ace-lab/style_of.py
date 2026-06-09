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

from _ace import generate  # sets up sys.path for `acestep`


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reference", help="audio file to take the style from")
    ap.add_argument("prompt", nargs="?", default="", help="optional caption to steer it")
    ap.add_argument("--strength", type=float, default=0.2, help="0.2=style transfer, 0.8=close cover")
    ap.add_argument("--duration", type=float, default=-1.0, help="seconds; -1 = match/auto")
    ap.add_argument("--seed", type=int, default=-1)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "out"))
    args = ap.parse_args()

    ref = Path(args.reference).expanduser().resolve()
    if not ref.exists():
        sys.exit(f"reference audio not found: {ref}")

    logging.basicConfig(level="INFO", format="%(message)s")
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
        seed=args.seed,
        thinking=True,
    )
    generate(params, args.out)


if __name__ == "__main__":
    main()

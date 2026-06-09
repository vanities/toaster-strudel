#!/usr/bin/env python3
"""Prep an INSTRUMENTAL LoRA dataset for ACE-Step.

Takes a folder of audio you want to tune the model's taste on, and writes the
per-file sidecars ACE-Step's trainer expects (see
vendor/ACE-Step/docs/en/LoRA_Training_Tutorial.md):

    <name>.lyrics.txt   -> "[Instrumental]"
    <name>.caption.txt  -> your vibe description

Optionally chops long tracks into clips (more training examples from fewer songs).

  python3 prep_dataset.py ~/Music/bonobo_faves --caption "warm organic downtempo, rhodes, vinyl crackle"
  python3 prep_dataset.py ./corpus --caption "ambient pad, hazy" --chop 30

Output: ace-lab/datasets/<name>/  ->  then run ./train_lora.sh <name>

(needs `ffmpeg` on PATH only if you pass --chop)
"""

from __future__ import annotations

import argparse
import logging
import shutil
import subprocess
from pathlib import Path

AUDIO_EXT = {".mp3", ".wav", ".flac", ".ogg", ".opus", ".m4a"}
log = logging.getLogger("prep")


def _sidecars(audio: Path, caption: str) -> None:
    base = audio.with_suffix("")  # strip ext: out/song1.mp3 -> out/song1
    Path(str(base) + ".lyrics.txt").write_text("[Instrumental]\n", encoding="utf-8")
    Path(str(base) + ".caption.txt").write_text(caption.strip() + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", help="folder of audio to train on")
    ap.add_argument("--caption", required=True, help="vibe description applied to every clip")
    ap.add_argument("--name", default=None, help="dataset name (default: source folder name)")
    ap.add_argument("--chop", type=float, default=0.0, help="chop into N-second clips (0 = whole tracks)")
    args = ap.parse_args()

    logging.basicConfig(level="INFO", format="%(message)s")
    src = Path(args.src).expanduser().resolve()
    name = args.name or src.name
    out = Path(__file__).resolve().parent / "datasets" / name
    out.mkdir(parents=True, exist_ok=True)

    files = [p for p in sorted(src.iterdir()) if p.suffix.lower() in AUDIO_EXT]
    if not files:
        raise SystemExit(f"no audio files in {src}")

    n = 0
    for f in files:
        stem = f.stem.replace(" ", "_")
        ext = f.suffix.lower()
        if args.chop > 0:
            log.info("[prep] chopping %s into %.0fs clips", f.name, args.chop)
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(f), "-f", "segment", "-segment_time", str(args.chop),
                 "-c", "copy", str(out / f"{stem}_%03d{ext}")],
                check=False, capture_output=True,
            )
            clips = sorted(out.glob(f"{stem}_*{ext}"))
        else:
            dst = out / f"{stem}{ext}"
            shutil.copy(f, dst)
            clips = [dst]
        for c in clips:
            _sidecars(c, args.caption)
            n += 1

    log.info("[prep] %d clip(s) -> %s", n, out)
    log.info("[prep] next: ./train_lora.sh %s", name)


if __name__ == "__main__":
    main()

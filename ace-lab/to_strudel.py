#!/usr/bin/env python3
"""Bridge: drop an ACE-Step output into toaster-strudel as a playable sample.

Copies a generated .wav into tracks/_ace_samples/<name>/ and prints the Strudel
snippet to load + chop it — so you can sequence the AI-generated texture in code
(granular pads, chopped beds, etc.) instead of using it as a finished track.

  python3 to_strudel.py out/text2music/SOMETHING.wav --name acepad

NOTE: browser Strudel needs the file served over http (the toaster-strudel dev
server). Exact URL depends on how the server exposes tracks/ — adjust the
printed `samples(...)` URL if needed. This is the experimental hybrid path.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

TS_ROOT = Path(__file__).resolve().parents[1]  # toaster-strudel/


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("wav", help="generated .wav to import")
    ap.add_argument("--name", default="acesample", help="sample name to use in Strudel")
    args = ap.parse_args()

    src = Path(args.wav).expanduser().resolve()
    if not src.exists():
        raise SystemExit(f"not found: {src}")

    dst_dir = TS_ROOT / "tracks" / "_ace_samples" / args.name
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / f"{args.name}.wav"
    shutil.copy(src, dst)

    rel = dst.relative_to(TS_ROOT)
    print(f"copied -> {dst}")
    print("\nIn a Strudel track:")
    print(f'  samples({{ {args.name}: "/{rel}" }})   // adjust URL to your dev server')
    print(f'  s("{args.name}").loopAt(4).gain(0.7)            // or .chop(16), .speed(), granular…')


if __name__ == "__main__":
    main()

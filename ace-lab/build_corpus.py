#!/usr/bin/env python3
"""Build an instrumental LoRA corpus from a manifest of full-quality audio files.

Reads a text manifest (one audio path per line; blank / #-comment lines ignored),
copies each track into ace-lab/datasets/<name>/, and writes the ACE-Step training
sidecars next to it:
    <track>.lyrics.txt   -> "[Instrumental]"
    <track>.caption.txt  -> a per-artist caption (matched from the path)

Using full tracks (not Demucs stem-mixdowns) = clean source, no separation artifacts.

  python3 build_corpus.py --manifest corpora/handpicked.txt --name handpicked

Output: ace-lab/datasets/<name>/  ->  rsync to box, then preprocess + train.
"""

from __future__ import annotations

import argparse
import logging
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
log = logging.getLogger("corpus")

# artist substring (lowercase, found in the path) -> training caption.
# Longest keys are matched first so "carbon based lifeforms" wins over nothing, etc.
CAPTIONS = {
    "carbon based lifeforms": "deep evolving ambient, lush analog pads, slow atmospheric electronica, instrumental",
    "floating points": "modular electronic jazz, analog synths, intricate live rhythms, cinematic builds, instrumental",
    "skee mask": "atmospheric IDM and breakbeat techno, dub chords, ambient pads, instrumental",
    "thrupence": "organic ambient, field recordings, textured loops, warm lo-fi, instrumental",
    "bonobo": "warm organic downtempo, rhodes, upright bass, live drums, vinyl crackle, layered samples, instrumental",
    "djrum": "genre-fluid electronic, jazzy chopped breakbeat into ambient, intricate sampled texture, instrumental",
    "rone": "emotive french electronica, lush analog synths, melodic techno, instrumental",
    "home": "nostalgic synthwave, warm analog pads, dreamy retro-futurist, instrumental",
}


def caption_for(path_str: str) -> tuple[str, str]:
    low = path_str.lower()
    for artist, cap in sorted(CAPTIONS.items(), key=lambda kv: -len(kv[0])):
        if artist in low:
            return artist, cap
    return "misc", "atmospheric instrumental electronic music, instrumental"


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", required=True, help="text file of audio paths")
    ap.add_argument("--name", required=True, help="dataset name, e.g. handpicked")
    args = ap.parse_args()
    logging.basicConfig(level="INFO", format="%(message)s")

    manifest = Path(args.manifest)
    if not manifest.is_absolute():
        manifest = HERE / manifest
    if not manifest.exists():
        sys.exit(f"manifest not found: {manifest}")

    lines = [ln.strip() for ln in manifest.read_text(encoding="utf-8").splitlines()
             if ln.strip() and not ln.lstrip().startswith("#")]
    out = HERE / "datasets" / args.name
    out.mkdir(parents=True, exist_ok=True)

    n, missing = 0, []
    for line in lines:
        src = Path(line).expanduser()
        if not src.exists():
            missing.append(line)
            continue
        artist, cap = caption_for(line)
        name = f"{slug(artist)}-{slug(src.stem)}"
        dst = out / f"{name}{src.suffix.lower()}"
        k = 1
        while dst.exists():
            dst = out / f"{name}-{k}{src.suffix.lower()}"
            k += 1
        shutil.copy(src, dst)
        base = dst.with_suffix("")
        Path(str(base) + ".lyrics.txt").write_text("[Instrumental]\n", encoding="utf-8")
        Path(str(base) + ".caption.txt").write_text(cap + "\n", encoding="utf-8")
        n += 1
        log.info("  %-44s [%s]", src.name[:44], artist)

    if missing:
        log.warning("\n[corpus] %d MISSING (check paths):", len(missing))
        for m in missing:
            log.warning("  %s", m)
    log.info("\n[corpus] %d/%d tracks -> %s", n, len(lines), out)
    if n:
        log.info("[corpus] next: rsync to box, then preprocess + train_lora.sh %s", args.name)


if __name__ == "__main__":
    main()

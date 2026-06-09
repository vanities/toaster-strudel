#!/usr/bin/env python3
"""Build an instrumental LoRA corpus from the stem-separated artist kit.

For each track under tools/.cache-stems matching the chosen artist prefixes, mix
the NON-VOCAL stems (other + bass + drums, vocals dropped) into one instrumental
wav, and write the ACE-Step training sidecars:
    <name>.lyrics.txt  -> "[Instrumental]"
    <name>.caption.txt -> a per-artist caption (from the style-* lenses)

  python3 build_corpus.py downtempo --artists bonobo kiasmos boards-of-canada bibio rone thrupence
  python3 build_corpus.py vgm --artists mitsuda uematsu nishiki shimomura jeremy-soule matt-uelmen david-wise sonic void-stranger

Output: ace-lab/datasets/<name>/   ->   ./train_lora.sh <name>
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TS_ROOT = HERE.parent
STEMS = TS_ROOT / "tools" / ".cache-stems"
log = logging.getLogger("corpus")

# per-artist captions, distilled from the style-* production lenses
CAPTIONS = {
    "bonobo": "warm organic downtempo, rhodes, upright bass, live drums, vinyl crackle, layered samples, instrumental",
    "kiasmos": "minimal melodic techno, hypnotic piano, deep sub bass, subtle strings, shuffled hats, instrumental",
    "boards-of-canada": "nostalgic analog hauntology, detuned tape-warped synths, woozy pads, dusty downtempo beats, instrumental",
    "bibio": "tape-warped folktronica, finger-picked guitar loops, cassette hiss, sun-faded warmth, instrumental",
    "rone": "emotive french electronica, lush analog synths, melodic techno, cinematic pads, instrumental",
    "thrupence": "organic ambient, field recordings, textured loops, warm lo-fi, instrumental",
    # VGM
    "mitsuda": "wistful melodic JRPG score, celtic-tinged, accordion and strings, SNES, instrumental",
    "uematsu": "epic orchestral JRPG score, sweeping melodies, Final Fantasy style, instrumental",
    "nishiki": "lively orchestral JRPG battle score, Octopath style, dynamic strings and brass, instrumental",
    "shimomura": "emotive orchestral game score, piano and strings, instrumental",
    "jeremy-soule": "sweeping fantasy orchestral score, Skyrim style, choirs, horns, ambient strings, instrumental",
    "matt-uelmen": "dark ambient gothic guitar, Diablo Tristram style, sparse and haunting, instrumental",
    "david-wise": "atmospheric SNES soundtrack, Donkey Kong Country style, ambient pads and percussion, instrumental",
    "sonic": "upbeat retro 16-bit game music, Sega Genesis style, bright synth leads, funky bass, instrumental",
    "void-stranger": "melodic indie chiptune-leaning game music, lo-fi synths, instrumental",
}


def caption_for(track_dir_name: str, artists: list[str]) -> str:
    # longest matching artist prefix wins (handles 'boards-of-canada' vs 'bonobo')
    best = ""
    for a in sorted(artists, key=len, reverse=True):
        if track_dir_name.startswith(a) and a in CAPTIONS:
            best = CAPTIONS[a]
            break
    return best or "instrumental music, atmospheric"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", help="dataset name, e.g. downtempo / vgm")
    ap.add_argument("--artists", nargs="+", required=True, help="artist prefixes to include")
    args = ap.parse_args()
    logging.basicConfig(level="INFO", format="%(message)s")

    if not STEMS.exists():
        sys.exit(f"no stems dir at {STEMS}")
    out = HERE / "datasets" / args.name
    out.mkdir(parents=True, exist_ok=True)

    tracks = sorted(d for d in STEMS.iterdir()
                    if d.is_dir() and any(d.name.startswith(a) for a in args.artists))
    if not tracks:
        sys.exit(f"no tracks matched artists={args.artists}")

    n = 0
    for t in tracks:
        sub = next((p for p in (t / "htdemucs").glob("*") if p.is_dir()), None)
        if not sub:
            log.info("  skip (no htdemucs stems): %s", t.name)
            continue
        stems = {s: sub / f"{s}.wav" for s in ("other", "bass", "drums")}
        if not all(p.exists() for p in stems.values()):
            log.info("  skip (missing stems): %s", t.name)
            continue
        dst = out / f"{t.name}.wav"
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(stems["other"]), "-i", str(stems["bass"]), "-i", str(stems["drums"]),
             "-filter_complex", "[0][1][2]amix=inputs=3:normalize=0[a]", "-map", "[a]", str(dst)],
            check=False, capture_output=True,
        )
        base = dst.with_suffix("")
        Path(str(base) + ".lyrics.txt").write_text("[Instrumental]\n", encoding="utf-8")
        Path(str(base) + ".caption.txt").write_text(caption_for(t.name, args.artists) + "\n", encoding="utf-8")
        n += 1
        log.info("  %-48s -> %s", t.name, caption_for(t.name, args.artists)[:40])

    log.info("\n[corpus] %d instrumental tracks -> %s", n, out)
    log.info("[corpus] next: rsync to box, then ./train_lora.sh %s", args.name)


if __name__ == "__main__":
    main()

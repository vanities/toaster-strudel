#!/usr/bin/env python3
"""Generate tools/midi-manifest.json from the sourced-MIDI library in the vault.

Scans vault/02_SOURCES/Music/midi-sourced/<skill>/*.mid and emits one manifest
entry per file (the EXACT-notes counterpart to build-manifest.py, which maps
audio). midi_dna.py reads this in --manifest mode.

Add a track: drop a real sequenced .mid into midi-sourced/<skill>/ (see
research-midi.md for where to source them), then re-run:

    python3 tools/build-midi-manifest.py
"""
import json
import sys
from pathlib import Path

MIDI_ROOT = Path.home() / "git/work/matty/Artist-Vault-Kit/vault/02_SOURCES/Music/midi-sourced"
OUT = Path(__file__).resolve().parent / "midi-manifest.json"

ARTIST = {
    "style-david-wise": "David Wise", "style-mitsuda": "Mitsuda", "style-sonic": "Sonic",
    "style-jeremy-soule": "Jeremy Soule", "style-matt-uelmen": "Matt Uelmen",
    "style-dark-souls": "Dark Souls", "style-yasunori-nishiki": "Nishiki",
    "style-void-stranger": "Void Stranger",
}
SMALL = {"of", "the", "a", "in", "to", "and", "on"}


def titleize(slug: str) -> str:
    words = slug.split("-")
    return " ".join(w if w in SMALL and i else w.capitalize() for i, w in enumerate(words))


def main() -> int:
    if not MIDI_ROOT.exists():
        print(f"  no midi-sourced dir at {MIDI_ROOT}", file=sys.stderr)
        return 1
    entries: list[dict] = []
    for skill_dir in sorted(MIDI_ROOT.glob("style-*")):
        skill = skill_dir.name
        artist = ARTIST.get(skill, skill.replace("style-", "").title())
        sp = skill_dir / "_sources.json"
        sources = json.loads(sp.read_text()) if sp.exists() else {}
        mids = sorted(skill_dir.glob("*.mid"))
        for p in mids:
            src = sources.get(p.name, {})
            entries.append({"skill": skill, "label": f"{artist} · {titleize(p.stem)}", "midi": str(p),
                            "source_site": src.get("site"), "source_url": src.get("url")})
        print(f"  {skill}: {len(mids)} midi ({sum(1 for p in mids if p.name in sources)} attributed)", file=sys.stderr)
    OUT.write_text(json.dumps(entries, indent=2))
    print(f"\n  wrote {len(entries)} entries -> {OUT}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

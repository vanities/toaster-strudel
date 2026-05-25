#!/usr/bin/env python3
"""Generate tools/reference-manifest.json — maps each style-* skill to its cited
reference tracks, resolving exact file paths under the audio reference library.

The transcribe.py batch mode reads this file. Re-run to expand scope (add terms
below) or after adding albums:

    python3 tools/build-manifest.py

Two resolution strategies:
  EXACT   — verbatim relative paths (the electronic refs, from batch-analyze).
  BY_NAME — {dir, tracks[]} resolved by case-insensitive filename substring,
            scoped to a directory hint so cross-album collisions can't happen.

Skills with no local audio (Khruangbin, Nmesh, Matt Uelmen, Switch Angel, Rone's
Boiler Room set) are listed in NO_AUDIO and reported, not resolved.
"""
import json
import sys
from pathlib import Path

AR = Path.home() / "git/work/me/game/references/audio"
OUT = Path(__file__).resolve().parent / "reference-manifest.json"

EXACT = {
    "style-bonobo": [
        "Bonobo - Black Sands  Japanese Edition (2010) [CD FLAC] {BRC-255}/01. Prelude.flac",
        "Bonobo - Black Sands  Japanese Edition (2010) [CD FLAC] {BRC-255}/03. Kong.flac",
        "Bonobo - Black Sands  Japanese Edition (2010) [CD FLAC] {BRC-255}/04. Eyesdown.flac",
        "Bonobo - Black Sands  Japanese Edition (2010) [CD FLAC] {BRC-255}/07. 1009.flac",
        "Bonobo - Black Sands  Japanese Edition (2010) [CD FLAC] {BRC-255}/11. Animals.flac",
        "Bonobo - Black Sands  Japanese Edition (2010) [CD FLAC] {BRC-255}/12. Black Sands.flac",
    ],
    "style-djrum": [
        "Djrum - Portrait with Firewood (2018)/01 - Unblocked.flac",
        "Djrum - Portrait with Firewood (2018)/03 - Creature, Pt. 1.flac",
        "Djrum - Portrait with Firewood (2018)/04 - Creature, Pt. 2.flac",
        "Djrum - Portrait with Firewood (2018)/05 - Sex.flac",
        "Djrum - Under Tangled Silence (2025) - WEB FLAC/07. Reprise.flac",
        "Djrum - Under Tangled Silence (2025) - WEB FLAC/02. Waxcap.flac",
        "Djrum - Under Tangled Silence (2025) - WEB FLAC/05. Hold.flac",
    ],
    "style-floating-points": [
        "Floating Points - Crush (2019) [FLAC] {ZENCD259}/02 - Last Bloom.flac",
        "Floating Points - Crush (2019) [FLAC] {ZENCD259}/06 - LesAlpx.flac",
        "Floating Points - Crush (2019) [FLAC] {ZENCD259}/04 - Requiem for CS70 and Strings.flac",
        "Floating Points - Cascade (2024) [ZENDNL303] [WEB FLAC]/03 - Floating Points - Birth4000.flac",
        "Floating Points - Cascade (2024) [ZENDNL303] [WEB FLAC]/07 - Floating Points - Afflecks Palace.flac",
        "Floating Points - Reflections - Mojave Desert (2017) {LBOP5041 CD} [FLAC]/01 Mojave Desert.flac",
        "Floating Points - Reflections - Mojave Desert (2017) {LBOP5041 CD} [FLAC]/04 Kelso Dunes.flac",
    ],
    "style-kiasmos": [
        "Kiasmos - Kiasmos (2014) ERATP062CD [flac]/01. Lit.flac",
        "Kiasmos - Kiasmos (2014) ERATP062CD [flac]/02. Held.flac",
        "Kiasmos - Kiasmos (2014) ERATP062CD [flac]/03. Looped.flac",
        "Kiasmos - Kiasmos (2014) ERATP062CD [flac]/04. Swayed.flac",
        "Kiasmos - Kiasmos (2014) ERATP062CD [flac]/05. Thrown.flac",
        "Kiasmos - Kiasmos (2014) ERATP062CD [flac]/07. Bent.flac",
    ],
    "style-skee-mask": [
        "Skee Mask - Compro (2018) {Ilian Tape - ITLP04} [WEB 16-48 FLAC]/03 - Skee Mask - Rev8617.flac",
        "Skee Mask - Compro (2018) {Ilian Tape - ITLP04} [WEB 16-48 FLAC]/09 - Skee Mask - Flyby VFR.flac",
        "Skee Mask - Compro (2018) {Ilian Tape - ITLP04} [WEB 16-48 FLAC]/05 - Skee Mask - Via Sub Mids.flac",
        "Skee Mask - Pool [2021] [WEB-FLAC]/Skee Mask - ITLP09 Skee Mask - Pool - 03 LFO.flac",
        "Skee Mask - Pool [2021] [WEB-FLAC]/Skee Mask - ITLP09 Skee Mask - Pool - 08 Breathing Method.flac",
        "Skee Mask - Resort (2024 WF)/04 - Skee Mask - Element.flac",
        "Skee Mask - Resort (2024 WF)/11 - Skee Mask - 7AM At The Rodeo.flac",
    ],
    # Genesis / Mega Drive FM (YM2612) — Masato Nakamura (Sonic 1 & 2) + the
    # MJ-team Sonic 3 & Knuckles. .m4a, resolved verbatim (BY_NAME skips non-flac/mp3).
    "style-sonic": [
        "Sonic 1 (1991) [96-24 FLAC]/02 - Green Hill Zone.m4a",
        "Sonic 1 (1991) [96-24 FLAC]/05 - Labyrinth Zone.m4a",
        "Sonic 1 (1991) [96-24 FLAC]/06 - Star Light Zone.m4a",
        "Sonic 2 (1992) [96-24 FLAC]/04 - Chemical Plant Zone.m4a",
        "Sonic 2 (1992) [96-24 FLAC]/08 - Mystic Cave Zone.m4a",
        "Sonic 3 & Knuckles (1994) [24-96 FLAC]/Disc 1 (Sonic 3)/1-04 Hydrocity 1.m4a",
        "Sonic 3 & Knuckles (1994) [24-96 FLAC]/Disc 1 (Sonic 3)/1-08 Carnival Night 1.m4a",
        "Sonic 3 & Knuckles (1994) [24-96 FLAC]/Disc 1 (Sonic 3)/1-10 Ice Cap 1.m4a",
    ],
}

BY_NAME = {
    "style-void-stranger": {"dir": "elegy of the stars", "tracks": [
        "affection air", "buzzing boogie", "greedy groove", "lax lullaby",
        "void symphony", "brightest blossom", "gray nostalgia", "voided"]},
    "style-david-wise": {"dir": "donkey kong 2", "tracks": [
        "thorny-thorny", "misty woods", "icy lake"]},
    "style-mitsuda": {"dir": "chrono trigger", "tracks": [
        "chrono trigger", "secret of the forest", "yearnings of the wind",
        "schala", "frog's theme"]},
    "style-dark-souls": {"dir": "dark souls", "tracks": [
        "majula", "moment's peace"]},
    "style-yasunori-nishiki": {"dir": "octopath", "tracks": ["at your back"]},
    "style-slowdive": {"dir": "everything is alive", "tracks": ["alife"]},
    # Rone: skill cites the Boiler Room live set (not on disk); use the Tohu Bohu
    # studio album, which IS local and is clean Rone reference material.
    "style-rone": {"dir": "tohu bohu", "tracks": [
        "bye bye macadam", "parade", "la grande ourse", "icare", "beast"]},
    # Fetched via yt-dlp into references/audio/_fetched/ (not in the FLAC library).
    "style-khruangbin": {"dir": "_fetched", "tracks": ["como me quieres", "august 10"]},
    "style-nmesh": {"dir": "_fetched", "tracks": ["kimono"]},
    "style-matt-uelmen": {"dir": "_fetched", "tracks": ["tristram", "wilderness"]},
    # ── new style skills (2026-05-25) — hearted artists + Sonic, all on disk ──
    "style-bibio": {"dir": "bibio", "tracks": [
        "potion", "cinnamon cinematic", "cherry go round", "ambivalence avenue",
        "fire ant", "haikuesque", "lovers"]},
    "style-clair-obscur": {"dir": "expedition 33", "tracks": [
        "rain from the ground", "battling breeze", "in lumi", "until you",
        "electric tides", "goblu", "entrance of the village"]},
    "style-toro-y-moi": {"dir": "underneath the pine", "tracks": [
        "divina", "still sound", "new beat", "go with you"]},
    "style-esbe": {"dir": "bloomsday", "tracks": ["float", "wanderlust", "reverie", "serenade"]},
    "style-nomak": {"dir": "nomak", "tracks": [
        "anger of the earth", "spiritual home", "diaphanous air", "blessing dance"]},
    "style-jeremy-soule": {"dir": "skyrim", "tracks": [
        "secunda", "dragonborn", "far horizons", "from past to present", "streets of whiterun"]},
    "style-forest-swords": {"dir": "forest swords", "tracks": [
        "highest flood", "panic", "arms out", "border margin"]},
    "style-thrupence": {"dir": "thrupence", "tracks": ["rinse repeat", "thought 12"]},
    "style-strfkr": {"dir": "strfkr", "tracks": ["reptilians", "julius", "bury us alive", "mystery cloud"]},
    "style-home": {"dir": "home - odyssey", "tracks": ["decay", "resonance", "tides", "native", "oort cloud"]},
}

# Adam's ❤️ heart tracks (heart-tracks-analysis.md) not already covered above —
# fuzzy-resolved over the whole lib (incl _fetched). The EP's real north star.
HEARTS = {
    "style-bonobo": {"dir": "bonobo", "tracks": ["cirrus", "nightlite"]},
    "style-djrum": {"dir": "djrum", "tracks": ["a tune for us"]},
    "style-floating-points": {"dir": "floating points", "tracks": ["anasickmodular", "key103", "sea-watch", "silhouettes", "vocoder"]},
    "style-khruangbin": {"dir": "khruangbin", "tracks": ["dern kala", "petits gris", "people everywhere", "white gloves"]},
    "style-kiasmos": {"dir": "kiasmos", "tracks": ["burst", "sailed", "spun"]},
    "style-skee-mask": {"dir": "skee", "tracks": ["cz3000", "daytime gamer", "was a dancer", "nvivo", "reminiscr", "terminal z"]},
    "style-yasunori-nishiki": {"dir": "octopath", "tracks": ["battle on the sea", "ruins immemorial"]},
    "style-mitsuda": {"dir": "chrono trigger", "tracks": ["corridor of time"]},
    "style-dark-souls": {"dir": "dark souls", "tracks": ["firelink"]},
}

NO_AUDIO = {
    "style-switch-angel": "reference is a YouTube live-coding tutorial, not a track",
}

ARTIST = {
    "style-bonobo": "Bonobo", "style-djrum": "DJRUM",
    "style-floating-points": "Floating Points", "style-kiasmos": "Kiasmos",
    "style-skee-mask": "Skee Mask", "style-void-stranger": "Void Stranger",
    "style-david-wise": "David Wise", "style-mitsuda": "Mitsuda",
    "style-dark-souls": "Dark Souls", "style-yasunori-nishiki": "Nishiki",
    "style-slowdive": "Slowdive", "style-rone": "Rone", "style-khruangbin": "Khruangbin",
    "style-nmesh": "Nmesh", "style-matt-uelmen": "Matt Uelmen",
    "style-bibio": "Bibio", "style-clair-obscur": "Clair Obscur", "style-sonic": "Sonic",
    "style-toro-y-moi": "Toro y Moi", "style-esbe": "Esbe", "style-nomak": "Nomak",
    "style-jeremy-soule": "Jeremy Soule", "style-forest-swords": "Forest Swords",
    "style-thrupence": "Thrupence", "style-strfkr": "STRFKR", "style-home": "HOME",
}


def clean_label(stem: str) -> str:
    # strip leading track numbers / "Artist - " noise for a readable label
    s = stem
    for sep in (" - ", ". ", " "):
        if sep in s and s.split(sep, 1)[0].replace(".", "").strip().isdigit():
            s = s.split(sep, 1)[1]
            break
    return s.strip()


def resolve_by_name(dir_hint: str, term: str) -> Path | None:
    matches = sorted(
        p for p in AR.rglob("*")
        if p.suffix.lower() in (".flac", ".mp3")
        and dir_hint in str(p).lower()
        and term in p.name.lower()
    )
    return matches[0] if matches else None


def main() -> int:
    entries: list[dict] = []
    print("=== manifest coverage ===", file=sys.stderr)

    for skill, rels in EXACT.items():
        n = 0
        for rel in rels:
            p = AR / rel
            if p.exists():
                entries.append({"skill": skill, "label": f"{ARTIST[skill]} · {clean_label(p.stem)}", "path": str(p)})
                n += 1
            else:
                print(f"  [{skill}] MISSING exact: {rel}", file=sys.stderr)
        print(f"  {skill}: {n}/{len(rels)} (exact)", file=sys.stderr)

    for skill, spec in BY_NAME.items():
        n = 0
        for term in spec["tracks"]:
            p = resolve_by_name(spec["dir"], term)
            if p:
                entries.append({"skill": skill, "label": f"{ARTIST[skill]} · {clean_label(p.stem)}", "path": str(p)})
                n += 1
            else:
                print(f"  [{skill}] UNRESOLVED term: '{term}' (dir~{spec['dir']})", file=sys.stderr)
        print(f"  {skill}: {n}/{len(spec['tracks'])} (by-name)", file=sys.stderr)

    for skill, spec in HEARTS.items():
        n = 0
        for term in spec["tracks"]:
            p = resolve_by_name(spec["dir"], term)
            if p:
                entries.append({"skill": skill, "label": f"{ARTIST[skill]} · {clean_label(p.stem)}", "path": str(p)})
                n += 1
            else:
                print(f"  [{skill}] UNRESOLVED heart: '{term}'", file=sys.stderr)
        print(f"  {skill}: {n}/{len(spec['tracks'])} (hearts)", file=sys.stderr)

    for skill, why in NO_AUDIO.items():
        print(f"  {skill}: NO AUDIO — {why}", file=sys.stderr)

    seen = set()
    entries = [e for e in entries if not (e["path"] in seen or seen.add(e["path"]))]
    OUT.write_text(json.dumps(entries, indent=2))
    print(f"\n  wrote {len(entries)} entries -> {OUT}", file=sys.stderr)
    # PC helpers for the GPU allin1 step: a PC-path manifest + an rsync transfer list
    ar = str(AR) + "/"
    pc = [{**e, "path": e["path"].replace(ar, "/home/vanities/refs/audio/")} for e in entries]
    (OUT.parent / "pc-manifest.json").write_text(json.dumps(pc, indent=2))
    rels = [e["path"][len(ar):] for e in entries if e["path"].startswith(ar)]
    (OUT.parent / "xfer-list.txt").write_text("\n".join(rels) + "\n")
    print(f"  wrote pc-manifest.json + xfer-list.txt ({len(rels)} files) for the GPU step", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

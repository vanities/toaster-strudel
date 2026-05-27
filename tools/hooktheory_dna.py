#!/usr/bin/env python3
"""Hooktheory / TheoryTab clipboard JSON → symbolic "style DNA" card.

Hooktheory's TheoryTab editor exports a clipboard JSON: melody as scale degrees
(sd 1-7 + relative octave) and chords as scale-degree roots, over a key+mode.
That's exactly melody + functional harmony — free, and it covers the non-VGM
artists the MIDI archives miss (pop, electronic… it has Bonobo). This converts
the scale-degree data to absolute pitches/chords, reuses the same symbolic_dna /
key_estimate / note-grid as the MIDI path, and writes a card so distill folds it
into the style skill (source: Hooktheory).

    tools/.venv-transcribe/bin/python tools/hooktheory_dna.py SONG.json \
        --skill style-bonobo --label "Bonobo · Kong" --url https://www.hooktheory.com/theorytab/view/...
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from transcribe import symbolic_dna, key_estimate, slugify, collapse, PITCHES  # noqa: E402
from midi_dna import strudel_seed  # 32nd-grid note line, chord-stacked  # noqa: E402

SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11], "ionian": [0, 2, 4, 5, 7, 9, 11],
    "dorian": [0, 2, 3, 5, 7, 9, 10], "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11], "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "aeolian": [0, 2, 3, 5, 7, 8, 10], "minor": [0, 2, 3, 5, 7, 8, 10],
    "locrian": [0, 1, 3, 5, 6, 8, 10],
}
NOTE2PC = {"C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3, "E": 4, "F": 5,
           "F#": 6, "GB": 6, "G": 7, "G#": 8, "AB": 8, "A": 9, "A#": 10, "BB": 10, "B": 11}
BASE_OCT = 5  # tonic at MIDI octave 4 (e.g. F# → 66)
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII"]


def deg_pitch(sd: int, octave: int, tonic_pc: int, scale: list[int]) -> int:
    d = sd - 1
    return tonic_pc + 12 * BASE_OCT + scale[d % 7] + 12 * (d // 7) + 12 * octave


def chord_name(root_deg: int, tonic_pc: int, scale: list[int], seventh: bool) -> tuple[str, str]:
    """Absolute name (e.g. 'F#m') + a rough roman label."""
    d = root_deg - 1
    idxs = [d, d + 2, d + 4] + ([d + 6] if seventh else [])
    pcs = [(tonic_pc + scale[i % 7] + 12 * (i // 7)) % 12 for i in idxs]
    root = pcs[0]
    third, fifth = (pcs[1] - root) % 12, (pcs[2] - root) % 12
    qual = ""
    if third == 4 and fifth == 7:
        qual = ""
    elif third == 3 and fifth == 7:
        qual = "m"
    elif third == 3 and fifth == 6:
        qual = "dim"
    elif third == 4 and fifth == 8:
        qual = "aug"
    if seventh:
        sev = (pcs[3] - root) % 12
        qual = {("", 11): "maj7", ("", 10): "7", ("m", 10): "m7", ("m", 11): "mMaj7",
                ("dim", 10): "m7b5", ("dim", 9): "dim7"}.get((qual, sev), qual + "7")
    roman = ROMAN[d % 7]
    roman = roman.lower() if "m" in qual or "dim" in qual else roman
    return PITCHES[root] + qual, roman


def convert(data: dict, label: str, skill: str, url: str | None) -> dict:
    key = data["keys"][0]
    tonic_pc = NOTE2PC[key["tonic"].upper()]
    scale = SCALES.get(key["scale"].lower(), SCALES["major"])
    notes = [(n["beat"], n["beat"] + n["duration"], deg_pitch(int(n["sd"]), n["octave"], tonic_pc, scale))
             for n in data["notes"] if not n["isRest"]]
    notes.sort()
    prog, romans = [], []
    for c in data["chords"]:
        if c.get("isRest"):
            continue
        name, rom = chord_name(c["root"], tonic_pc, scale, c.get("type") == 7)
        prog.append(name)
        romans.append(rom)
    pcs = Counter(p % 12 for (_s, _e, p) in notes)
    mel = {"dna": symbolic_dna([(s, e, p) for (s, e, p) in notes]),
           "key": key_estimate([(s, e, p) for (s, e, p) in notes]),
           "strudel_seed": strudel_seed(notes, bars=2),
           "strudel_full": strudel_seed(notes, bars=None)}
    return {
        "label": label, "skill": skill, "source": "hooktheory",
        "source_site": "Hooktheory", "source_url": url,
        "key_str": f"{key['tonic']} {key['scale']}",
        "stats": {"key_chroma": key["tonic"], "n_notes": len(notes)},
        "chords": collapse(prog), "romans": collapse(romans),
        "melody": mel,
    }


def render_card(r: dict) -> str:
    site = f"[{r['source_site']}]({r['source_url']})" if r.get("source_url") else r["source_site"]
    m = r["melody"]
    dna, k = m["dna"], m["key"]
    L = [f"# {r['label']}", "",
         f"`source: Hooktheory (melody + functional harmony)` · key **{r['key_str']}**", "",
         f"_Scale-degree transcription from {site} — melody contour + chord function, free. "
         "Partial (the hook), not the full multitrack; use for melodic/harmonic DNA._", "",
         f"**Progression:** `{' '.join(r['chords'])}`   ({' '.join(r['romans'])})", "",
         "## Melody"]
    if dna:
        reg = dna["register"]
        ivs = ", ".join(f"{i['interval']} ×{i['count']}" for i in dna["top_intervals"][:6])
        L += [f"- key {(k or {}).get('key','?')} · register {reg['low']}↔{reg['high']} "
              f"(median {reg['median']}, span {reg['span_semitones']}st)",
              f"- pitch-classes: {' '.join(dna['top_pitch_classes'])}",
              f"- intervals: {ivs}",
              f'- notes ({dna["n_notes"]}, full): `note("{m["strudel_full"]}")`']
    L.append("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("json", type=Path, help="Hooktheory clipboard JSON file")
    ap.add_argument("--skill", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--url", default=None)
    ap.add_argument("--out", type=Path, default=Path("references/analysis"))
    args = ap.parse_args()
    data = json.loads(args.json.read_text())
    r = convert(data, args.label, args.skill, args.url)
    outdir = args.out / args.skill
    outdir.mkdir(parents=True, exist_ok=True)
    slug = slugify(args.label.split("·")[-1])
    (outdir / f"{slug}.json").write_text(json.dumps(r, indent=2))
    (outdir / f"{slug}.md").write_text(render_card(r))
    print(render_card(r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

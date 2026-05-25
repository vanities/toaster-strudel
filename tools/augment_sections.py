#!/usr/bin/env python3
"""Replace librosa sections with allin1 functional sections in the cards.

Consumes allin1-results.json (from the GPU box) and rebuilds each card's
per-section breakdown using allin1's labeled, downbeat-aligned segments
(intro/verse/chorus/bridge/inst/solo/outro/...). Reuses the cached notes + BTC
chords (no demucs / transcription / BTC recompute); loads audio only for
per-segment loudness/brightness.

    tools/.venv-transcribe/bin/python tools/augment_sections.py [allin1-results.json]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "tools")
from transcribe import symbolic_dna, strudel_line, collapse, slugify, render_card

QMAP = {"maj": "", "min": "m", "dim": "dim", "aug": "aug", "min6": "m6", "maj6": "6",
        "min7": "m7", "minmaj7": "mM7", "maj7": "maj7", "7": "7", "dim7": "dim7",
        "hdim7": "m7b5", "sus2": "sus2", "sus4": "sus4"}


def norm_chord(lab: str) -> str:
    if lab in ("N", "X", None, ""):
        return "~"
    if ":" not in lab:
        return lab
    root, q = lab.split(":", 1)
    return root + QMAP.get(q, q)


def merge_segments(segs):
    """Collapse runs of identical labels (allin1 over-segments) into blocks."""
    out = []
    for s, e, lab in segs:
        if out and out[-1][2] == lab:
            out[-1][1] = e
        else:
            out.append([s, e, lab])
    return out


def audio_feats(path: str):
    import librosa
    y, sr = librosa.load(path, sr=22050, mono=True)
    rms = librosa.feature.rms(y=y)[0]
    cen = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    return rms, cen, librosa.times_like(rms, sr=sr)


def main() -> int:
    res_path = sys.argv[1] if len(sys.argv) > 1 else "allin1-results.json"
    out = Path("references/analysis")
    cache = Path(__file__).resolve().parent / ".cache-stems"
    results = {r["label"]: r for r in json.loads(Path(res_path).read_text())}

    n = 0
    for jp in sorted(out.rglob("*.json")):
        if "_cache" in jp.parts:
            continue
        r = json.loads(jp.read_text())
        a = results.get(r["label"])
        if not a or not a.get("segments"):
            continue
        bpm = r["stats"]["bpm"]
        tcache = cache / slugify(r["label"])

        voice_notes = {}
        for vn in ("bass", "melody", "full-mix"):
            f = tcache / "notes" / f"{vn}.json"
            if f.exists():
                voice_notes[vn] = [tuple(x) for x in json.loads(f.read_text())]
        bf = tcache / "btc_chords.json"
        timed = [(s, e, norm_chord(c)) for s, e, c in json.loads(bf.read_text())] if bf.exists() else []

        try:
            rms, cen, tt = audio_feats(r["file"])
        except Exception as e:
            print(f"  [audio] {r['label']}: {e}", file=sys.stderr)
            rms = cen = tt = None

        secs = []
        for (s, e, label) in merge_segments(a["segments"]):
            if e - s < 0.2:   # drop allin1's zero-width start/end boundary markers
                continue
            sec = {"name": label, "start": round(s, 1), "end": round(e, 1), "rms": 0.0, "centroid_hz": 0}
            if tt is not None:
                m = (tt >= s) & (tt < e)
                if m.any():
                    sec["rms"] = round(float(rms[m].mean()), 4)
                    sec["centroid_hz"] = int(cen[m].mean())
            sec["chords"] = collapse([c for cs, _ce, c in timed if s <= cs < e and c != "~"])[:8]
            sec["voices"] = {}
            for vn, notes in voice_notes.items():
                sn = [nt for nt in notes if s <= nt[0] < e]
                if len(sn) >= 4:
                    sec["voices"][vn] = {"dna": symbolic_dna(sn), "strudel_seed": strudel_line(sn, bpm, t0=s)}
            secs.append(sec)

        r["sections"] = secs
        r["section_method"] = "allin1"
        jp.write_text(json.dumps(r, indent=2))
        jp.with_suffix(".md").write_text(render_card(r))
        n += 1
        print(f"  ✓ {r['label']}: {len(secs)} sections {[x[2] for x in a['segments']]}", file=sys.stderr)

    print(f"\n  augmented {n} cards with allin1 sections", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Rip symbolic / note-level info from a reference track, section by section.

Where `analyze-wav.py` extracts the *production envelope* (one BPM, one key,
brightness, dynamics), this pulls the *musical content* an LLM needs to actually
reproduce the ideas in Strudel: the bassline notes, the melodic contour, the
chord progression, the interval/octave signature, register, and mode — broken
out per song-section AND summarised whole-track.

Pipeline per track:
  1. global stats   librosa     — bpm, key, centroid, flatness, onsets/s, dyn
  2. stems          demucs      — bass / drums / other / vocals (cached to disk)
  3. transcription  basic-pitch — bass + melodic stems -> MIDI notes (cached)
  4. sections       librosa     — boundaries + per-section rms / centroid
  5. symbolic       music21     — key+confidence, pitch-class mode, register,
                                  interval histogram (octave-displacement DNA)
  6. chords         librosa     — chroma -> triad template match, per-bar
  7. serialize                  — <out>/<slug>.json (full) + <slug>.md (card)

Caching: the expensive demucs + basic-pitch passes write to <cache>/<slug>/, so
re-running to improve sections / chords / labels is cheap (stems aren't redone).

Run with the bundled venv:
  tools/.venv-transcribe/bin/python tools/transcribe.py <audio> [--out DIR]
  tools/.venv-transcribe/bin/python tools/transcribe.py --manifest tools/reference-manifest.json
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np

# basic-pitch calls scipy.signal.gaussian, removed in scipy>=1.13. Shim it back
# to the windows submodule so transcription runs against modern scipy.
import scipy.signal as _sps
if not hasattr(_sps, "gaussian"):
    from scipy.signal import windows as _spw
    _sps.gaussian = _spw.gaussian

PITCHES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
INTERVAL_NAMES = {
    0: "unison", 1: "m2", 2: "M2", 3: "m3", 4: "M3", 5: "P4",
    6: "tritone", 7: "P5", 8: "m6", 9: "M6", 10: "m7", 11: "M7", 12: "octave",
}
MAJ = np.array([1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0], float)
MIN = np.array([1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0], float)


def slugify(s: str) -> str:
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    return re.sub(r"[\s_-]+", "-", s) or "track"


def midi_to_name(m: int) -> str:
    return f"{PITCHES[m % 12]}{m // 12 - 1}"


def collapse(seq: list[str]) -> list[str]:
    out: list[str] = []
    for c in seq:
        if not out or out[-1] != c:
            out.append(c)
    return out


# ── stage 1: global stats ────────────────────────────────────────────────────
def global_stats(path: Path) -> dict:
    import librosa

    y, sr = librosa.load(str(path), sr=22050, mono=True)
    dur = float(librosa.get_duration(y=y, sr=sr))
    tempo = float(np.atleast_1d(librosa.beat.beat_track(y=y, sr=sr)[0])[0])
    hop = sr * 5
    rms = librosa.feature.rms(y=y, frame_length=hop, hop_length=hop)[0]
    sc = float(librosa.feature.spectral_centroid(y=y, sr=sr)[0].mean())
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
    flat = float(librosa.feature.spectral_flatness(y=y).mean())
    onsets = librosa.onset.onset_detect(y=y, sr=sr, units="time")
    rmn, rmx = float(rms.min()), float(rms.max())
    return {
        "duration_s": round(dur, 1),
        "bpm": round(tempo, 1),
        "key_chroma": PITCHES[int(np.argmax(chroma))],
        "centroid_hz": int(round(sc)),
        "flatness": round(flat, 4),
        "onsets_per_s": round(len(onsets) / max(dur, 0.01), 2),
        "dyn_x": round(rmx / max(rmn, 0.0001), 1),
    }


# ── stage 2: stems (cached) ──────────────────────────────────────────────────
def split_stems(path: Path, cache_dir: Path, device: str) -> dict[str, Path]:
    """demucs htdemucs -> {bass,drums,other,vocals}.wav, cached under cache_dir."""
    base = cache_dir / "htdemucs" / path.stem
    stems = {s: base / f"{s}.wav" for s in ("bass", "drums", "other", "vocals")}
    if all(p.exists() for p in stems.values()):
        return stems
    cmd = [sys.executable, "-m", "demucs", "-n", "htdemucs", "-d", device,
           "-o", str(cache_dir), str(path)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=1800)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"    [stems] demucs failed: {(getattr(e, 'stderr', '') or '')[-200:]}", file=sys.stderr)
        return {}
    return {s: p for s, p in stems.items() if p.exists()}


# ── stage 3: transcription (cached) ──────────────────────────────────────────
def transcribe_notes(audio_path: Path) -> list[tuple[float, float, int]]:
    import basic_pitch
    from basic_pitch.inference import predict

    onnx = Path(basic_pitch.__file__).parent / "saved_models" / "icassp_2022" / "nmp.onnx"
    _, _, note_events = predict(str(audio_path), str(onnx))
    notes = [(round(float(s), 3), round(float(e), 3), int(p)) for (s, e, p, *_r) in note_events]
    notes.sort(key=lambda n: n[0])
    return notes


def transcribe_cached(audio_path: Path, cache_json: Path) -> list[tuple[float, float, int]]:
    if cache_json.exists():
        return [tuple(x) for x in json.loads(cache_json.read_text())]
    notes = transcribe_notes(audio_path)
    cache_json.write_text(json.dumps(notes))
    return notes


# ── stage 4: sections ────────────────────────────────────────────────────────
def analyze_sections(path: Path, max_sections: int = 8) -> list[dict]:
    import librosa

    y, sr = librosa.load(str(path), sr=22050, mono=True)
    dur = float(librosa.get_duration(y=y, sr=sr))
    try:
        _t, beats = librosa.beat.beat_track(y=y, sr=sr)
        if len(beats) < 8:
            raise ValueError("too few beats")
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        mfcc = librosa.util.normalize(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13), axis=1)
        feat = librosa.util.sync(np.vstack([chroma, mfcc]), beats, aggregate=np.median)
        k = int(min(max_sections, max(2, len(beats) // 16)))
        bound_idx = librosa.segment.agglomerative(feat, k)
        bt = librosa.frames_to_time(beats, sr=sr)
        edges = sorted({0.0, *(float(bt[i]) for i in bound_idx if 0 < i < len(bt)), round(dur, 2)})
    except Exception as e:
        print(f"    [sections] fallback to whole-track: {e}", file=sys.stderr)
        edges = [0.0, round(dur, 2)]
    rms = librosa.feature.rms(y=y)[0]
    cen = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    tt = librosa.times_like(rms, sr=sr)
    secs = []
    for i, (s, e) in enumerate(zip(edges[:-1], edges[1:])):
        m = (tt >= s) & (tt < e)
        secs.append({
            "name": chr(65 + i), "start": round(s, 1), "end": round(e, 1),
            "rms": round(float(rms[m].mean()), 4) if m.any() else 0.0,
            "centroid_hz": int(cen[m].mean()) if m.any() else 0,
        })
    return secs


# ── stage 5: symbolic DNA ────────────────────────────────────────────────────
def symbolic_dna(notes: list[tuple[float, float, int]]) -> dict | None:
    if len(notes) < 4:
        return None
    pitches = [p for (_s, _e, p) in notes]
    pcs = Counter(p % 12 for p in pitches)
    intervals: Counter = Counter()
    for p0, p1 in zip(pitches, pitches[1:]):
        d = p1 - p0
        if d == 0:
            continue
        name = "octave+" if abs(d) > 12 else INTERVAL_NAMES.get(abs(d), f"{abs(d)}st")
        intervals[("+" if d > 0 else "-") + name] += 1
    lo, hi, med = min(pitches), max(pitches), int(np.median(pitches))
    oct_disp = sum(v for k, v in intervals.items() if "octave" in k)
    return {
        "n_notes": len(notes),
        "register": {"low": midi_to_name(lo), "high": midi_to_name(hi),
                     "median": midi_to_name(med), "span_semitones": hi - lo},
        "top_pitch_classes": [PITCHES[pc] for pc, _ in pcs.most_common(7)],
        "top_intervals": [{"interval": k, "count": c} for k, c in intervals.most_common(6)],
        "octave_displaced": oct_disp >= max(3, len(notes) // 20),
    }


def key_estimate(notes: list[tuple[float, float, int]]) -> dict | None:
    if len(notes) < 4:
        return None
    try:
        from music21 import stream, note as m21note

        s = stream.Stream()
        for (st, en, p) in notes:
            n = m21note.Note(p)
            n.quarterLength = max(0.125, round((en - st) * 2) / 2)
            s.append(n)
        k = s.analyze("key")
        return {"key": f"{k.tonic.name} {k.mode}", "confidence": round(min(float(k.tonalCertainty()), 1.0), 2)}
    except Exception as e:
        print(f"    [key] music21 failed: {e}", file=sys.stderr)
        return None


def strudel_line(notes: list[tuple[float, float, int]], bpm: float, t0: float | None = None, bars: int = 2) -> str | None:
    if not notes or bpm <= 0:
        return None
    step = (60.0 / bpm) / 4  # 16th grid
    steps = bars * 16
    base = notes[0][0] if t0 is None else t0
    grid = ["~"] * steps
    for (st, _en, p) in notes:
        idx = int(round((st - base) / step))
        if 0 <= idx < steps:
            grid[idx] = midi_to_name(p).replace("#", "s").lower()
    while grid and grid[-1] == "~":
        grid.pop()
    return " ".join(grid) if grid else None


# ── stage 6: chords (per-bar, with times) ────────────────────────────────────
def chords_timed(path: Path, max_bars: int = 80) -> list[tuple[float, str]]:
    import librosa

    try:
        y, sr = librosa.load(str(path), sr=22050, mono=True)
        _t, beats = librosa.beat.beat_track(y=y, sr=sr, units="frames")
        if len(beats) < 4:
            return []
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        bsync = librosa.util.sync(chroma, beats, aggregate=np.median)
        bt = librosa.frames_to_time(beats, sr=sr)
        out: list[tuple[float, str]] = []
        for b in range(0, min(bsync.shape[1], max_bars * 4), 4):
            v = bsync[:, b:b + 4].mean(axis=1)
            t = float(bt[b]) if b < len(bt) else 0.0
            if v.sum() <= 0:
                out.append((t, "~"))
                continue
            v = v / (np.linalg.norm(v) + 1e-9)
            best, best_s = "?", -1.0
            for root in range(12):
                for tmpl, q in ((MAJ, ""), (MIN, "m")):
                    sc = float(v @ np.roll(tmpl, root))
                    if sc > best_s:
                        best_s, best = sc, PITCHES[root] + q
            out.append((t, best))
        return out
    except Exception as e:
        print(f"    [chords] failed: {e}", file=sys.stderr)
        return []


# ── orchestration ────────────────────────────────────────────────────────────
def transcribe_track(path: Path, label: str, use_stems: bool, device: str, cache_root: Path) -> dict:
    print(f"  ◦ {label}", file=sys.stderr)
    tcache = cache_root / slugify(label)
    (tcache / "notes").mkdir(parents=True, exist_ok=True)

    r: dict = {"label": label, "file": str(path), "stats": global_stats(path)}
    bpm = r["stats"]["bpm"]
    chords_t = chords_timed(path)
    r["chords"] = collapse([c for _t, c in chords_t])[:16]
    sections = analyze_sections(path)

    stems = split_stems(path, tcache, device) if use_stems else {}
    r["stems_used"] = sorted(stems) or ["full-mix"]
    targets: list[tuple[str, Path]] = []
    if "bass" in stems:
        targets.append(("bass", stems["bass"]))
    if "other" in stems:
        targets.append(("melody", stems["other"]))
    if not targets:
        targets.append(("full-mix", path))

    r["voices"] = {}
    voice_notes: dict[str, list] = {}
    for name, src in targets:
        try:
            notes = transcribe_cached(src, tcache / "notes" / f"{name}.json")
        except Exception as e:
            print(f"    [transcribe:{name}] {e}", file=sys.stderr)
            continue
        voice_notes[name] = notes
        r["voices"][name] = {
            "dna": symbolic_dna(notes),
            "key": key_estimate(notes),
            "strudel_seed": strudel_line(notes, bpm),
        }

    r["sections"] = []
    for s in sections:
        sec = {**s, "chords": collapse([c for t, c in chords_t if s["start"] <= t < s["end"]])[:8], "voices": {}}
        for name, notes in voice_notes.items():
            sn = [n for n in notes if s["start"] <= n[0] < s["end"]]
            if len(sn) >= 4:
                sec["voices"][name] = {"dna": symbolic_dna(sn), "strudel_seed": strudel_line(sn, bpm, t0=s["start"])}
        r["sections"].append(sec)
    return r


# ── output ───────────────────────────────────────────────────────────────────
def _dna_line(name: str, v: dict) -> str:
    dna, key = v.get("dna"), v.get("key")
    if not dna:
        return f"- **{name}:** (too few notes)"
    reg = dna["register"]
    ivs = ", ".join(f"{i['interval']} ×{i['count']}" for i in dna["top_intervals"])
    ks = f"{key['key']} ({key['confidence']})" if key else "—"
    flag = " · **octave-displaced**" if dna["octave_displaced"] else ""
    line = (f"- **{name}** — key {ks}, register {reg['low']}↔{reg['high']} "
            f"(median {reg['median']}, span {reg['span_semitones']}st){flag}\n"
            f"    - pitch-classes: {' '.join(dna['top_pitch_classes'])}\n"
            f"    - intervals: {ivs}")
    if v.get("strudel_seed"):
        line += f'\n    - seed: `note("{v["strudel_seed"]}")`'
    return line


def render_card(r: dict) -> str:
    s = r["stats"]
    L = [f"# {r['label']}", ""]
    L.append(f"`{s['bpm']} BPM · key~{s['key_chroma']} · centroid {s['centroid_hz']}Hz · "
             f"flatness {s['flatness']} · {s['onsets_per_s']} onsets/s · dyn {s['dyn_x']}× · "
             f"{s['duration_s']}s` — stems: {', '.join(r['stems_used'])}")
    if r.get("chords"):
        L += ["", f"**Progression ({r.get('chord_method', 'chroma')}, per-bar):** `{' '.join(r['chords'])}`"]
    L += ["", "## Melodic DNA (whole track)"]
    for name, v in r.get("voices", {}).items():
        L.append(_dna_line(name, v))
    if r.get("sections"):
        L += ["", "## Sections"]
        for sec in r["sections"]:
            head = f"- **{sec['name']}** {sec['start']}–{sec['end']}s · rms {sec['rms']} · {sec['centroid_hz']}Hz"
            if sec.get("chords"):
                head += f" · `{' '.join(sec['chords'])}`"
            L.append(head)
            for name, v in sec.get("voices", {}).items():
                if v.get("strudel_seed"):
                    L.append(f'    - {name}: `note("{v["strudel_seed"]}")`')
    L.append("")
    return "\n".join(L)


def write_outputs(r: dict, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    slug = slugify(r["label"].split("·")[-1])
    (outdir / f"{slug}.json").write_text(json.dumps(r, indent=2))
    (outdir / f"{slug}.md").write_text(render_card(r))
    print(f"    -> {outdir / (slug + '.md')}", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", nargs="?", type=Path)
    ap.add_argument("--manifest", type=Path)
    ap.add_argument("--out", type=Path, default=Path("references/analysis"))
    ap.add_argument("--cache-dir", type=Path, default=None)
    ap.add_argument("--label", default=None)
    ap.add_argument("--no-stems", action="store_true")
    ap.add_argument("--device", default="cpu", help="demucs device: cpu | mps | cuda")
    ap.add_argument("--only", default=None, help="substring filter for manifest labels")
    args = ap.parse_args()
    cache = args.cache_dir or (Path(__file__).resolve().parent / ".cache-stems")

    if args.manifest:
        entries = json.loads(args.manifest.read_text())
        if args.only:
            entries = [e for e in entries if args.only.lower() in e["label"].lower()]
        print(f"manifest: {len(entries)} tracks · cache {cache}", file=sys.stderr)
        ok = 0
        for e in entries:
            p = Path(e["path"]).expanduser()
            if not p.exists():
                print(f"  MISSING: {e['label']} -> {p}", file=sys.stderr)
                continue
            try:
                r = transcribe_track(p, e["label"], not args.no_stems, args.device, cache)
                write_outputs(r, args.out / slugify(e.get("skill", "misc")))
                ok += 1
            except Exception as ex:
                import traceback
                print(f"  ERROR {e['label']}: {ex}", file=sys.stderr)
                traceback.print_exc()
        print(f"\n  done: {ok}/{len(entries)} tracks", file=sys.stderr)
        return 0

    if not args.audio:
        ap.print_help()
        return 1
    label = args.label or args.audio.stem
    r = transcribe_track(args.audio.expanduser(), label, not args.no_stems, args.device, cache)
    write_outputs(r, args.out)
    print(render_card(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())

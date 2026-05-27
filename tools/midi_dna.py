#!/usr/bin/env python3
"""MIDI → symbolic "style DNA" card — the EXACT-notes path.

Where transcribe.py *guesses* notes from audio (demucs → Basic Pitch, lossy),
this reads a real sequenced MIDI and emits the SAME card schema with EXACT
tempo, per-instrument voices, a real (note-derived) chord progression, and a
GM-program → Strudel-voice mapping. Cards land in references/analysis/<skill>/
next to the audio cards, so distill-skills.py folds them into the style skill.

Why MIDI beats the audio path for sequenced/chiptune VGM:
  - tempo is exact (no librosa octave-doubling — Stickerbush reads 100, not 198)
  - voices are the composer's real channels (not a demucs bass/other split)
  - harmony comes from the actual notes, not chroma template-matching on a mix
  - each voice carries its GM patch → a direct Strudel gm_* voice suggestion

Run with the bundled venv (mido + music21):
  tools/.venv-transcribe/bin/python tools/midi_dna.py FILE.mid \
      --skill style-david-wise --label "David Wise · Stickerbush Symphony"
  tools/.venv-transcribe/bin/python tools/midi_dna.py \
      --manifest tools/midi-manifest.json --out references/analysis
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import mido

# Some community-sequenced MIDIs carry a malformed key_signature meta (mode byte
# 255) that makes mido raise KeySignatureError on load, dropping the whole file.
# We re-derive key from the notes anyway (key_estimate), so the meta key isn't
# load-bearing — tolerate the bad event and default it to C instead of losing the track.
import mido.midifiles.meta as _meta
_orig_ks_decode = _meta.MetaSpec_key_signature.decode
def _tolerant_ks_decode(self, message, data):
    try:
        _orig_ks_decode(self, message, data)
    except _meta.KeySignatureError:
        message.key = "C"
_meta.MetaSpec_key_signature.decode = _tolerant_ks_decode

# Reuse the audio pipeline's symbolic stages verbatim — they operate on a plain
# list[(start, end, pitch)], so MIDI notes (in quarter-note units) feed straight in.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from transcribe import symbolic_dna, key_estimate, midi_to_name, slugify, collapse, PITCHES  # noqa: E402

# ── General MIDI: program (0-127) → name. "gm_" + slug = the Strudel voice. ────
GM_NAMES = [
    "Acoustic Grand Piano", "Bright Acoustic Piano", "Electric Grand Piano", "Honky-tonk Piano",
    "Electric Piano 1", "Electric Piano 2", "Harpsichord", "Clavinet",
    "Celesta", "Glockenspiel", "Music Box", "Vibraphone", "Marimba", "Xylophone", "Tubular Bells", "Dulcimer",
    "Drawbar Organ", "Percussive Organ", "Rock Organ", "Church Organ", "Reed Organ",
    "Accordion", "Harmonica", "Tango Accordion",
    "Acoustic Guitar (nylon)", "Acoustic Guitar (steel)", "Electric Guitar (jazz)", "Electric Guitar (clean)",
    "Electric Guitar (muted)", "Overdriven Guitar", "Distortion Guitar", "Guitar Harmonics",
    "Acoustic Bass", "Electric Bass (finger)", "Electric Bass (pick)", "Fretless Bass",
    "Slap Bass 1", "Slap Bass 2", "Synth Bass 1", "Synth Bass 2",
    "Violin", "Viola", "Cello", "Contrabass", "Tremolo Strings", "Pizzicato Strings",
    "Orchestral Harp", "Timpani",
    "String Ensemble 1", "String Ensemble 2", "Synth Strings 1", "Synth Strings 2",
    "Choir Aahs", "Voice Oohs", "Synth Voice", "Orchestra Hit",
    "Trumpet", "Trombone", "Tuba", "Muted Trumpet", "French Horn", "Brass Section", "Synth Brass 1", "Synth Brass 2",
    "Soprano Sax", "Alto Sax", "Tenor Sax", "Baritone Sax", "Oboe", "English Horn", "Bassoon", "Clarinet",
    "Piccolo", "Flute", "Recorder", "Pan Flute", "Blown Bottle", "Shakuhachi", "Whistle", "Ocarina",
    "Lead 1 (square)", "Lead 2 (sawtooth)", "Lead 3 (calliope)", "Lead 4 (chiff)",
    "Lead 5 (charang)", "Lead 6 (voice)", "Lead 7 (fifths)", "Lead 8 (bass + lead)",
    "Pad 1 (new age)", "Pad 2 (warm)", "Pad 3 (polysynth)", "Pad 4 (choir)",
    "Pad 5 (bowed)", "Pad 6 (metallic)", "Pad 7 (halo)", "Pad 8 (sweep)",
    "FX 1 (rain)", "FX 2 (soundtrack)", "FX 3 (crystal)", "FX 4 (atmosphere)",
    "FX 5 (brightness)", "FX 6 (goblins)", "FX 7 (echoes)", "FX 8 (sci-fi)",
    "Sitar", "Banjo", "Shamisen", "Koto", "Kalimba", "Bagpipe", "Fiddle", "Shanai",
    "Tinkle Bell", "Agogo", "Steel Drums", "Woodblock", "Taiko Drum", "Melodic Tom", "Synth Drum", "Reverse Cymbal",
    "Guitar Fret Noise", "Breath Noise", "Seashore", "Bird Tweet", "Telephone Ring", "Helicopter",
    "Applause", "Gunshot",
]


def gm_name(prog: int | None) -> str:
    if prog is None or not (0 <= prog < 128):
        return "Unknown"
    return GM_NAMES[prog]


def gm_voice(prog: int | None) -> str:
    """Strudel soundfont voice name, e.g. 73 -> 'gm_flute'."""
    if prog is None or not (0 <= prog < 128):
        return "gm_acoustic_grand_piano"
    return "gm_" + slugify(GM_NAMES[prog]).replace("-", "_")


# ── chord naming from EXACT pitch classes ─────────────────────────────────────
QUALITIES = [
    ("", (0, 4, 7)), ("m", (0, 3, 7)), ("7", (0, 4, 7, 10)), ("maj7", (0, 4, 7, 11)),
    ("m7", (0, 3, 7, 10)), ("sus4", (0, 5, 7)), ("sus2", (0, 2, 7)), ("dim", (0, 3, 6)),
]


def name_chord(pc_weight: list[float]) -> str:
    total = sum(pc_weight)
    if total <= 0:
        return "~"
    best, best_s = "?", -1e9
    for root in range(12):
        for suffix, ivs in QUALITIES:
            cover = sum(pc_weight[(root + iv) % 12] for iv in ivs)
            extra = total - cover
            # coverage rewards matched tones; extra penalises out-of-chord weight;
            # tiny bonus per tone so a real 7th beats the bare triad, not noise.
            score = cover - 0.55 * extra + 0.02 * len(ivs)
            if score > best_s:
                best_s, best = score, PITCHES[root] + suffix
    return best


# ── parse one MIDI into per-channel note streams (quarter-note units) ──────────
def parse_midi(path: Path) -> dict:
    mid = mido.MidiFile(str(path))
    tpb = mid.ticks_per_beat or 480

    tempos: list[int] = []          # microseconds per beat
    timesig = (4, 4)
    program: dict[int, int] = {}    # channel -> current program
    chan_prog_hist: dict[int, Counter] = defaultdict(Counter)
    # notes per channel: (start_q, end_q, pitch, velocity)
    chan_notes: dict[int, list[tuple[float, float, int, int]]] = defaultdict(list)
    drums = False

    for track in mid.tracks:
        t = 0
        open_notes: dict[tuple[int, int], tuple[float, int]] = {}  # (chan,pitch)->(start_q,vel)
        for msg in track:
            t += msg.time
            q = t / tpb
            if msg.type == "set_tempo":
                tempos.append(msg.tempo)
            elif msg.type == "time_signature":
                timesig = (msg.numerator, msg.denominator)
            elif msg.type == "program_change":
                program[msg.channel] = msg.program
            elif msg.type == "note_on" and msg.velocity > 0:
                if msg.channel == 9:
                    drums = True
                    continue
                open_notes[(msg.channel, msg.note)] = (q, msg.velocity)
                chan_prog_hist[msg.channel][program.get(msg.channel, 0)] += 1
            elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                if msg.channel == 9:
                    continue
                k = (msg.channel, msg.note)
                if k in open_notes:
                    s, v = open_notes.pop(k)
                    chan_notes[msg.channel].append((s, q, msg.note, v))

    bpm = round(mido.tempo2bpm(tempos[0]) if tempos else 120.0, 1)
    for ch in chan_notes:
        chan_notes[ch].sort(key=lambda n: n[0])
    chan_program = {ch: (h.most_common(1)[0][0] if h else 0) for ch, h in chan_prog_hist.items()}
    return {
        "bpm": bpm, "tpb": tpb, "timesig": timesig, "drums": drums,
        "chan_notes": dict(chan_notes), "chan_program": chan_program,
        "n_tracks": len(mid.tracks),
    }


GRID_SPQ = 8  # grid steps per quarter note: 4 = 16th, 8 = 32nd, 16 = 64th
GRID_LABEL = {4: "16th", 8: "32nd", 16: "64th"}


def strudel_seed(notes: list[tuple], bars: int | None = 2, spq: int = GRID_SPQ) -> str | None:
    """Note grid in quarter-note units (spq steps per quarter; 8 = 32nd-note grid —
    fine enough to keep fast chiptune runs that a 16th grid would merge). bars=None →
    the complete line (first note to last); an int caps to that many 4/4 bars."""
    if not notes:
        return None
    base = notes[0][0]
    if bars:
        steps = bars * 4 * spq
    else:
        last = max(e for (_s, e, _p, *_r) in notes)
        steps = max(1, int(round((last - base) * spq)) + 1)
    cells: dict[int, set[int]] = defaultdict(set)
    for (st, _en, p, *_r) in notes:
        idx = int(round((st - base) * spq))
        if 0 <= idx < steps:
            cells[idx].add(p)                 # accumulate — simultaneous notes = a chord
    grid = ["~"] * steps
    for idx, pset in cells.items():
        names = [midi_to_name(p).replace("#", "s").lower() for p in sorted(pset)]
        grid[idx] = names[0] if len(names) == 1 else "[" + ",".join(names) + "]"
    while grid and grid[-1] == "~":
        grid.pop()
    return " ".join(grid) if grid else None


def progression(parsed: dict, max_bars: int = 24) -> list[str]:
    num, den = parsed["timesig"]
    bar_q = num * 4.0 / den
    alln = [n for ch, ns in parsed["chan_notes"].items() for n in ns]
    if not alln:
        return []
    end = max(n[1] for n in alln)
    out: list[str] = []
    b = 0
    while b * bar_q < end and b < max_bars:
        lo, hi = b * bar_q, (b + 1) * bar_q
        w = [0.0] * 12
        for (s, e, p, _v) in alln:
            if s < hi and e > lo:                       # note sounds during this bar
                w[p % 12] += max(0.25, min(e, hi) - max(s, lo))
        out.append(name_chord(w))
        b += 1
    return collapse(out)


def velocity_dyn(parsed: dict) -> float:
    """Crude dynamic ratio from per-bar mean velocity (MIDI has no RMS)."""
    num, den = parsed["timesig"]
    bar_q = num * 4.0 / den
    alln = [n for ns in parsed["chan_notes"].values() for n in ns]
    if not alln:
        return 1.0
    bars: dict[int, list[int]] = defaultdict(list)
    for (s, _e, _p, v) in alln:
        bars[int(s // bar_q)].append(v)
    means = [sum(vs) / len(vs) for vs in bars.values() if vs]
    if not means:
        return 1.0
    return round(max(means) / max(min(means), 1.0), 1)


# ── classify channels into bass / melody / others ─────────────────────────────
def classify(parsed: dict) -> dict:
    chans = parsed["chan_notes"]
    stats = {}
    for ch, ns in chans.items():
        if len(ns) < 4:
            continue
        pitches = sorted(p for (_s, _e, p, _v) in ns)
        stats[ch] = {"n": len(ns), "median": pitches[len(pitches) // 2],
                     "lo": pitches[0], "hi": pitches[-1]}
    if not stats:
        return {}
    prog = parsed["chan_program"]
    # GM 112-127 are Percussive + Sound-effect patches — never the melody line.
    pitched = {c for c in stats if not (112 <= prog.get(c, 0) <= 127)}
    bass_ch = min(pitched or stats, key=lambda c: (stats[c]["median"], -stats[c]["n"]))
    mel_cands = [c for c in (pitched or stats) if c != bass_ch and stats[c]["median"] >= 55]
    melody_ch = (max(mel_cands, key=lambda c: stats[c]["n"]) if mel_cands
                 else max((c for c in (pitched or stats) if c != bass_ch), key=lambda c: stats[c]["median"], default=None))
    roles = {bass_ch: "bass"}
    if melody_ch is not None:
        roles[melody_ch] = "melody"
    return {"stats": stats, "roles": roles, "bass": bass_ch, "melody": melody_ch}


def voice_entry(parsed: dict, ch: int) -> dict:
    notes = [(s, e, p) for (s, e, p, _v) in parsed["chan_notes"][ch]]
    prog = parsed["chan_program"].get(ch, 0)
    return {
        "channel": ch, "program": prog, "gm": gm_name(prog), "strudel_voice": gm_voice(prog),
        "dna": symbolic_dna(notes), "key": key_estimate(notes),
        "strudel_seed": strudel_seed(notes, bars=2),     # 2-bar quick glance
        "strudel_full": strudel_seed(notes, bars=None),  # complete line, every bar
    }


def dedup_channels(parsed: dict) -> dict:
    """Sequencers (esp. XG arrangements) double a part onto a second channel for
    chorus/stereo — identical notes. Collapse channels with the same program +
    note signature so the card shows real voices, not echoes."""
    cn, cp = parsed["chan_notes"], parsed["chan_program"]
    seen: dict[tuple, int] = {}
    keep: dict[int, list] = {}
    for ch in sorted(cn):
        sig = (cp.get(ch, 0), tuple(p for (_s, _e, p, _v) in cn[ch][:48]))
        if sig in seen:
            continue
        seen[sig] = ch
        keep[ch] = cn[ch]
    parsed = {**parsed, "chan_notes": keep}
    return parsed


def analyze(path: Path, label: str, skill: str, source_site: str | None = None,
            source_url: str | None = None) -> dict:
    parsed = dedup_channels(parse_midi(path))
    cls = classify(parsed)
    if not cls:
        raise ValueError("no melodic channels with >=4 notes")

    # order: bass, melody, then remaining voices by note count
    ordered: list[int] = [c for c in (cls["bass"], cls["melody"]) if c is not None]
    ordered += [c for c in sorted(cls["stats"], key=lambda c: -cls["stats"][c]["n"]) if c not in ordered]
    voices: dict[str, dict] = {}
    for ch in ordered:
        role = cls["roles"].get(ch)
        prog = parsed["chan_program"].get(ch, 0)
        key = role if role else f"ch{ch} · {gm_name(prog)}"
        voices[key] = voice_entry(parsed, ch)

    alln = [(s, e, p) for ns in parsed["chan_notes"].values() for n in ns for (s, e, p, _v) in [n]]
    alln.sort(key=lambda n: n[0])
    track_key = key_estimate(alln)
    pcs = Counter(p % 12 for (_s, _e, p) in alln)
    total_q = max((e for (_s, e, _p) in alln), default=0.0)

    return {
        "label": label, "skill": skill, "file": str(path), "source": "midi",
        "source_site": source_site, "source_url": source_url,
        "midi": {"tempo_bpm": parsed["bpm"], "ppq": parsed["tpb"],
                 "time_sig": f"{parsed['timesig'][0]}/{parsed['timesig'][1]}",
                 "tracks": parsed["n_tracks"], "drums": parsed["drums"],
                 "channels": len(parsed["chan_notes"]),
                 "grid": GRID_LABEL.get(GRID_SPQ, f"1/{GRID_SPQ}q")},
        "stats": {
            "bpm": parsed["bpm"],
            "key_chroma": PITCHES[pcs.most_common(1)[0][0]] if pcs else "?",
            "key": track_key, "centroid_hz": None, "flatness": None,
            "duration_s": round(total_q * 60.0 / max(parsed["bpm"], 1), 1),
            "dyn_x": velocity_dyn(parsed),
        },
        "chord_method": "midi-exact",
        "chords": progression(parsed),
        "sections": [],
        "voices": voices,
    }


# ── card rendering ────────────────────────────────────────────────────────────
def _voice_line(name: str, v: dict) -> str:
    dna, key = v.get("dna"), v.get("key")
    head = f"- **{name}** — {v['gm']} (`{v['strudel_voice']}`, ch{v['channel']}/prog{v['program']})"
    if not dna:
        return head + " — (too few notes)"
    reg = dna["register"]
    ivs = ", ".join(f"{i['interval']} ×{i['count']}" for i in dna["top_intervals"])
    ks = f"{key['key']} ({key['confidence']})" if key else "—"
    flag = " · **octave-displaced**" if dna["octave_displaced"] else ""
    line = (f"{head}\n"
            f"    - key {ks}, register {reg['low']}↔{reg['high']} (median {reg['median']}, span {reg['span_semitones']}st){flag}\n"
            f"    - pitch-classes: {' '.join(dna['top_pitch_classes'])}\n"
            f"    - intervals: {ivs}\n"
            f"    - notes ({dna['n_notes']}, full): `note(\"{v.get('strudel_full') or v.get('strudel_seed') or ''}\")`")
    return line


def render_card(r: dict) -> str:
    m, s = r["midi"], r["stats"]
    tk = f" · key {s['key']['key']} ({s['key']['confidence']})" if s.get("key") else ""
    site = r.get("source_site") or "?"
    src = f"[{site}]({r['source_url']})" if r.get("source_url") else site
    L = [f"# {r['label']}", "",
         f"`source: MIDI (exact)` · `{m['tempo_bpm']} BPM · {m['time_sig']} · ppq {m['ppq']} · "
         f"{m['channels']} voices{' · drums' if m['drums'] else ''} · {s['duration_s']}s`{tk}", "",
         f"_Sequenced MIDI from {src} — exact notes, not audio transcription. Tempo/voices/harmony are the composer's, not estimated._"]
    if r.get("chords"):
        L += ["", f"**Progression (midi-exact, per-bar):** `{' '.join(r['chords'][:16])}`"]
    L += ["", "## Voices (exact)"]
    for name, v in r["voices"].items():
        L.append(_voice_line(name, v))
    L.append("")
    return "\n".join(L)


def write_outputs(r: dict, outdir: Path) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    slug = slugify(r["label"].split("·")[-1])
    (outdir / f"{slug}.json").write_text(json.dumps(r, indent=2))
    mdp = outdir / f"{slug}.md"
    mdp.write_text(render_card(r))
    return mdp


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("midi", nargs="?", type=Path)
    ap.add_argument("--skill", default="misc")
    ap.add_argument("--label", default=None)
    ap.add_argument("--manifest", type=Path, help="JSON: [{midi,skill,label}]")
    ap.add_argument("--out", type=Path, default=Path("references/analysis"))
    args = ap.parse_args()

    if args.manifest:
        entries = json.loads(args.manifest.read_text())
        ok = 0
        for e in entries:
            p = Path(e["midi"]).expanduser()
            if not p.exists():
                print(f"  MISSING: {e.get('label', p)} -> {p}", file=sys.stderr)
                continue
            try:
                r = analyze(p, e.get("label") or p.stem, e["skill"],
                            e.get("source_site"), e.get("source_url"))
                mdp = write_outputs(r, args.out / e["skill"])
                print(f"  ✓ {r['label']} ({r['midi']['tempo_bpm']} BPM, {len(r['voices'])} voices) -> {mdp}", file=sys.stderr)
                ok += 1
            except Exception as ex:
                import traceback
                print(f"  ERROR {e.get('label', p)}: {ex}", file=sys.stderr)
                traceback.print_exc()
        print(f"\n  done: {ok}/{len(entries)}", file=sys.stderr)
        return 0

    if not args.midi:
        ap.print_help()
        return 1
    r = analyze(args.midi.expanduser(), args.label or args.midi.stem, args.skill)
    write_outputs(r, args.out / args.skill)
    print(render_card(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())

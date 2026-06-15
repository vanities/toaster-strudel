#!/usr/bin/env python3
"""Static analyzer for Strudel track snapshots.

Reads tracks/<id>/*.strudel files (and optional manifest.json), then
estimates per-slot dynamics WITHOUT rendering audio:

  - Voice count
  - Sum of `gain()` values per voice  (proxy for RMS)
  - Rhythmic density  (estimated events per cycle)
  - Spectral character  (synth-vs-sample, low-pass cutoffs)
  - Effect richness    (delay/reverb/filter modulation present?)
  - Per-slot @cycles or manifest cycles

Outputs a table per slot + an ASCII bar chart of predicted dynamics.
Compares total dynamic range against reference tracks.

Usage:  uv run python3 tools/analyze-patterns.py 01-dawn
        uv run python3 tools/analyze-patterns.py 01-dawn --json
"""

import json
import re
import sys
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACKS_DIR = ROOT / "tracks"

# Rough reference dynamic ratios (from librosa analysis of real tracks).
REF_DYN = {
    "Bonobo · Kong":            5,
    "Skee Mask · Rev8617":      8,
    "Floating Pts · Last Bloom":5,
    "Kiasmos · Looped":         7,
    "DJRUM · Creature Pt.1":   15,
    "DJRUM · Reprise":         57,
    "Skee Mask · Flyby VFR":  273,
}

# ── parsing helpers ────────────────────────────────────────────────────
GAIN_RE = re.compile(r"\.gain\(\s*([\d.]+)")
GAIN_RANGE_RE = re.compile(r"\.gain\(\s*\w+\.range\(\s*([\d.]+)\s*,\s*([\d.]+)")
S_RE = re.compile(r'\.s\(\s*"([^"]+)"')
S_DIRECT_RE = re.compile(r'(?<!\.)s\(\s*"([^"]+)"')  # top-level s("...")
LPF_RE = re.compile(r"\.lpf\(\s*(?:\w+\.range\(\s*([\d.]+)\s*,\s*([\d.]+)|([\d.]+))")
NOTE_RE = re.compile(r'(?:^|[^\.])note\(\s*"([^"]+)"')
EUCLID_RE = re.compile(r"\((\d+),(\d+)\)")
FAST_RE = re.compile(r"\.fast\(\s*(\d+)")
SLOW_RE = re.compile(r"\.slow\(\s*(\d+)")
MULT_RE = re.compile(r'"\s*\w+\s*\*\s*(\d+)')  # patterns like "hh*8"
ANGLE_RE = re.compile(r"<([^>]+)>")
EFFECT_PRESENT = {
    "delay": re.compile(r"\.delay\("),
    "room": re.compile(r"\.room\("),
    "detune": re.compile(r"\.detune\("),
    "lpf_mod": re.compile(r"\.lpf\(\s*\w+\.range"),
    "degradeBy": re.compile(r"\.degradeBy\("),
    "attack": re.compile(r"\.attack\("),
    "release": re.compile(r"\.release\("),
    "pan_mod": re.compile(r"\.pan\(\s*\w+\.range"),
}
SYNTH_VOICES = {"sine", "sawtooth", "triangle", "square", "white", "pink"}


def parse_cps(code):
    m = re.search(r"setcps\s*\(\s*([\d.]+)", code)
    return float(m.group(1)) if m else 0.4


def strip_line_comments(code):
    """Strip `// ...` line comments but preserve newlines."""
    return re.sub(r"//[^\n]*", "", code)


def parse_voice_blocks(code):
    """Find top-level voices inside a `stack(...)`. Returns list of voice
    source strings (one per voice). Strips comments first to avoid
    comma-detection getting confused inside commented lines."""
    code = strip_line_comments(code)
    # Find stack(...)
    m = re.search(r"\bstack\s*\(", code)
    if not m:
        return []
    start = m.end()
    depth = 1
    end = start
    while end < len(code) and depth > 0:
        c = code[end]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                break
        end += 1
    body = code[start:end]
    # Split on top-level commas
    voices = []
    depth_p = 0
    depth_b = 0
    in_str = False
    buf = []
    for ch in body:
        if in_str:
            buf.append(ch)
            if ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            buf.append(ch)
            continue
        if ch == "(":
            depth_p += 1
        elif ch == ")":
            depth_p -= 1
        elif ch == "[":
            depth_b += 1
        elif ch == "]":
            depth_b -= 1
        if ch == "," and depth_p == 0 and depth_b == 0:
            s = "".join(buf).strip()
            if s:
                voices.append(s)
            buf = []
            continue
        buf.append(ch)
    tail = "".join(buf).strip()
    if tail:
        voices.append(tail)
    return voices


def estimate_voice_gain(voice_src):
    m = GAIN_RANGE_RE.search(voice_src)
    if m:
        lo, hi = float(m.group(1)), float(m.group(2))
        return (lo + hi) / 2
    m = GAIN_RE.search(voice_src)
    if m:
        return float(m.group(1))
    return 0.5  # default if no .gain() set


def estimate_voice_density(voice_src):
    """Rough events-per-cycle estimate."""
    # If the voice has a mask that's mostly 0, density is low — handle later
    # Count notes/samples per pattern
    density = 0
    # Find all patterns within strings
    for m in NOTE_RE.finditer(voice_src):
        pat = m.group(1)
        # Count non-`~` tokens, split by whitespace
        tokens = [t for t in re.split(r"\s+", pat) if t and t != "~"]
        # Inside <a b c>, those cycle one-per-cycle, so 1 event per cycle
        if pat.strip().startswith("<"):
            density += 1
        else:
            density += len(tokens)
    for m in S_DIRECT_RE.finditer(voice_src):
        pat = m.group(1)
        tokens = [t for t in re.split(r"\s+", pat) if t and t != "~"]
        if pat.strip().startswith("<"):
            density += 1
        else:
            density += len(tokens)
    # Apply *N multipliers in patterns
    for m in MULT_RE.finditer(voice_src):
        density *= int(m.group(1))
    # Apply .fast(N) / .slow(N)
    fast_m = FAST_RE.search(voice_src)
    if fast_m:
        density *= int(fast_m.group(1))
    slow_m = SLOW_RE.search(voice_src)
    if slow_m:
        density = density / int(slow_m.group(1))
    # Apply degradeBy reduction
    degr = re.search(r"\.degradeBy\(\s*([\d.]+)", voice_src)
    if degr:
        density *= (1 - float(degr.group(1)))
    return round(density, 2)


def voice_kind(voice_src):
    """Detect what kind of voice: synth / sample / noise / unknown."""
    for m in S_RE.finditer(voice_src):
        name = m.group(1).split()[0].strip('<>')
        if name in {"white", "pink", "brown"}:
            return "noise"
        if name in SYNTH_VOICES:
            return "synth"
        return "sample"
    for m in S_DIRECT_RE.finditer(voice_src):
        name = m.group(1).split()[0].strip('<>')
        if name in {"white", "pink", "brown"}:
            return "noise"
        if "_" in name or "bank" in voice_src:
            return "sample"
        return "sample-or-synth"
    return "unknown"


def voice_brightness(voice_src):
    """Rough centroid hint from lpf cutoff."""
    m = LPF_RE.search(voice_src)
    if not m:
        return 8000  # no filter → wide spectrum
    if m.group(3):
        return float(m.group(3))
    if m.group(1) and m.group(2):
        return (float(m.group(1)) + float(m.group(2))) / 2
    return 8000


def analyze_slot(code):
    voices = parse_voice_blocks(code)
    cps = parse_cps(code)
    summary = []
    for v in voices:
        kind = voice_kind(v)
        gain = estimate_voice_gain(v)
        density = estimate_voice_density(v)
        brightness = voice_brightness(v)
        effects = [name for name, rx in EFFECT_PRESENT.items() if rx.search(v)]
        summary.append({
            "kind": kind,
            "gain": round(gain, 3),
            "density_per_cycle": density,
            "lpf_avg_hz": int(brightness),
            "effects": effects,
            "preview": v.split("\n", 1)[0][:60],
        })
    total_gain = sum(v["gain"] for v in summary)
    total_density = sum(v["density_per_cycle"] for v in summary)
    avg_brightness = (
        sum(v["lpf_avg_hz"] for v in summary) / len(summary) if summary else 0
    )
    has_noise = any(v["kind"] == "noise" for v in summary)
    return {
        "cps": cps,
        "voice_count": len(voices),
        "total_gain": round(total_gain, 3),
        "total_density": round(total_density, 2),
        "avg_lpf_hz": int(avg_brightness),
        "has_noise": has_noise,
        "voices": summary,
    }


# ── output ──────────────────────────────────────────────────────────────
def bar(val, peak, width=30):
    if peak == 0:
        return ""
    n = max(0, int(val / peak * width))
    return "▮" * n + "·" * (width - n)


def load_manifest(tdir):
    manifest_path = tdir / "manifest.json"
    return json.loads(manifest_path.read_text()) if manifest_path.exists() else {}


def manifest_sections(manifest):
    """Manifests use "sections" (current) or "slots" (legacy) — accept both."""
    return manifest.get("sections") or manifest.get("slots") or []


def section_files(tdir):
    """The track's numbered section files. Excludes arrange.strudel (the
    generated whole-arc stitch — analyzing it as a section double-counts the
    entire track). Falls back to any non-arrange .strudel for odd layouts."""
    files = sorted(p for p in tdir.glob("*.strudel") if re.fullmatch(r"\d+\.strudel", p.name))
    if not files:
        files = sorted(p for p in tdir.glob("*.strudel") if p.name != "arrange.strudel")
    return files


def analyze_track(track_id):
    """Static per-section analysis for tracks/<track_id>.

    Returns (slot_results, manifest). Raises FileNotFoundError when the track
    dir or its section files are missing. This is the import surface for
    eval-tracks.py / loudness.py; main() below is the CLI veneer.
    """
    tdir = TRACKS_DIR / track_id
    if not tdir.is_dir():
        raise FileNotFoundError(f"no such track: {tdir}")
    manifest = load_manifest(tdir)
    manifest_slots = manifest_sections(manifest)
    slot_files = section_files(tdir)
    if not slot_files:
        raise FileNotFoundError(f"no .strudel section files in {tdir}")

    slot_results = []
    for i, p in enumerate(slot_files):
        code = p.read_text()
        slot = analyze_slot(code)
        # Resolve cycles: manifest > @cycles directive > default
        cycles = None
        if i < len(manifest_slots) and manifest_slots[i].get("cycles"):
            cycles = manifest_slots[i]["cycles"]
            cycles_source = "manifest"
        else:
            m = re.search(r"//\s*@cycles\s+(\d+)", code)
            if m:
                cycles = int(m.group(1))
                cycles_source = "@cycles"
            else:
                cycles = 32
                cycles_source = "default"
        slot["cycles"] = cycles
        slot["cycles_source"] = cycles_source
        slot["file"] = p.name
        slot["label"] = (
            manifest_slots[i].get("label")
            if i < len(manifest_slots) and manifest_slots[i].get("label")
            else p.stem
        )
        slot["duration_s"] = round(cycles / slot["cps"], 1)
        slot_results.append(slot)

    return slot_results, manifest


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    args = [a for a in args if a != "--json"]
    if not args:
        print(__doc__)
        return 1
    track_id = args[0]
    try:
        slot_results, manifest = analyze_track(track_id)
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 1

    if as_json:
        print(json.dumps(slot_results, indent=2))
        return 0

    total_secs = sum(s["duration_s"] for s in slot_results)
    print(f"\n  ╔═ {track_id} ".ljust(82, "═") + "╗")
    print(f"  ║  {len(slot_results)} slots · {total_secs:.0f}s total · cps {slot_results[0]['cps']}".ljust(81) + "║")
    print(f"  ╚".ljust(81, "═") + "╝")

    peak_gain = max(s["total_gain"] for s in slot_results) or 1
    min_gain  = min(s["total_gain"] for s in slot_results) or 0.01
    dyn_ratio = peak_gain / max(min_gain, 0.01)

    print(f"  {'slot':<22} {'voices':>6} {'gain':>5} {'dens':>5} {'lpfHz':>6} {'cycles':>7} {'predicted dynamic':>30}")
    print("  " + "-" * 90)
    for s in slot_results:
        cycles_mark = "·" if s["cycles_source"] == "default" else "✓"
        print(
            f"  {s['label'][:22]:<22} {s['voice_count']:>6} {s['total_gain']:>5.2f} "
            f"{s['total_density']:>5.1f} {s['avg_lpf_hz']:>6} "
            f"{s['cycles']:>3}{cycles_mark}  {bar(s['total_gain'], peak_gain)}"
        )

    print("\n  ── dynamics ──")
    print(f"  predicted total-gain ratio: {dyn_ratio:.1f}× (min {min_gain:.2f}, peak {peak_gain:.2f})")
    print(f"  for context:")
    for ref, r in sorted(REF_DYN.items(), key=lambda kv: kv[1]):
        marker = "←  ~our track" if abs(r - dyn_ratio) <= 1 else ""
        print(f"    {ref:<28} {r:>4}× {marker}")

    print("\n  ── diagnosis ──")
    if dyn_ratio < 3:
        print("  ⚠ TOO FLAT — every slot has similar total gain. Lower gain values in slots 1 & 8 (intro/outro), raise in slot 7 (climax). References go 5–273×.")
    elif dyn_ratio < 8:
        print("  ✓ moderate dynamics — Bonobo/Floating Points range. Fine for sustained tracks.")
    elif dyn_ratio < 20:
        print("  ✓ strong dynamics — Kiasmos/DJRUM territory. Real builds and drops felt.")
    else:
        print("  ✓ extreme dynamics — Skee Mask/Reprise territory. Big silences AND big peaks.")

    # Voice-count progression — should generally rise then fall (build-strip arc)
    counts = [s["voice_count"] for s in slot_results]
    if max(counts) - min(counts) < 2:
        print(f"  ⚠ FLAT VOICE COUNT — all slots have {min(counts)}-{max(counts)} voices. Track doesn't build/strip.")
    elif counts == sorted(counts):
        print("  ⚠ MONOTONIC BUILD — voice count only grows. Add a strip-back slot (Bonobo arc requires it).")
    else:
        peak_idx = counts.index(max(counts))
        print(f"  ✓ build-strip arc: peaks at slot {peak_idx+1} ({counts[peak_idx]} voices) then strips back to {counts[-1]}")

    # Noise warning for tonal tracks
    if any(s["has_noise"] for s in slot_results):
        noise_slots = [i+1 for i, s in enumerate(slot_results) if s["has_noise"]]
        print(f"  · noise (s(\"white\")) present in slots {noise_slots} — strips 'tonal' Reprise vibe if that's your target")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

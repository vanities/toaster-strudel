#!/usr/bin/env python3
"""Per-track playback gain — loudness normalization for the rotation.

The radio plays tracks back-to-back, all synthesized live in the browser, so
any loudness mismatch between tracks is a volume lurch on every hop. This tool
computes one playback gain per track and writes it into the track's
manifest.json as "playbackGain"; both players (lab web app + toaster-radio)
route output through a master GainNode and apply it on track switch. Within-
track dynamics are untouched — this is leveling between tracks, not compression.

Two methods, best available wins:

  measured   integrated LUFS (ITU-R BS.1770 via pyloudnorm) from a rendered
             WAV. Render via the player's offline render (⏺) — it POSTs to
             the server's /save-wav and lands in /tmp/strudel-renders/<id>.wav.
             Gain = target − LUFS, clamped to ±12 dB.

  predicted  (--predict) static fallback for unrendered tracks: the cycle-
             weighted mean of per-section total_gain from analyze-patterns.
             Anchored to measured tracks when any exist (median offset),
             otherwise to the rotation's median (pure relative leveling).
             Clamped to ±6 dB and marked "method": "predicted" so a later
             measured pass overrides it.

Usage:
  uv run python3 tools/loudness.py                       # measured only, all tracks
  uv run python3 tools/loudness.py --predict             # + static fallback
  uv run python3 tools/loudness.py --dry-run --predict   # table only, no writes
  uv run python3 tools/loudness.py v2-gen/crank-glade    # specific track(s)
  uv run python3 tools/loudness.py --target -16          # default -14 LUFS
"""

import importlib.util
import json
import math
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACKS_DIR = ROOT / "tracks"
WAV_DIR_DEFAULT = Path("/tmp/strudel-renders")

_here = Path(__file__).resolve().parent


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, _here / fname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ap = _load("analyze_patterns", "analyze-patterns.py")
ev = _load("eval_tracks", "eval-tracks.py")

MEASURED_CLAMP_DB = 12.0
PREDICTED_CLAMP_DB = 6.0


def wav_for(track_id, wav_dir):
    """Map a track id to its rendered WAV. /save-wav sanitizes the name the
    same way ("v2-gen/crank-glade" -> v2-gen_crank-glade.wav); also accept the
    bare id for hand-saved renders."""
    safe = re.sub(r"[^a-zA-Z0-9_.-]", "_", track_id)
    bare = track_id.split("/")[-1]
    for cand in (f"{safe}.wav", f"{bare}.wav"):
        p = wav_dir / cand
        if p.exists():
            return p
    return None


def measure_lufs(path):
    import soundfile as sf
    import pyloudnorm as pyln

    t0 = time.perf_counter()
    data, rate = sf.read(str(path), always_2d=True)
    lufs = pyln.Meter(rate).integrated_loudness(data)
    ms = (time.perf_counter() - t0) * 1000
    print(f"  [loudness] measured {path.name}: {lufs:.1f} LUFS ({data.shape[0]/rate:.0f}s in {ms:.0f}ms)", file=sys.stderr)
    return lufs


def predicted_proxy(track_id):
    """Cycle-weighted mean of per-section total_gain — a crude loudness proxy
    (ignores density/filtering/sample content). Good enough for relative
    leveling; superseded by any measured LUFS."""
    slots, _ = ap.analyze_track(track_id)
    num = sum(s["total_gain"] * s["cycles"] for s in slots)
    den = sum(s["cycles"] for s in slots) or 1
    return num / den


def gain_for(delta_db, clamp_db):
    delta_db = max(-clamp_db, min(clamp_db, delta_db))
    return 10 ** (delta_db / 20), delta_db


def write_manifest(track_id, gain, lufs, method, target, dry_run):
    tdir = TRACKS_DIR / track_id
    mpath = tdir / "manifest.json"
    manifest = ap.load_manifest(tdir)
    manifest["playbackGain"] = round(gain, 3)
    manifest["loudness"] = {
        "lufs": round(lufs, 1) if lufs is not None else None,
        "method": method,
        "target": target,
        "date": time.strftime("%Y-%m-%d"),
    }
    if dry_run:
        return
    mpath.write_text(json.dumps(manifest, indent=2) + "\n")


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    predict = "--predict" in args
    target = -14.0
    if "--target" in args:
        target = float(args[args.index("--target") + 1])
    wav_dir = WAV_DIR_DEFAULT
    if "--wav-dir" in args:
        wav_dir = Path(args[args.index("--wav-dir") + 1])
    track_args = [
        a for i, a in enumerate(args)
        if not a.startswith("--") and args[i - 1] not in ("--target", "--wav-dir")
    ]

    track_ids = track_args or ev.discover_tracks()
    if not track_ids:
        print("no tracks found", file=sys.stderr)
        return 1

    t0 = time.perf_counter()
    measured = {}   # id -> lufs
    proxies = {}    # id -> static proxy
    for tid in track_ids:
        wav = wav_for(tid, wav_dir)
        if wav:
            measured[tid] = measure_lufs(wav)
        try:
            proxies[tid] = predicted_proxy(tid)
        except FileNotFoundError:
            pass

    # Anchor for predicted tracks: prefer the measured/proxy overlap, else the
    # rotation median (relative leveling — absolute target unknowable unrendered).
    offset_db = None
    overlap = [tid for tid in measured if tid in proxies and proxies[tid] > 0]
    if overlap:
        diffs = sorted(measured[t] - 20 * math.log10(proxies[t]) for t in overlap)
        offset_db = diffs[len(diffs) // 2]
        print(f"  [loudness] proxy→LUFS offset {offset_db:+.1f} dB (from {len(overlap)} rendered tracks)", file=sys.stderr)
    elif predict:
        vals = sorted(p for p in proxies.values() if p > 0)
        if vals:
            median_proxy = vals[len(vals) // 2]
            offset_db = target - 20 * math.log10(median_proxy)
            print(f"  [loudness] no renders — anchoring rotation median to {target} LUFS (relative leveling only)", file=sys.stderr)

    rows = []
    for tid in track_ids:
        if tid in measured:
            lufs = measured[tid]
            gain, delta = gain_for(target - lufs, MEASURED_CLAMP_DB)
            rows.append((tid, "measured", lufs, gain, delta))
            write_manifest(tid, gain, lufs, "measured", target, dry_run)
        elif predict and tid in proxies and proxies[tid] > 0 and offset_db is not None:
            est_lufs = 20 * math.log10(proxies[tid]) + offset_db
            gain, delta = gain_for(target - est_lufs, PREDICTED_CLAMP_DB)
            rows.append((tid, "predicted", est_lufs, gain, delta))
            write_manifest(tid, gain, est_lufs, "predicted", target, dry_run)
        else:
            rows.append((tid, "skipped", None, None, None))

    print(f"\n  loudness — target {target} LUFS{' (DRY RUN)' if dry_run else ''}\n")
    for tid, method, lufs, gain, delta in rows:
        if method == "skipped":
            print(f"  · {tid:<28} no render{'' if predict else ' (use --predict for static fallback)'}")
        else:
            print(f"  {'✓' if method == 'measured' else '~'} {tid:<28} {lufs:>6.1f} LUFS  gain {gain:>5.3f} ({delta:+.1f} dB)  [{method}]")

    done = sum(1 for r in rows if r[1] != "skipped")
    print(f"\n  {done}/{len(rows)} tracks {'previewed' if dry_run else 'written'} in {(time.perf_counter()-t0)*1000:.0f}ms")
    if not dry_run and done:
        print("  → re-publish the radio (toaster-radio: pnpm publish-tracks) to pick up gains")
    return 0


if __name__ == "__main__":
    sys.exit(main())

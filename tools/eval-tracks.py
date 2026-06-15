#!/usr/bin/env python3
"""Regression eval suite over the static track analyzer.

Promotes analyze-patterns.py's diagnosis heuristics from printed warnings to
hard assertions, and adds per-track baselines so an edit that flattens a
track's dynamics fails mechanically instead of getting discovered by ear
three tracks later. No audio render needed — this is static prediction, so
it's fast enough to run after every compose/iterate pass.

Checks per track (thresholds overridable via manifest.json "eval" object):

  contrast   predicted dynamic ratio (peak/min section gain) >= min_dyn (3.0)
  arc        voice-count spread >= min_voice_spread (2) and not monotonic —
             the track must build AND strip back
  build      the peak-gain section is not the first section
  baseline   per-section total_gain within tolerance (15%) of
             tools/eval-baselines.json; section count/files unchanged

Manifest overrides, e.g. an intentionally-flat ambient piece:

  "eval": { "min_dyn": 1.5, "allow_monotonic": true, "allow_flat": true }

Usage:
  uv run python3 tools/eval-tracks.py                     # every track
  uv run python3 tools/eval-tracks.py v2-gen/crank-glade  # specific track(s)
  uv run python3 tools/eval-tracks.py --update            # rewrite baselines
  uv run python3 tools/eval-tracks.py --json              # machine-readable

Exit code: 0 all pass, 1 any failure (CI-able).
"""

import importlib.util
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACKS_DIR = ROOT / "tracks"
BASELINES_PATH = ROOT / "tools" / "eval-baselines.json"
SKIP_DIRS = {"_scrapped"}

# analyze-patterns.py has a dash in its name — load it via importlib.
_spec = importlib.util.spec_from_file_location(
    "analyze_patterns", Path(__file__).resolve().parent / "analyze-patterns.py"
)
ap = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ap)

DEFAULTS = {
    "min_dyn": 3.0,            # analyzer's own "TOO FLAT" threshold
    "min_voice_spread": 2,     # analyzer's own flat-voice-count threshold
    "allow_monotonic": False,  # build-only arcs (no strip-back) fail by default
    "allow_flat": False,       # true = skip contrast/arc/build entirely
    "baseline_tolerance": 0.15,
}


def discover_tracks():
    """Track ids = any dir under tracks/ (depth 1 or 2) holding NN.strudel files."""
    ids = []

    def has_sections(d):
        # Strictly NN.strudel — track files like 01-dawn.strudel are NOT sections.
        return any(re.fullmatch(r"\d+\.strudel", p.name) for p in d.iterdir())

    for entry in sorted(TRACKS_DIR.iterdir()):
        if not entry.is_dir() or entry.name in SKIP_DIRS or entry.name.startswith("."):
            continue
        if has_sections(entry):
            ids.append(entry.name)  # loose track dir: tracks/<id>/
            continue
        for sub in sorted(entry.iterdir()):  # station dir: tracks/<station>/<id>/
            if sub.is_dir() and not sub.name.startswith(".") and has_sections(sub):
                ids.append(f"{entry.name}/{sub.name}")
    return ids


def eval_track(track_id, baselines):
    slots, manifest = ap.analyze_track(track_id)
    cfg = {**DEFAULTS, **(manifest.get("eval") or {})}

    gains = [s["total_gain"] for s in slots]
    counts = [s["voice_count"] for s in slots]
    peak = max(gains) or 1
    low = max(min(gains), 0.01)
    dyn_ratio = peak / low

    failures = []
    notes = []

    if not cfg["allow_flat"]:
        # contrast — sections must actually differ in level
        if dyn_ratio < cfg["min_dyn"]:
            failures.append(
                f"contrast: dyn {dyn_ratio:.1f}x < {cfg['min_dyn']}x — sections too similar (structural mush)"
            )
        # arc — build and strip-back in the voice counts
        spread = max(counts) - min(counts)
        if spread < cfg["min_voice_spread"]:
            failures.append(
                f"arc: voice spread {spread} < {cfg['min_voice_spread']} ({min(counts)}-{max(counts)} voices) — track doesn't build/strip"
            )
        elif counts == sorted(counts) and not cfg["allow_monotonic"]:
            failures.append("arc: voice count only grows — no strip-back section")
        # build — the loudest section shouldn't open the track
        if len(slots) > 1 and gains.index(max(gains)) == 0:
            failures.append("build: peak-gain section is the FIRST section — nothing builds")

    # baseline regression
    base = baselines.get(track_id)
    if base is None:
        notes.append("no baseline (new track — record with --update)")
    else:
        base_secs = base.get("sections", [])
        cur_files = [s["file"] for s in slots]
        if [b.get("file") for b in base_secs] != cur_files:
            failures.append(
                f"baseline: section layout changed ({len(base_secs)} -> {len(slots)} files) — re-record with --update if intended"
            )
        else:
            tol = cfg["baseline_tolerance"]
            for b, s in zip(base_secs, slots):
                bg = b.get("gain", 0)
                if bg and abs(s["total_gain"] - bg) / bg > tol:
                    failures.append(
                        f"baseline: {s['file']} gain {s['total_gain']:.2f} drifted >{tol:.0%} from {bg:.2f}"
                    )
                if b.get("voices") is not None and s["voice_count"] != b["voices"]:
                    failures.append(
                        f"baseline: {s['file']} voices {s['voice_count']} != {b['voices']}"
                    )

    return {
        "track": track_id,
        "sections": len(slots),
        "dyn_ratio": round(dyn_ratio, 1),
        "voices": f"{min(counts)}-{max(counts)}",
        "failures": failures,
        "notes": notes,
        "slots": [
            {"file": s["file"], "gain": s["total_gain"], "voices": s["voice_count"], "cycles": s["cycles"]}
            for s in slots
        ],
    }


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    update = "--update" in args
    track_args = [a for a in args if not a.startswith("--")]

    t0 = time.perf_counter()
    baselines = {}
    if BASELINES_PATH.exists():
        baselines = json.loads(BASELINES_PATH.read_text())

    track_ids = track_args or discover_tracks()
    if not track_ids:
        print("no tracks found", file=sys.stderr)
        return 1

    results = []
    errors = []
    for tid in track_ids:
        try:
            results.append(eval_track(tid, baselines))
        except FileNotFoundError as e:
            errors.append(f"{tid}: {e}")

    if update:
        for r in results:
            baselines[r["track"]] = {
                "dyn_ratio": r["dyn_ratio"],
                "sections": r["slots"],
            }
        BASELINES_PATH.write_text(json.dumps(baselines, indent=1, sort_keys=True) + "\n")

    failed = [r for r in results if r["failures"]]
    elapsed_ms = (time.perf_counter() - t0) * 1000

    if as_json:
        print(json.dumps({
            "passed": len(results) - len(failed),
            "failed": len(failed),
            "errors": errors,
            "duration_ms": round(elapsed_ms, 1),
            "tracks": results,
        }, indent=2))
        return 1 if failed or errors else 0

    print(f"\n  eval — {len(results)} tracks ({elapsed_ms:.0f}ms)\n")
    for r in results:
        mark = "✗" if r["failures"] else "✓"
        note = f"  · {'; '.join(r['notes'])}" if r["notes"] else ""
        print(f"  {mark} {r['track']:<28} {r['sections']:>2} sections  dyn {r['dyn_ratio']:>5.1f}x  voices {r['voices']}{note}")
        for f in r["failures"]:
            print(f"      ↳ {f}")
    for e in errors:
        print(f"  ! {e}")

    if update:
        print(f"\n  baselines written → {BASELINES_PATH.relative_to(ROOT)} ({len(baselines)} tracks)")
    if failed or errors:
        print(f"\n  FAIL — {len(failed)} of {len(results)} tracks failed" + (f", {len(errors)} errors" if errors else ""))
        return 1
    print(f"\n  PASS — all {len(results)} tracks clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())

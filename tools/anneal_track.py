#!/usr/bin/env python3
"""Anneal a track's sections toward a brightness arc, judged by the static analyzer.

The point: wire the existing analyzer in as an EXECUTABLE fitness function (not a
diagnostic you read), and let the creative-annealer search loop shape a real,
measurable property the track is missing.

`sunfade` has a fine *gain* arc (build-strip) but no *brightness* arc — its
filters barely move across the track. A producer would open the filter into the
bloom and close it on the intro/outro, leaving the sub-bass alone. We measure
**tonal brightness** = mean filter cutoff of the non-bass voices (lpf ≥ 400 Hz),
derive a per-section target from the track's own gain arc (louder ⇒ brighter),
then anneal each section toward its target while PRESERVING gain and never
touching the sub. Mechanical mutations + analyzer judge ⇒ fully offline, no API
key, no audio render. The win is a measured change in the analyzer's own numbers.

    python3 tools/anneal_track.py v2-gen/25-sunfade
    python3 tools/anneal_track.py v2-gen/25-sunfade --steps 120
"""

from __future__ import annotations

import argparse
import difflib
import importlib.util
import logging
import random
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent              # toaster-strudel/
TRACKS = ROOT / "tracks"
ANNEALER_SRC = ROOT.parent / "creative-annealer" / "src"   # sibling repo
sys.path.insert(0, str(ANNEALER_SRC))

from annealer import Candidate, Judgment, anneal, geometric, metropolis_accept  # noqa: E402
from annealer.frameworks.base import Move, MoveResult                           # noqa: E402

_spec = importlib.util.spec_from_file_location("analyze_patterns", ROOT / "tools" / "analyze-patterns.py")
analyzer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(analyzer)
analyze_slot = analyzer.analyze_slot   # (code) -> {voice_count,total_gain,avg_lpf_hz,...}

logging.getLogger("annealer").setLevel(logging.WARNING)

SUB_FLOOR = 400.0   # never touch filters below this — that's the sub-bass

LPF_NUM = re.compile(r"\.lpf\((\d+(?:\.\d+)?)\)")
LPF_RANGE = re.compile(r"\.lpf\(sine\.range\((\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?)\)")
GAIN_NUM = re.compile(r"\.gain\((\d+(?:\.\d+)?)\)")


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def _lpf_sites(code: str):
    """All editable lpf sites (value ≥ SUB_FLOOR) as (start, end, kind, value)."""
    sites = []
    for m in LPF_NUM.finditer(code):
        v = float(m.group(1))
        if v >= SUB_FLOOR:
            sites.append((m.start(), m.end(), "num", v))
    for m in LPF_RANGE.finditer(code):
        lo, hi = float(m.group(1)), float(m.group(2))
        if (lo + hi) / 2 >= SUB_FLOOR:
            sites.append((m.start(), m.end(), "range", (lo + hi) / 2))
    return sites


def _rewrite_site(frag: str, kind: str, factor: float) -> str:
    if kind == "num":
        v = float(LPF_NUM.match(frag).group(1))
        return f".lpf({int(_clamp(v * factor, SUB_FLOOR, 12000))})"
    lo, hi = (float(x) for x in LPF_RANGE.match(frag).groups())
    nlo = _clamp(lo * factor, SUB_FLOOR, 12000)
    nhi = max(nlo + 50, _clamp(hi * factor, SUB_FLOOR, 12000))
    return f".lpf(sine.range({int(nlo)},{int(nhi)})"


def _apply(code: str, sites, factor: float) -> str:
    """Rewrite the given sites (back-to-front so spans stay valid)."""
    for s, e, kind, _ in sorted(sites, key=lambda x: -x[0]):
        code = code[:s] + _rewrite_site(code[s:e], kind, factor) + code[e:]
    return code


def filter_sweep(direction: float):
    """A group filter automation: open (direction>0) or close every non-bass
    voice's cutoff at once — how a producer rides the filter into/out of a drop."""
    def move(text, llm, boldness, rng):
        sites = _lpf_sites(text)
        if not sites:
            return MoveResult(text, note="sweep·noop")
        if direction > 0:
            f = 1 + (0.15 + 0.85 * boldness) * rng.random()
        else:
            f = 1 - (0.10 + 0.45 * boldness) * rng.random()
        return MoveResult(_apply(text, sites, f), note=f"sweep {'↑' if direction > 0 else '↓'}×{f:.2f}")
    return move


def lpf_voice_nudge(text, llm, boldness, rng):
    sites = _lpf_sites(text)
    if not sites:
        return MoveResult(text, note="lpf·noop")
    one = [sites[rng.randrange(len(sites))]]
    f = 1 + (rng.random() - 0.4) * (0.4 + boldness)
    return MoveResult(_apply(text, one, f), note=f"voice-lpf×{f:.2f}")


def gain_nudge(text, llm, boldness, rng):
    sites = [(m.start(), m.end()) for m in GAIN_NUM.finditer(text)]
    if not sites:
        return MoveResult(text, note="gain·noop")
    s, e = sites[rng.randrange(len(sites))]
    v = float(GAIN_NUM.match(text[s:e]).group(1))
    f = 1 + (rng.random() - 0.5) * 0.25
    return MoveResult(text[:s] + f".gain({round(_clamp(v * f, 0.0, 1.0), 3)})" + text[e:], note=f"gain×{f:.2f}")


MOVES = [
    Move("filter_sweep_open", "strudel", "leap", filter_sweep(+1)),
    Move("filter_sweep_close", "strudel", "leap", filter_sweep(-1)),
    Move("lpf_voice_nudge", "strudel", "neutral", lpf_voice_nudge),
    Move("gain_nudge", "strudel", "refine", gain_nudge),
]


def tonal_brightness(code: str) -> float:
    """Mean filter cutoff of non-bass voices — what a listener hears as 'openness'."""
    vals = [v for _, _, _, v in _lpf_sites(code)]
    return sum(vals) / len(vals) if vals else 0.0


def make_judge(target_tb: float, orig: dict, orig_code: str):
    base_voices = orig["voice_count"]
    orig_gain = orig["total_gain"] or 0.01

    def judge(c: Candidate) -> Judgment:
        f = analyze_slot(c.text)
        coherence = 1.0 if f["voice_count"] == base_voices else 0.0
        bright = 1 - min(1.0, abs(tonal_brightness(c.text) - target_tb) / max(target_tb, 1))
        gain_keep = 1 - min(1.0, abs(f["total_gain"] - orig_gain) / orig_gain)
        novelty = 1 - difflib.SequenceMatcher(None, orig_code, c.text).ratio()
        total = coherence * (0.70 * bright + 0.25 * gain_keep + 0.05 * novelty)
        return Judgment(coherence=coherence, novelty=novelty, constraint_fit=gain_keep,
                        domain=bright, total=round(total, 4))

    return judge


def target_curve(gains, base=450.0, span=3000.0):
    g = max(gains) or 1.0
    return [base + span * (x / g) for x in gains]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("track")
    ap.add_argument("--steps", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    tdir = TRACKS / args.track
    sections = sorted(p for p in tdir.glob("*.strudel") if re.match(r"^\d+\.strudel$", p.name))
    if not sections:
        print(f"no NN.strudel sections in {tdir}", file=sys.stderr)
        return 1

    codes = [p.read_text() for p in sections]
    feats = [analyze_slot(c) for c in codes]
    tb0 = [tonal_brightness(c) for c in codes]
    targets = target_curve([f["total_gain"] for f in feats])

    out_dir = tdir.parent / (tdir.name + "__annealed")
    out_dir.mkdir(exist_ok=True)
    if (tdir / "manifest.json").exists():
        shutil.copy(tdir / "manifest.json", out_dir / "manifest.json")

    print(f"\n  annealing {len(sections)} sections of {args.track}  ({args.steps} steps each · analyzer judge · offline)\n")
    print(f"  {'section':<10} {'tonal-bright':>16} {'target':>7}   {'gain (preserved)':>20}")
    print("  " + "-" * 62)

    tb1, feats1 = [], []
    for i, (p, code, f0, t) in enumerate(zip(sections, codes, feats, targets)):
        res = anneal(
            seed=Candidate(text=code, note="seed"),
            moves=MOVES,
            judge=make_judge(t, f0, code),
            schedule=geometric(0.9, 0.93),
            steps=args.steps,
            accept=metropolis_accept,
            rng=random.Random(args.seed + i),
        )
        best = res.best.text
        (out_dir / p.name).write_text(best)
        tbn = tonal_brightness(best)
        fn = analyze_slot(best)
        tb1.append(tbn)
        feats1.append(fn)
        print(f"  {p.name:<10} {f'{tb0[i]:.0f}→{tbn:.0f}':>16} {int(t):>7}   "
              f"{f'{f0['total_gain']:.2f}→{fn['total_gain']:.2f}':>20}")

    def ratio(vals):
        vals = [v for v in vals if v]
        return (max(vals) / min(vals)) if vals and min(vals) else 0

    print("\n  ── result (analyzer's own numbers) ──")
    print(f"  brightness arc (tonal):   {ratio(tb0):.2f}×  →  {ratio(tb1):.2f}×   ← the fix: real spectral movement")
    print(f"  gain arc (must hold):     {ratio([f['total_gain'] for f in feats]):.2f}×  →  "
          f"{ratio([f['total_gain'] for f in feats1]):.2f}×")
    print(f"\n  candidates → {out_dir.relative_to(ROOT)}/   (audition; promote or delete)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

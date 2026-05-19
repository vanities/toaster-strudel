#!/usr/bin/env python3
"""Batch-analyze FLACs across multiple artists for skill updates.

Outputs JSON with per-track stats + per-artist aggregates.

Usage:  uv run --with librosa --with numpy tools/batch-analyze.py
"""
import json
import sys
from pathlib import Path
import numpy as np
import librosa

AUDIO_ROOT = Path.home() / "git/work/me/game/references/audio"

KEYS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Curated sample per artist — mix of singles + deep cuts for variety
SAMPLES = {
    "bonobo": [
        "Bonobo - Black Sands  Japanese Edition (2010) [CD FLAC] {BRC-255}/01. Prelude.flac",
        "Bonobo - Black Sands  Japanese Edition (2010) [CD FLAC] {BRC-255}/03. Kong.flac",
        "Bonobo - Black Sands  Japanese Edition (2010) [CD FLAC] {BRC-255}/04. Eyesdown.flac",
        "Bonobo - Black Sands  Japanese Edition (2010) [CD FLAC] {BRC-255}/07. 1009.flac",
        "Bonobo - Black Sands  Japanese Edition (2010) [CD FLAC] {BRC-255}/12. Black Sands.flac",
        "Bonobo - Black Sands  Japanese Edition (2010) [CD FLAC] {BRC-255}/11. Animals.flac",
    ],
    "djrum": [
        "Djrum - Portrait with Firewood (2018)/01 - Unblocked.flac",
        "Djrum - Portrait with Firewood (2018)/03 - Creature, Pt. 1.flac",
        "Djrum - Portrait with Firewood (2018)/04 - Creature, Pt. 2.flac",
        "Djrum - Portrait with Firewood (2018)/05 - Sex.flac",
        "Djrum - Under Tangled Silence (2025) - WEB FLAC/07. Reprise.flac",
        "Djrum - Under Tangled Silence (2025) - WEB FLAC/02. Waxcap.flac",
        "Djrum - Under Tangled Silence (2025) - WEB FLAC/05. Hold.flac",
    ],
    "floating_points": [
        "Floating Points - Crush (2019) [FLAC] {ZENCD259}/02 - Last Bloom.flac",
        "Floating Points - Crush (2019) [FLAC] {ZENCD259}/06 - LesAlpx.flac",
        "Floating Points - Crush (2019) [FLAC] {ZENCD259}/04 - Requiem for CS70 and Strings.flac",
        "Floating Points - Cascade (2024) [ZENDNL303] [WEB FLAC]/03 - Floating Points - Birth4000.flac",
        "Floating Points - Cascade (2024) [ZENDNL303] [WEB FLAC]/07 - Floating Points - Afflecks Palace.flac",
        "Floating Points - Reflections - Mojave Desert (2017) {LBOP5041 CD} [FLAC]/01 Mojave Desert.flac",
        "Floating Points - Reflections - Mojave Desert (2017) {LBOP5041 CD} [FLAC]/04 Kelso Dunes.flac",
    ],
    "kiasmos": [
        "Kiasmos - Kiasmos (2014) ERATP062CD [flac]/01. Lit.flac",
        "Kiasmos - Kiasmos (2014) ERATP062CD [flac]/02. Held.flac",
        "Kiasmos - Kiasmos (2014) ERATP062CD [flac]/03. Looped.flac",
        "Kiasmos - Kiasmos (2014) ERATP062CD [flac]/04. Swayed.flac",
        "Kiasmos - Kiasmos (2014) ERATP062CD [flac]/05. Thrown.flac",
        "Kiasmos - Kiasmos (2014) ERATP062CD [flac]/07. Bent.flac",
    ],
    "skee_mask": [
        "Skee Mask - Compro (2018) {Ilian Tape - ITLP04} [WEB 16-48 FLAC]/03 - Skee Mask - Rev8617.flac",
        "Skee Mask - Compro (2018) {Ilian Tape - ITLP04} [WEB 16-48 FLAC]/09 - Skee Mask - Flyby VFR.flac",
        "Skee Mask - Compro (2018) {Ilian Tape - ITLP04} [WEB 16-48 FLAC]/05 - Skee Mask - Via Sub Mids.flac",
        "Skee Mask - Pool [2021] [WEB-FLAC]/Skee Mask - ITLP09 Skee Mask - Pool - 03 LFO.flac",
        "Skee Mask - Pool [2021] [WEB-FLAC]/Skee Mask - ITLP09 Skee Mask - Pool - 08 Breathing Method.flac",
        "Skee Mask - Resort (2024 WF)/04 - Skee Mask - Element.flac",
        "Skee Mask - Resort (2024 WF)/11 - Skee Mask - 7AM At The Rodeo.flac",
    ],
}


def analyze(path: Path) -> dict:
    y, sr = librosa.load(str(path), sr=22050, mono=True)
    dur = librosa.get_duration(y=y, sr=sr)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(np.atleast_1d(tempo)[0])
    hop = sr * 5
    rms = librosa.feature.rms(y=y, frame_length=hop, hop_length=hop)[0]
    sc = librosa.feature.spectral_centroid(y=y, sr=sr)[0].mean()
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
    flatness = librosa.feature.spectral_flatness(y=y).mean()
    onsets = librosa.onset.onset_detect(y=y, sr=sr, units="time")
    rms_min = float(rms.min())
    rms_max = float(rms.max())
    return {
        "track": path.name,
        "duration_s": round(float(dur), 1),
        "bpm": round(tempo, 1),
        "key": KEYS[int(np.argmax(chroma))],
        "centroid_hz": int(round(float(sc))),
        "flatness": round(float(flatness), 4),
        "onsets_per_s": round(len(onsets) / max(dur, 0.01), 2),
        "rms_min": round(rms_min, 4),
        "rms_max": round(rms_max, 4),
        "dyn_x": round(rms_max / max(rms_min, 0.0001), 1),
    }


def aggregate(tracks: list[dict]) -> dict:
    bpms = [t["bpm"] for t in tracks]
    cs = [t["centroid_hz"] for t in tracks]
    fs = [t["flatness"] for t in tracks]
    os_ = [t["onsets_per_s"] for t in tracks]
    dx = [t["dyn_x"] for t in tracks]
    keys = [t["key"] for t in tracks]
    key_counts = {k: keys.count(k) for k in set(keys)}
    return {
        "n": len(tracks),
        "bpm_range": [min(bpms), max(bpms)],
        "bpm_median": float(np.median(bpms)),
        "centroid_range": [min(cs), max(cs)],
        "centroid_median": int(np.median(cs)),
        "flatness_range": [min(fs), max(fs)],
        "flatness_median": float(np.median(fs)),
        "onsets_range": [min(os_), max(os_)],
        "onsets_median": float(np.median(os_)),
        "dyn_range": [min(dx), max(dx)],
        "dyn_median": float(np.median(dx)),
        "key_counts": dict(sorted(key_counts.items(), key=lambda kv: -kv[1])),
    }


def main():
    result = {}
    for artist, files in SAMPLES.items():
        print(f"=== {artist} ===", file=sys.stderr)
        tracks = []
        for rel in files:
            path = AUDIO_ROOT / rel
            if not path.exists():
                print(f"  MISSING: {rel}", file=sys.stderr)
                continue
            print(f"  {path.name}", file=sys.stderr)
            try:
                tracks.append(analyze(path))
            except Exception as e:
                print(f"  ERROR: {e}", file=sys.stderr)
        result[artist] = {
            "tracks": tracks,
            "aggregate": aggregate(tracks) if tracks else None,
        }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Measure a rendered WAV with the same librosa features the reference cards use
(centroid, flatness, onset density, dynamic range, duration, peak) — the "ears"
readout. Compare these to a target track's card to catch harsh/cluttered/flat.

    tools/.venv-transcribe/bin/python tools/measure-wav.py <file.wav>
"""
import sys
import json
import numpy as np
import librosa

path = sys.argv[1]
y, sr = librosa.load(path, sr=22050, mono=True)
dur = float(librosa.get_duration(y=y, sr=sr))
hop = sr * 5
rms = librosa.feature.rms(y=y, frame_length=hop, hop_length=hop)[0]
sc = float(librosa.feature.spectral_centroid(y=y, sr=sr)[0].mean())
flat = float(librosa.feature.spectral_flatness(y=y).mean())
onsets = librosa.onset.onset_detect(y=y, sr=sr, units="time")
rmn, rmx = float(rms.min()), float(rms.max())
peak = float(np.max(np.abs(y))) if len(y) else 0.0
out = {
    "duration_s": round(dur, 1),
    "centroid_hz": int(round(sc)),
    "flatness": round(flat, 4),
    "onsets_per_s": round(len(onsets) / max(dur, 0.01), 2),
    "dyn_x": round(rmx / max(rmn, 0.0001), 1),
    "peak": round(peak, 4),
    "verdict": "ALL_ZERO" if peak == 0 else "NEAR_SILENT" if peak < 0.001 else "HAS_AUDIO",
}
print(json.dumps(out, indent=2))

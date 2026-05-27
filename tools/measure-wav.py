#!/usr/bin/env python3
"""Measure a rendered WAV with the same librosa features the reference cards use
(centroid, flatness, onset density, dynamic range, duration, peak, rms) — the "ears"
readout. Compare these to a target track's card to catch harsh/cluttered/flat.

The verdict is also the LOUDNESS review: Strudel doesn't auto-normalise, so a track
mixed with conservative per-voice gains peaks well below full scale and reads SOFT
(headroom unused). A healthy master peaks ~0.6-0.95. The verdict flags TOO_SOFT (under
~0.5) and CLIPPING (>=0.98) so an under- or over-leveled mix doesn't slip through.

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
rms_mean = float(rms.mean()) if len(rms) else 0.0

# Loudness review (headroom check). Healthy master peak ~0.6-0.95; below ~0.5 the mix
# is leaving the top of the range unused and reads soft; >=0.98 it's at/over full scale.
SOFT_PEAK, CLIP_PEAK = 0.5, 0.98
if peak == 0:
    verdict = "ALL_ZERO"
elif peak < 0.001:
    verdict = "NEAR_SILENT"
elif peak < SOFT_PEAK:
    verdict = "TOO_SOFT"      # under-using headroom — push the per-voice gains up
elif peak >= CLIP_PEAK:
    verdict = "CLIPPING"      # at/over full scale — pull gains down (or limit)
else:
    verdict = "HAS_AUDIO"

out = {
    "duration_s": round(dur, 1),
    "centroid_hz": int(round(sc)),
    "flatness": round(flat, 4),
    "onsets_per_s": round(len(onsets) / max(dur, 0.01), 2),
    "dyn_x": round(rmx / max(rmn, 0.0001), 1),
    "peak": round(peak, 4),
    "rms": round(rms_mean, 4),
    "verdict": verdict,
}
print(json.dumps(out, indent=2))

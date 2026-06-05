#!/usr/bin/env python3
"""Precompute compact per-video-frame audio features for Blender animation."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile


def smooth(x: np.ndarray, radius: int) -> np.ndarray:
    if radius <= 0:
        return x.astype(np.float32)
    k = np.hanning(radius * 2 + 3).astype(np.float32)
    k /= k.sum()
    return np.convolve(x, k, mode="same").astype(np.float32)


def robust_norm(x: np.ndarray, lo=8, hi=97, gamma=0.75) -> np.ndarray:
    x = np.asarray(x, dtype=np.float32)
    a, b = float(np.percentile(x, lo)), float(np.percentile(x, hi))
    if b <= a + 1e-9:
        return np.zeros_like(x)
    y = np.clip((x - a) / (b - a), 0, 1)
    return np.power(y, gamma).astype(np.float32)


def band(freqs: np.ndarray, mag: np.ndarray, a: float, b: float) -> np.ndarray:
    mask = (freqs >= a) & (freqs < b)
    if not np.any(mask):
        return np.zeros(mag.shape[1], dtype=np.float32)
    return mag[mask].mean(axis=0).astype(np.float32)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("audio")
    p.add_argument("--output", required=True)
    p.add_argument("--fps", type=int, default=24)
    args = p.parse_args()
    audio_path = Path(args.audio).expanduser().resolve()
    sr, data = wavfile.read(audio_path)
    if data.ndim == 1:
        data = np.column_stack([data, data])
    if np.issubdtype(data.dtype, np.integer):
        stereo = data[:, :2].astype(np.float32) / float(np.iinfo(data.dtype).max)
    else:
        stereo = data[:, :2].astype(np.float32)
    mono = stereo.mean(axis=1)
    duration = len(mono) / sr
    n_frames = int(math.ceil(duration * args.fps))
    frame_times = np.arange(n_frames, dtype=np.float32) / args.fps

    # RMS at frame cadence.
    half = max(128, int(sr * 0.030))
    sq = mono * mono
    cs = np.concatenate([[0.0], np.cumsum(sq, dtype=np.float64)])
    centers = np.clip((frame_times * sr).astype(np.int64), 0, len(mono) - 1)
    starts = np.maximum(0, centers - half)
    ends = np.minimum(len(mono), centers + half)
    rms = np.sqrt((cs[ends] - cs[starts]) / np.maximum(1, ends - starts))
    rms = smooth(robust_norm(rms, 5, 97, 0.65), max(1, args.fps // 10))

    freqs, times, zxx = signal.stft(mono, fs=sr, window="hann", nperseg=4096, noverlap=3072, boundary=None, padded=False)  # type: ignore[arg-type]
    mag = np.log1p(np.abs(zxx).astype(np.float32) * 80.0)
    bass = np.interp(frame_times, times, robust_norm(band(freqs, mag, 45, 180), 6, 97, 0.70)).astype(np.float32)
    mid = np.interp(frame_times, times, robust_norm(band(freqs, mag, 250, 2200), 6, 97, 0.75)).astype(np.float32)
    high = np.interp(frame_times, times, robust_norm(band(freqs, mag, 2400, 10500), 8, 98, 0.70)).astype(np.float32)
    diff = np.maximum(0.0, np.diff(mag, axis=1, prepend=mag[:, :1]))
    flux = np.interp(frame_times, times, robust_norm(diff.mean(axis=0), 20, 99, 0.60)).astype(np.float32)
    rms_delta = np.maximum(0, np.diff(rms, prepend=rms[:1]))
    flux = robust_norm(flux * 0.82 + robust_norm(rms_delta, 50, 99, 0.55) * 0.32, 5, 99, 0.75)
    out = {
        "source": str(audio_path),
        "sr": sr,
        "duration": duration,
        "fps": args.fps,
        "frames": n_frames,
        "rms": smooth(rms, 1).round(5).tolist(),
        "bass": smooth(bass, 2).round(5).tolist(),
        "mid": smooth(mid, 2).round(5).tolist(),
        "high": smooth(high, 1).round(5).tolist(),
        "flux": smooth(flux, 1).round(5).tolist(),
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(out))
    print(f"wrote {args.output}: duration={duration:.2f}s frames={n_frames} fps={args.fps}")
    print("feature ranges:", {k: [float(np.min(out[k])), float(np.max(out[k]))] for k in ["rms", "bass", "mid", "high", "flux"]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

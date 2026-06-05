#!/usr/bin/env python3
"""Audio-reactive MP4 visualizer for WAV/AIFF/MP3/etc.

Creates a glowing, beat-synced "enchanted glade / spectral portal" music video by
analyzing RMS, onset flux, spectral centroid, and log-spaced frequency bands, then
streaming generated RGB frames into ffmpeg with the original audio muxed in.

Example:
  .venv-vis/bin/python tools/audio_reactive_visualizer.py \
    /Users/vanities/Downloads/v2-gen_crank-glade.wav \
    --output /Users/vanities/Downloads/v2-gen_crank-glade_visuals.mp4 \
    --fps 24 --width 1280 --height 720 --crf 18
"""
from __future__ import annotations

import argparse
import colorsys
import math
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image, ImageDraw  # type: ignore[import-not-found]
from scipy import signal
from scipy.io import wavfile


@dataclass
class Features:
    sr: int
    audio: np.ndarray  # mono float32 [-1, 1]
    stereo: np.ndarray  # shape [n, 2]
    duration: float
    frame_times: np.ndarray
    rms: np.ndarray
    sub: np.ndarray
    bass: np.ndarray
    lowmid: np.ndarray
    mid: np.ndarray
    high: np.ndarray
    air: np.ndarray
    flux: np.ndarray
    centroid: np.ndarray
    spec: np.ndarray  # [n_frames, n_bins]
    peaks: np.ndarray  # peak times


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr, flush=True)


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def smooth_1d(x: np.ndarray, radius: int) -> np.ndarray:
    if radius <= 0:
        return x.astype(np.float32, copy=False)
    k = np.hanning(radius * 2 + 3).astype(np.float32)
    k /= k.sum()
    return np.convolve(x, k, mode="same").astype(np.float32)


def robust_norm(x: np.ndarray, lo: float = 8, hi: float = 96, gamma: float = 0.75) -> np.ndarray:
    x = np.asarray(x, dtype=np.float32)
    a = float(np.percentile(x, lo))
    b = float(np.percentile(x, hi))
    if not np.isfinite(a) or not np.isfinite(b) or b <= a + 1e-9:
        return np.zeros_like(x, dtype=np.float32)
    y = np.clip((x - a) / (b - a), 0, 1)
    if gamma != 1:
        y = np.power(y, gamma)
    return y.astype(np.float32)


def load_audio(path: Path) -> tuple[int, np.ndarray, np.ndarray]:
    sr, data = wavfile.read(path)
    if data.ndim == 1:
        data = np.column_stack([data, data])
    data = data[:, :2]
    if np.issubdtype(data.dtype, np.integer):
        max_abs = float(np.iinfo(data.dtype).max)
        stereo = data.astype(np.float32) / max_abs
    else:
        stereo = data.astype(np.float32)
    stereo = np.nan_to_num(stereo, nan=0.0, posinf=0.0, neginf=0.0)
    stereo = np.clip(stereo, -1.0, 1.0)
    mono = stereo.mean(axis=1).astype(np.float32)
    return sr, mono, stereo


def band_energy(freqs: np.ndarray, mag: np.ndarray, f0: float, f1: float) -> np.ndarray:
    mask = (freqs >= f0) & (freqs < f1)
    if not np.any(mask):
        return np.zeros(mag.shape[1], dtype=np.float32)
    return mag[mask].mean(axis=0).astype(np.float32)


def compute_features(audio_path: Path, fps: int, n_spec_bins: int = 72) -> Features:
    eprint(f"Analyzing audio: {audio_path}")
    sr, mono, stereo = load_audio(audio_path)
    duration = len(mono) / sr
    n_frames = int(math.ceil(duration * fps))
    frame_times = np.arange(n_frames, dtype=np.float32) / float(fps)

    # RMS envelope at video-frame cadence.
    half = max(128, int(sr * 0.028))
    rms = np.empty(n_frames, dtype=np.float32)
    absmono = np.abs(mono)
    cumsum = np.concatenate([[0.0], np.cumsum(absmono * absmono, dtype=np.float64)])
    centers = np.clip((frame_times * sr).astype(np.int64), 0, len(mono) - 1)
    starts = np.maximum(0, centers - half)
    ends = np.minimum(len(mono), centers + half)
    spans = np.maximum(1, ends - starts)
    rms[:] = np.sqrt((cumsum[ends] - cumsum[starts]) / spans)
    rms = smooth_1d(robust_norm(rms, 5, 97, 0.70), max(1, fps // 14))

    # STFT for frequency-aware motion. 2048 hop is enough for visuals and keeps analysis fast.
    nperseg = 4096
    hop = 1024
    freqs, stft_times, zxx = signal.stft(
        mono,
        fs=sr,
        window="hann",
        nperseg=nperseg,
        noverlap=nperseg - hop,
        boundary=None,  # type: ignore[arg-type]
        padded=False,
    )
    mag = np.abs(zxx).astype(np.float32)
    mag_dbish = np.log1p(mag * 80.0).astype(np.float32)

    raw_bands = {
        "sub": band_energy(freqs, mag_dbish, 24, 70),
        "bass": band_energy(freqs, mag_dbish, 70, 240),
        "lowmid": band_energy(freqs, mag_dbish, 240, 700),
        "mid": band_energy(freqs, mag_dbish, 700, 2200),
        "high": band_energy(freqs, mag_dbish, 2200, 7200),
        "air": band_energy(freqs, mag_dbish, 7200, min(18000, sr / 2)),
    }

    bands: dict[str, np.ndarray] = {}
    for name, values in raw_bands.items():
        values = robust_norm(values, 6, 97, 0.72)
        bands[name] = np.interp(frame_times, stft_times, values, left=values[0], right=values[-1]).astype(np.float32)
        bands[name] = smooth_1d(bands[name], max(1, fps // 20))

    # Spectral centroid normalized to 0..1, weighted by magnitude.
    denom = mag.sum(axis=0) + 1e-9
    centroid_raw = ((freqs[:, None] * mag).sum(axis=0) / denom).astype(np.float32)
    centroid_raw = np.clip(centroid_raw / 7000.0, 0, 1)
    centroid = np.interp(frame_times, stft_times, centroid_raw, left=centroid_raw[0], right=centroid_raw[-1]).astype(np.float32)
    centroid = smooth_1d(centroid, max(1, fps // 8))

    # Spectral flux / onset-ish energy.
    diff = np.maximum(0.0, np.diff(mag_dbish, axis=1, prepend=mag_dbish[:, :1]))
    flux_raw = robust_norm(diff.mean(axis=0), 15, 99, 0.65)
    flux = np.interp(frame_times, stft_times, flux_raw, left=flux_raw[0], right=flux_raw[-1]).astype(np.float32)
    # Blend in positive RMS delta to catch full-band hits.
    rms_delta = np.maximum(0, np.diff(rms, prepend=rms[:1]))
    flux = robust_norm(flux * 0.82 + robust_norm(rms_delta, 50, 99, 0.55) * 0.35, 5, 99, 0.78)
    flux = smooth_1d(flux, 1)

    # Log frequency bins for radial mandala / spectrum petals.
    edges = np.geomspace(35, min(17500, sr / 2), n_spec_bins + 1)
    spec_rows = []
    for a, b in zip(edges[:-1], edges[1:]):
        row = band_energy(freqs, mag_dbish, float(a), float(b))
        row = robust_norm(row, 8, 98, 0.62)
        spec_rows.append(np.interp(frame_times, stft_times, row, left=row[0], right=row[-1]).astype(np.float32))
    spec = np.stack(spec_rows, axis=1).astype(np.float32)
    # Gentle temporal smoothing per bin.
    if fps >= 20:
        for i in range(spec.shape[1]):
            spec[:, i] = smooth_1d(spec[:, i], 1)

    # Peak picking with a refractory period.
    local = (flux > np.roll(flux, 1)) & (flux >= np.roll(flux, -1)) & (flux > 0.60)
    peak_indices = np.flatnonzero(local)
    filtered = []
    last_t = -10.0
    for idx in peak_indices:
        t = float(frame_times[idx])
        if t - last_t >= 0.18:
            filtered.append(t)
            last_t = t
        elif filtered and flux[idx] > flux[int(filtered[-1] * fps)]:
            filtered[-1] = t
            last_t = t
    peaks = np.array(filtered, dtype=np.float32)
    eprint(f"Audio duration: {duration:.2f}s, frames: {n_frames}, detected peaks: {len(peaks)}")

    return Features(
        sr=sr,
        audio=mono,
        stereo=stereo,
        duration=duration,
        frame_times=frame_times,
        rms=rms,
        sub=bands["sub"],
        bass=bands["bass"],
        lowmid=bands["lowmid"],
        mid=bands["mid"],
        high=bands["high"],
        air=bands["air"],
        flux=flux,
        centroid=centroid,
        spec=spec,
        peaks=peaks,
    )


def hsv255(h: float, s: float, v: float, a: int = 255) -> tuple[int, int, int, int]:
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, clamp01(s), clamp01(v))
    return int(r * 255), int(g * 255), int(b * 255), int(a)


def make_background_grid(w: int, h: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    y, x = np.mgrid[-1:1:complex(0, h), -1:1:complex(0, w)]
    x = x.astype(np.float32) * (w / h)
    y = y.astype(np.float32)
    r = np.sqrt(x * x + y * y).astype(np.float32)
    a = np.arctan2(y, x).astype(np.float32)
    return x, y, r, a


def render_background(
    x: np.ndarray,
    y: np.ndarray,
    r: np.ndarray,
    a: np.ndarray,
    t: float,
    rms: float,
    bass: float,
    mid: float,
    high: float,
    centroid: float,
) -> Image.Image:
    # Layered procedural glade: mist, portal glow, bark-like interference, aurora wash.
    phase = t * (0.12 + 0.18 * mid)
    swirl = np.sin(8.5 * r - 2.7 * a + phase * 4.0 + 1.4 * np.sin(y * 3.0 + phase))
    bark = np.sin(11.0 * (x * math.cos(phase) + y * math.sin(phase)) + 2.2 * np.sin(a * 5.0 - phase * 2.0))
    canopy = np.sin(5.0 * y + 2.0 * np.sin(3.0 * x + phase * 3.0))
    portal = np.exp(-((r - (0.46 + 0.08 * bass)) ** 2) * (22.0 - 6.0 * rms))
    core = np.exp(-(r**2) * (2.8 - 0.9 * bass))
    vignette = np.clip(1.25 - r * 0.85, 0, 1)

    teal = 38 + 52 * core + 65 * portal + 18 * bark
    green = 44 + 105 * core + 80 * portal + 34 * canopy + 18 * mid
    blue = 72 + 120 * portal + 56 * swirl + 45 * high + 28 * centroid
    red = 10 + 37 * portal + 18 * rms + 12 * np.sin(a * 3.0 + phase)

    # Electric veins appear with high-frequency detail.
    veins = np.maximum(0.0, np.sin(18.0 * r + 9.0 * a - phase * 8.0)) ** 18
    red += veins * 70 * high
    green += veins * 180 * high
    blue += veins * 150 * high

    arr = np.dstack([red, green, blue]) * vignette[..., None]
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, mode="RGB")


def sample_audio_window(stereo: np.ndarray, sr: int, t: float, seconds: float, n: int) -> np.ndarray:
    end = int(t * sr)
    start = max(0, end - int(seconds * sr))
    if end <= start + 8:
        return np.zeros((n, 2), dtype=np.float32)
    idx = np.linspace(start, end - 1, n).astype(np.int64)
    return stereo[idx]


def draw_polyline_glow(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[float, float]],
    color: tuple[int, int, int, int],
    width: int,
    glow: int = 3,
) -> None:
    if len(points) < 2:
        return
    r, g, b, a = color
    for k in range(glow, 0, -1):
        draw.line(points, fill=(r, g, b, max(10, a // (k + 2))), width=width + k * 5, joint="curve")
    draw.line(points, fill=color, width=width, joint="curve")


def draw_temple_rune(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    scale: float,
    angle: float,
    color: tuple[int, int, int, int],
    kind: int,
) -> None:
    """Draw tiny pseudo-Hylian / forest-temple glyph strokes."""
    ca = math.cos(angle)
    sa = math.sin(angle)

    def tr(px: float, py: float) -> tuple[float, float]:
        return (x + (px * ca - py * sa) * scale, y + (px * sa + py * ca) * scale)

    if kind % 5 == 0:
        pts = [tr(-0.45, 0.35), tr(0.0, -0.45), tr(0.45, 0.35), tr(-0.45, 0.35)]
        draw.line(pts, fill=color, width=max(1, int(scale * 0.09)))
        draw.line([tr(0, -0.45), tr(0, 0.5)], fill=color, width=max(1, int(scale * 0.08)))
    elif kind % 5 == 1:
        draw.arc((x - scale * 0.45, y - scale * 0.45, x + scale * 0.45, y + scale * 0.45), 25, 315, fill=color, width=max(1, int(scale * 0.08)))
        draw.line([tr(-0.1, -0.4), tr(0.32, 0.1), tr(-0.25, 0.45)], fill=color, width=max(1, int(scale * 0.08)))
    elif kind % 5 == 2:
        draw.line([tr(-0.42, -0.35), tr(0.42, -0.35), tr(-0.2, 0.05), tr(0.3, 0.42)], fill=color, width=max(1, int(scale * 0.08)))
    elif kind % 5 == 3:
        draw.line([tr(0, -0.5), tr(0, 0.5)], fill=color, width=max(1, int(scale * 0.08)))
        draw.line([tr(-0.35, -0.12), tr(0, 0.1), tr(0.35, -0.12)], fill=color, width=max(1, int(scale * 0.08)))
        draw.line([tr(-0.25, 0.28), tr(0.25, 0.28)], fill=color, width=max(1, int(scale * 0.08)))
    else:
        draw.ellipse((x - scale * 0.22, y - scale * 0.22, x + scale * 0.22, y + scale * 0.22), outline=color, width=max(1, int(scale * 0.08)))
        draw.line([tr(-0.5, 0), tr(0.5, 0)], fill=color, width=max(1, int(scale * 0.08)))


def draw_branching_tree(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    length: float,
    angle: float,
    depth: int,
    width_px: float,
    sway: float,
    seed: int,
    bark: tuple[int, int, int, int],
    leaf: tuple[int, int, int, int],
    glow_leaf: tuple[int, int, int, int],
) -> None:
    """Recursive tree silhouette: real trunk + branches + canopy blobs."""
    if depth <= 0 or length < 4:
        # A leaf clump at the branch tip; alternating glow makes it feel magical but still tree-like.
        rr = max(3.0, length * (1.25 + 0.18 * ((seed * 7) % 5)))
        fill = glow_leaf if seed % 4 == 0 else leaf
        draw.ellipse((x - rr * 1.55, y - rr, x + rr * 1.55, y + rr), fill=fill)
        return

    curve = math.sin(seed * 1.91 + depth * 0.73) * 0.18 + sway
    x2 = x + math.cos(angle + curve) * length
    y2 = y + math.sin(angle + curve) * length
    w = max(1, int(width_px))

    # Draw branch as layered strokes: dark underpaint + green moss highlight.
    draw.line([(x, y), (x2, y2)], fill=(0, 5, 4, min(235, bark[3] + 35)), width=w + 2)
    draw.line([(x, y), (x2, y2)], fill=bark, width=w)
    if depth >= 3:
        hx = x + (x2 - x) * 0.52
        hy = y + (y2 - y) * 0.52
        draw.line([(hx, hy), (hx + math.cos(angle - 0.8) * length * 0.18, hy + math.sin(angle - 0.8) * length * 0.18)], fill=(26, 96, 42, 95), width=max(1, w // 3))

    # Deterministic asymmetric splits: looks more arboreal than radial spokes.
    spread = 0.38 + 0.10 * math.sin(seed * 0.77)
    child_len = length * (0.66 + 0.05 * math.sin(seed))
    child_w = width_px * 0.68
    draw_branching_tree(draw, x2, y2, child_len, angle - spread, depth - 1, child_w, sway * 0.72, seed * 3 + 1, bark, leaf, glow_leaf)
    draw_branching_tree(draw, x2, y2, child_len * (0.90 + 0.08 * math.sin(seed * 2.3)), angle + spread * 0.86, depth - 1, child_w, sway * 0.72, seed * 3 + 2, bark, leaf, glow_leaf)
    if depth >= 4:
        draw_branching_tree(draw, x2, y2, child_len * 0.56, angle + spread * 1.55, depth - 2, child_w * 0.72, sway * 0.65, seed * 3 + 3, bark, leaf, glow_leaf)


def draw_forest_temple_back(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    t: float,
    rms: float,
    bass: float,
    lowmid: float,
    mid: float,
    high: float,
    flux: float,
    centroid: float,
    spec: np.ndarray,
    cx: float,
    cy: float,
    base_radius: float,
    hue_base: float,
) -> None:
    """Ancient game-level forest temple: stone arch, pillars, canopy, glyphs, shafts."""
    # Deep canopy silhouettes and shafts of god-light from the broken ceiling.
    for i in range(18):
        x0 = width * ((i * 0.073 + 0.03 * math.sin(t * 0.019 + i)) % 1.0)
        trunk_w = width * (0.010 + 0.009 * ((i * 11) % 7) / 7)
        lean = math.sin(i * 1.7) * width * 0.055
        draw.polygon(
            [(x0 - trunk_w, 0), (x0 + trunk_w, 0), (x0 + lean + trunk_w * 0.45, height * 0.76), (x0 + lean - trunk_w * 0.45, height * 0.76)],
            fill=(1, 8, 7, 62),
        )
    for i in range(9):
        x0 = width * (0.18 + i * 0.085 + 0.02 * math.sin(i))
        ray_w = width * (0.045 + 0.02 * math.sin(i * 2.3))
        alpha = int(16 + 32 * high + 16 * flux + 6 * math.sin(t * 0.21 + i))
        draw.polygon(
            [(x0 - ray_w * 0.28, 0), (x0 + ray_w * 0.28, 0), (cx + (x0 - cx) * 0.24 + ray_w, cy + height * 0.22), (cx + (x0 - cx) * 0.24 - ray_w, cy + height * 0.22)],
            fill=(145, 255, 190, max(5, alpha)),
        )

    stone = (23, 36, 33, 190)
    stone_hi = (71, 96, 82, 145)
    moss = (30, 108, 54, 118)
    shadow = (0, 7, 8, 145)
    glow = hsv255(hue_base + 0.02, 0.62, 0.98, int(65 + 80 * rms + 42 * flux))

    # Main circular ruin portal inset into a temple wall.
    arch_rx = base_radius * 2.15
    arch_ry = base_radius * 2.55
    wall_y = cy + arch_ry * 0.10
    left = cx - arch_rx * 1.24
    right = cx + arch_rx * 1.24
    top = cy - arch_ry * 1.02
    bottom = cy + arch_ry * 1.08

    # Massive back wall / lintel with moss stains.
    draw.rounded_rectangle((left, top + arch_ry * 0.40, right, bottom), radius=int(width * 0.025), fill=(10, 20, 19, 105), outline=(72, 91, 79, 80), width=max(2, int(width / 420)))
    draw.rectangle((left - width * 0.035, top + arch_ry * 0.56, right + width * 0.035, top + arch_ry * 0.76), fill=stone, outline=stone_hi, width=max(2, int(width / 520)))

    # Pillars with block seams.
    for side in (-1, 1):
        px = cx + side * arch_rx * 1.05
        pw = width * 0.075
        ptop = top + arch_ry * 0.50
        pbot = bottom + height * 0.07
        draw.rounded_rectangle((px - pw / 2, ptop, px + pw / 2, pbot), radius=int(pw * 0.16), fill=stone, outline=stone_hi, width=max(2, int(width / 500)))
        draw.rectangle((px - pw * 0.68, ptop - height * 0.026, px + pw * 0.68, ptop + height * 0.020), fill=(34, 50, 43, 210), outline=stone_hi)
        draw.rectangle((px - pw * 0.78, pbot - height * 0.020, px + pw * 0.78, pbot + height * 0.030), fill=(18, 28, 25, 220), outline=(77, 93, 78, 95))
        for k in range(6):
            yy = ptop + (pbot - ptop) * (k + 0.5) / 6
            crack = math.sin(t * 0.13 + side * k) * width * 0.004
            draw.line([(px - pw * 0.42, yy), (px + pw * 0.36 + crack, yy + height * 0.004 * math.sin(k))], fill=(4, 11, 11, 105), width=1)
        # vines on columns, gently audio-swaying
        for v in range(5):
            vx = px - pw * 0.38 + v * pw * 0.19
            pts = []
            for q in range(14):
                yy = ptop - height * 0.02 + q * (pbot - ptop) / 13
                sway = math.sin(t * (0.34 + 0.03 * v) + q * 0.8 + v) * width * (0.003 + 0.005 * mid)
                pts.append((vx + sway, yy))
            draw.line(pts, fill=(11, 72, 35, 150), width=max(1, int(width / 520)))
            for q in range(2, 13, 3):
                lx, ly = pts[q]
                draw.ellipse((lx - 4, ly - 2, lx + 7, ly + 4), fill=(45, 130, 59, 80 + int(50 * high)))

    # Ring stones around the portal; each block reacts to spectral bins.
    block_count = 34
    for j in range(block_count):
        ang = -math.pi * 0.92 + j * (math.pi * 1.84 / (block_count - 1))
        # only upper arch + shoulders, leaves bottom open for stairs
        x = cx + math.cos(ang) * arch_rx * 0.86
        y = wall_y + math.sin(ang) * arch_ry * 0.72
        val = float(spec[(j * len(spec)) // block_count])
        bw = width * (0.025 + 0.008 * val)
        bh = height * (0.036 + 0.018 * val)
        a = ang + math.pi / 2
        col = (31 + int(35 * val), 48 + int(48 * val), 42 + int(26 * val), 205)
        # approximated rotated block as a fat line plus glowing rune.
        dx = math.cos(a) * bw
        dy = math.sin(a) * bw
        draw.line([(x - dx, y - dy), (x + dx, y + dy)], fill=col, width=max(5, int(bh)), joint="curve")
        draw.line([(x - dx, y - dy), (x + dx, y + dy)], fill=(103, 123, 99, 95), width=max(1, int(bh * 0.16)))
        if j % 2 == 0:
            draw_temple_rune(draw, x, y, max(7, width * 0.010 + 10 * val), a, hsv255(hue_base + 0.08 + val * 0.12, 0.62, 1.0, int(35 + 145 * val + 55 * flux)), j)

    # Inner magic pool, now framed as the temple door/portal.
    for j in range(7, 0, -1):
        rr_x = arch_rx * (0.16 + j * 0.086 + 0.018 * bass * math.sin(t * 0.9 + j))
        rr_y = arch_ry * (0.18 + j * 0.083 + 0.014 * mid * math.cos(t * 0.7 + j))
        alpha = int((9 + 10 * rms + 20 * flux) * (8 - j))
        draw.ellipse((cx - rr_x, wall_y - rr_y, cx + rr_x, wall_y + rr_y), outline=hsv255(hue_base + 0.03 * j, 0.78, 1.0, alpha), width=max(1, int(width / 360)))
    draw.ellipse((cx - arch_rx * 0.30, wall_y - arch_ry * 0.34, cx + arch_rx * 0.30, wall_y + arch_ry * 0.34), fill=(34, 255, 155, int(18 + 52 * rms + 55 * flux)))

    # Hanging vines/fronds from ceiling, like a playable forest-temple room.
    for i in range(30):
        x0 = width * ((i * 0.061 + 0.017 * math.sin(i * 4.1)) % 1.0)
        length = height * (0.13 + 0.24 * (((i * 29) % 19) / 19.0))
        pts = []
        for q in range(12):
            yy = q * length / 11
            xx = x0 + math.sin(t * (0.20 + (i % 7) * 0.025) + q * 0.8 + i) * width * (0.004 + 0.006 * high)
            pts.append((xx, yy))
        draw.line(pts, fill=(5, 43, 25, 135), width=max(1, int(width / 640)))
        if i % 3 == 0:
            for q in range(3, 11, 3):
                xx, yy = pts[q]
                draw.ellipse((xx - 5, yy - 3, xx + 8, yy + 5), fill=(37, 112, 48, 78))

    # Shadowy doorway floor behind stairs.
    draw.ellipse((cx - arch_rx * 0.72, bottom - height * 0.06, cx + arch_rx * 0.72, bottom + height * 0.10), fill=shadow)


def draw_forest_temple_front(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    t: float,
    rms: float,
    sub: float,
    bass: float,
    mid: float,
    high: float,
    flux: float,
    cx: float,
    cy: float,
    base_radius: float,
    hue_base: float,
) -> None:
    """Foreground floor, steps, roots, grass silhouettes; keeps the scene grounded."""
    floor_y = height * (0.735 - 0.012 * bass)
    step_depth = height * 0.043
    max_w = width * 0.72
    min_w = width * 0.24
    for s in range(8):
        y0 = floor_y + s * step_depth
        w0 = min_w + (max_w - min_w) * (s / 7) ** 1.15
        h = step_depth * 0.82
        col = (13 + s * 3, 24 + s * 4, 22 + s * 3, 205)
        edge = (76, 100, 83, 88 + int(55 * flux))
        draw.polygon([(cx - w0 * 0.48, y0), (cx + w0 * 0.48, y0), (cx + w0 * 0.57, y0 + h), (cx - w0 * 0.57, y0 + h)], fill=col, outline=edge)
        if s % 2 == 0:
            draw.line([(cx - w0 * 0.42, y0 + h * 0.35), (cx + w0 * 0.42, y0 + h * 0.28)], fill=(2, 10, 10, 80), width=1)
        # moss strip on each step catches high-end shimmer.
        draw.line([(cx - w0 * 0.36, y0 + h * 0.12), (cx + w0 * 0.34, y0 + h * 0.08)], fill=(25, 105, 48, 58 + int(72 * high)), width=max(1, int(width / 520)))

    # Reactive glowing floor sigil just in front of the doorway.
    sig_y = floor_y + step_depth * 1.15
    sig_rx = base_radius * (1.05 + 0.20 * bass)
    sig_ry = base_radius * (0.25 + 0.08 * rms)
    draw.ellipse((cx - sig_rx, sig_y - sig_ry, cx + sig_rx, sig_y + sig_ry), outline=hsv255(hue_base + 0.10, 0.74, 0.98, int(60 + 110 * flux)), width=max(1, int(width / 330)))
    for i in range(12):
        ang = i * math.tau / 12 + t * 0.10
        x = cx + math.cos(ang) * sig_rx * 0.76
        y = sig_y + math.sin(ang) * sig_ry * 0.76
        draw_temple_rune(draw, x, y, width * 0.010, ang, hsv255(hue_base + 0.20, 0.60, 1.0, int(45 + 105 * rms)), i + 7)

    # Roots and grass silhouettes in front, pulsing with sub/bass.
    ground_y = height * (0.90 - 0.015 * bass)
    for i in range(54):
        x0 = (i / 53.0) * width
        h = height * (0.030 + 0.105 * ((i * 37) % 17) / 17.0) * (0.62 + 0.95 * sub)
        sway = math.sin(t * (0.55 + (i % 5) * 0.08) + i) * width * 0.007 * (1 + bass)
        draw.line([(x0, height), (x0 + sway, ground_y - h)], fill=(1, 10, 9, 190), width=max(1, int(width / 430)))
    for i in range(12):
        x0 = width * ((i * 0.097 + 0.03) % 1.0)
        pts = []
        for q in range(9):
            x = x0 + q * width * 0.022
            y = height - q * height * 0.018 - math.sin(t * 0.34 + i + q) * height * 0.007 * (1 + mid)
            pts.append((x, y))
        draw.line(pts, fill=(2, 13, 10, 165), width=max(3, int(width / 250)))
    draw.rectangle((0, int(ground_y), width, height), fill=(0, 5, 6, 118))


def render_frame(
    idx: int,
    f: Features,
    width: int,
    height: int,
    bg_grid: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray],
    particles: dict[str, np.ndarray],
    fps: int,
) -> Image.Image:
    t = float(f.frame_times[idx])
    rms = float(f.rms[idx])
    sub = float(f.sub[idx])
    bass = float(f.bass[idx])
    lowmid = float(f.lowmid[idx])
    mid = float(f.mid[idx])
    high = float(f.high[idx])
    air = float(f.air[idx])
    flux = float(f.flux[idx])
    centroid = float(f.centroid[idx])
    spec = f.spec[idx]

    bg_low = render_background(*bg_grid, t, rms, bass, mid, high, centroid)
    img = bg_low.resize((width, height), Image.Resampling.BICUBIC).convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")

    cx = width * 0.5
    cy = height * (0.52 + 0.025 * math.sin(t * 0.17))
    base_radius = min(width, height) * (0.145 + 0.055 * bass + 0.025 * rms)
    hue_base = 0.38 + 0.16 * centroid + 0.025 * math.sin(t * 0.07)

    draw_forest_temple_back(draw, width, height, t, rms, bass, lowmid, mid, high, flux, centroid, spec, cx, cy, base_radius, hue_base)

    # Beat-synced expanding rings from detected peaks.
    lo = np.searchsorted(f.peaks, t - 1.55, side="left")
    hi = np.searchsorted(f.peaks, t, side="right")
    for pt in f.peaks[lo:hi]:
        age = t - float(pt)
        if 0 <= age <= 1.55:
            k = age / 1.55
            rr = base_radius * (1.0 + 4.7 * k)
            alpha = int(170 * (1.0 - k) ** 1.55)
            col = hsv255(hue_base + 0.08 * k, 0.82, 1.0, alpha)
            w = max(1, int(7 * (1 - k) + 1))
            draw.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=col, width=w)
            if age < 0.28:
                flash = int(45 * (1 - age / 0.28))
                draw.rectangle((0, 0, width, height), fill=(120, 255, 190, flash))

    # Radial spectral mandala: low frequencies are thick roots, highs are sparks.
    n = len(spec)
    rot = t * (0.075 + bass * 0.055) + 0.42 * math.sin(t * 0.045)
    for mirror in (0, math.pi):
        for i, val in enumerate(spec):
            # Skip tiny values randomly-ish to keep it organic.
            if val < 0.035 and i % 3:
                continue
            ang = mirror + rot + (i / n) * math.tau
            low_weight = 1.0 - i / n
            high_weight = i / n
            inner = base_radius * (0.60 + 0.30 * math.sin(i * 0.21 + t * 0.33))
            length = min(width, height) * (0.035 + 0.25 * float(val) * (0.55 + 0.8 * low_weight + 0.35 * high))
            wobble = 0.045 * math.sin(t * 1.3 + i * 0.55) * (1 + mid)
            a2 = ang + wobble
            p1 = (cx + math.cos(a2) * inner, cy + math.sin(a2) * inner)
            p2 = (cx + math.cos(a2) * (inner + length), cy + math.sin(a2) * (inner + length))
            hue = hue_base + 0.30 * high_weight + 0.05 * math.sin(t * 0.21 + i)
            alpha = int(35 + 175 * float(val) + 35 * flux)
            wid = max(1, int(1 + 6 * float(val) * (0.8 + bass) + 2 * low_weight))
            col = hsv255(hue, 0.72 + 0.25 * high_weight, 0.72 + 0.28 * val, min(alpha, 235))
            draw.line([p1, p2], fill=col, width=wid)

    # Portal/core ellipses, layered for bloom without expensive blur.
    for j in range(9, 0, -1):
        rr = base_radius * (0.42 + j * 0.145 + 0.05 * math.sin(t * 0.6 + j))
        alpha = int((13 + 12 * rms + 11 * bass) * (10 - j) / 9)
        col = hsv255(hue_base + j * 0.018, 0.68, 0.96, alpha)
        draw.ellipse((cx - rr * 1.15, cy - rr, cx + rr * 1.15, cy + rr), outline=col, width=max(1, int(2 + 5 * bass)))
    core_r = base_radius * (0.33 + 0.16 * flux)
    draw.ellipse((cx - core_r, cy - core_r, cx + core_r, cy + core_r), fill=hsv255(hue_base + 0.04, 0.34, 0.95, int(35 + 75 * rms)))

    # Lissajous oscilloscope from the last 0.36 sec of stereo audio.
    scope = sample_audio_window(f.stereo, f.sr, t, 0.36, 360)
    if np.max(np.abs(scope)) > 1e-5:
        scale = min(width, height) * (0.20 + 0.08 * rms)
        phase = np.linspace(0, math.tau, len(scope), dtype=np.float32)
        xs = cx + (scope[:, 0] * 0.58 + 0.10 * np.sin(phase * 3 + t)) * scale
        ys = cy + (scope[:, 1] * 0.58 + 0.08 * np.cos(phase * 2 - t * 0.7)) * scale
        pts = list(zip(xs.tolist(), ys.tolist()))
        draw_polyline_glow(draw, pts, hsv255(hue_base + 0.49, 0.52, 1.0, int(40 + 42 * rms)), max(1, int(1 + 2 * rms)), glow=1)

    # Three horizontal spectral ribbons / vines.
    ribbon_samples = sample_audio_window(f.stereo, f.sr, t, 2.4, 420)
    xs = np.linspace(width * 0.06, width * 0.94, len(ribbon_samples))
    for lane, (ybase, chan, hh, amp_mul) in enumerate([
        (height * 0.22, 0, hue_base + 0.06, 0.11 + high * 0.10),
        (height * 0.79, 1, hue_base + 0.20, 0.10 + bass * 0.10),
        (height * 0.50, 0, hue_base + 0.35, 0.07 + mid * 0.10),
    ]):
        wave = ribbon_samples[:, chan]
        carrier = np.sin(np.linspace(0, math.tau * (2.0 + lane), len(wave)) + t * (0.9 + lane * 0.23))
        ys = ybase + (wave * height * amp_mul) + carrier * height * 0.018 * (0.3 + rms + [high, bass, mid][lane])
        pts = list(zip(xs.tolist(), ys.tolist()))
        draw_polyline_glow(draw, pts, hsv255(hh, 0.62, 0.86, int(26 + 38 * [high, bass, mid][lane])), 1, glow=1)

    # Fireflies / spores: deterministic particle field, pulled upward by air/high energy.
    px = particles["x"]
    py = particles["y"]
    phase = particles["phase"]
    size = particles["size"]
    hue = particles["hue"]
    drift_x = (px + 0.028 * np.sin(t * particles["speed"] + phase) + 0.012 * math.sin(t * 0.08)) % 1.0
    drift_y = (py - (t * (0.003 + 0.010 * high + 0.006 * air) * particles["rise"]) + 0.018 * np.cos(t * particles["speed"] * 0.7 + phase)) % 1.0
    twinkle = 0.5 + 0.5 * np.sin(t * particles["twinkle"] + phase * 1.7)
    # Draw larger/brightest last so they sit on top.
    order = np.argsort(size)
    for p in order:
        b = float(0.16 + 0.46 * twinkle[p] + 0.28 * high + 0.20 * flux)
        if b < 0.33 and p % 4:
            continue
        x0 = float(drift_x[p] * width)
        y0 = float(drift_y[p] * height)
        rr = float(size[p] * (0.75 + 1.9 * b + 1.2 * air))
        col = hsv255(float(hue[p] + hue_base * 0.08 + 0.07 * high), 0.55, min(1, b + 0.35), int(20 + 105 * b))
        draw.ellipse((x0 - rr * 2.3, y0 - rr * 2.3, x0 + rr * 2.3, y0 + rr * 2.3), fill=(col[0], col[1], col[2], max(5, col[3] // 5)))
        draw.ellipse((x0 - rr, y0 - rr, x0 + rr, y0 + rr), fill=col)

    draw_forest_temple_front(draw, width, height, t, rms, sub, bass, mid, high, flux, cx, cy, base_radius, hue_base)

    # Subtle letterbox vignette for cinematic contrast.
    bar = int(height * 0.035)
    draw.rectangle((0, 0, width, bar), fill=(0, 0, 0, 90))
    draw.rectangle((0, height - bar, width, height), fill=(0, 0, 0, 100))

    return img.convert("RGB")


def ffmpeg_command(audio_path: Path, output_path: Path, width: int, height: int, fps: int, crf: int, preset: str) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{width}x{height}",
        "-r",
        str(fps),
        "-i",
        "-",
        "-i",
        str(audio_path),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "libx264",
        "-preset",
        preset,
        "-crf",
        str(crf),
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "320k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(output_path),
    ]


def render_video(args: argparse.Namespace) -> None:
    audio_path = Path(args.audio).expanduser().resolve()
    if not audio_path.exists():
        raise FileNotFoundError(audio_path)
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    f = compute_features(audio_path, args.fps, n_spec_bins=args.spec_bins)
    bg_grid = make_background_grid(max(160, args.width // args.bg_scale), max(90, args.height // args.bg_scale))

    rng = np.random.default_rng(args.seed)
    n_particles = args.particles
    particles = {
        "x": rng.random(n_particles).astype(np.float32),
        "y": rng.random(n_particles).astype(np.float32),
        "phase": rng.random(n_particles).astype(np.float32) * math.tau,
        "size": rng.uniform(0.65, 2.9, n_particles).astype(np.float32) * (args.width / 1280.0),
        "hue": rng.uniform(0.28, 0.56, n_particles).astype(np.float32),
        "speed": rng.uniform(0.25, 1.9, n_particles).astype(np.float32),
        "rise": rng.uniform(0.35, 1.8, n_particles).astype(np.float32),
        "twinkle": rng.uniform(1.2, 4.7, n_particles).astype(np.float32),
    }

    cmd = ffmpeg_command(audio_path, output_path, args.width, args.height, args.fps, args.crf, args.preset)
    eprint("Encoding with ffmpeg:", " ".join(cmd))
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdin is not None
    t0 = time.time()
    try:
        total = len(f.frame_times)
        for i in range(total):
            frame = render_frame(i, f, args.width, args.height, bg_grid, particles, args.fps)
            proc.stdin.write(frame.tobytes())
            if i == 0 or (i + 1) % max(1, args.fps * 5) == 0 or i + 1 == total:
                elapsed = time.time() - t0
                rate = (i + 1) / max(1e-6, elapsed)
                eta = (total - i - 1) / max(1e-6, rate)
                eprint(f"frame {i + 1:5d}/{total}  {100*(i+1)/total:5.1f}%  {rate:5.1f} fps render  ETA {eta:5.1f}s")
    except BrokenPipeError:
        pass
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
    stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
    rc = proc.wait()
    if rc != 0:
        eprint(stderr[-4000:])
        raise RuntimeError(f"ffmpeg failed with exit code {rc}")
    eprint(stderr[-1600:])
    eprint(f"Wrote: {output_path}")


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate an audio-reactive enchanted-glade MP4 visualizer.")
    p.add_argument("audio", help="Input audio file. WAV is read directly; ffmpeg handles muxing.")
    p.add_argument("--output", "-o", default=None, help="Output MP4 path. Defaults to <audio>_visuals.mp4")
    p.add_argument("--width", type=int, default=1280)
    p.add_argument("--height", type=int, default=720)
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--crf", type=int, default=18, help="x264 quality: lower is better/larger. 16-20 recommended.")
    p.add_argument("--preset", default="medium", choices=["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower"])
    p.add_argument("--seed", type=int, default=1337)
    p.add_argument("--particles", type=int, default=360)
    p.add_argument("--spec-bins", type=int, default=72)
    p.add_argument("--bg-scale", type=int, default=2, help="Render procedural background at width/bg-scale for speed, then upscale.")
    args = p.parse_args(list(argv))
    if args.output is None:
        src = Path(args.audio).expanduser()
        args.output = str(src.with_name(src.stem + "_visuals.mp4"))
    if args.width < 320 or args.height < 180:
        p.error("width/height too small")
    if args.fps < 12 or args.fps > 60:
        p.error("fps must be between 12 and 60")
    return args


def main(argv: Iterable[str] = sys.argv[1:]) -> int:
    try:
        args = parse_args(argv)
        render_video(args)
        return 0
    except Exception as exc:
        eprint(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

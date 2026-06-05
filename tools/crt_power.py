#!/usr/bin/env python3
"""crt_power — add a CRT power-ON and/or power-OFF animation to a finished MP4.

The classic tube-TV effect, as a post-pass over ANY video (any style):
  POWER-ON  : black → a bright horizontal line snaps on → expands vertically to full
              picture (with an overshoot flash).
  POWER-OFF : picture collapses vertically to a bright horizontal line → that line
              shrinks horizontally to a centre dot → a quick flash → black.

This is a TEMPORAL effect (geometry animates over time), so it can't live in the static
CRT grade ([[blender-crt-grade]]) — it's a separate envelope applied to the final clip.
Pairs with that grade: grade the look in Blender, then run this for the on/off bookends.

Implementation: pipe raw RGB frames through ffmpeg (decode → numpy warp → re-encode),
re-muxing the original audio. Only the on/off WINDOWS are warped; all middle frames pass
through untouched, so it's fast regardless of clip length. numpy only (no PIL/cv2).

    .venv/bin/python tools/crt_power.py IN.mp4 OUT.mp4 [--on 0.5] [--off 0.7] [--no-audio]

Verified on the parallax-bloom demo: first frame = bright scan-line snap; last frames =
collapse to line → dot → black.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

import numpy as np


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate,nb_read_frames",
         "-count_frames", "-of", "json", path],
        capture_output=True, text=True).stdout
    s = json.loads(out)["streams"][0]
    num, den = s["r_frame_rate"].split("/")
    fps = float(num) / float(den)
    n = int(s.get("nb_read_frames") or 0)
    return int(s["width"]), int(s["height"]), fps, n


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def vertical_collapse(frame, sy, sx=1.0, bright=1.0):
    """Collapse the frame toward its centre: keep a band of height sy*H (and width sx*W),
    everything outside → black. sy,sx in (0,1]; bright scales the surviving pixels."""
    h, w, _ = frame.shape
    out = np.zeros_like(frame)
    cy, cx = (h - 1) / 2.0, (w - 1) / 2.0
    sy = max(sy, 1e-3); sx = max(sx, 1e-3)
    ys = np.arange(h)
    src_y = (cy + (ys - cy) / sy).round().astype(int)         # which source row feeds each out row
    valid_y = (src_y >= 0) & (src_y < h)
    xs = np.arange(w)
    src_x = (cx + (xs - cx) / sx).round().astype(int)
    valid_x = (src_x >= 0) & (src_x < w)
    sy_idx = np.where(valid_y, src_y, 0)
    sx_idx = np.where(valid_x, src_x, 0)
    sampled = frame[sy_idx][:, sx_idx].astype(np.float32) * bright
    mask = valid_y[:, None] & valid_x[None, :]
    out = np.where(mask[:, :, None], sampled, 0.0)
    return np.clip(out, 0, 255).astype(np.uint8)


def envelope_off(u):
    """u 0→1 across the OFF window. Returns (sy, sx, bright). Vertical collapse first
    (u 0→0.65), then horizontal to a dot (0.65→0.9), then dark flash-out."""
    if u < 0.65:
        t = u / 0.65
        return (1.0 - 0.97 * smoothstep(t), 1.0, 1.0 + 0.6 * t)   # squeeze to a bright line
    if u < 0.9:
        t = (u - 0.65) / 0.25
        return (0.03, 1.0 - 0.97 * smoothstep(t), 1.7)            # line → dot, hot
    t = (u - 0.9) / 0.1
    return (0.03, 0.03 * (1 - t), 1.7 * (1 - smoothstep(t)))      # dot fades to black


def envelope_on(u):
    """u 0→1 across the ON window: reverse of off — line snaps in, expands, overshoot flash."""
    if u < 0.12:
        return (0.03, 0.03 + 0.97 * (u / 0.12), 1.8)             # dot → bright line
    if u < 0.6:
        t = (u - 0.12) / 0.48
        return (0.03 + 0.97 * smoothstep(t), 1.0, 1.8 - 0.4 * t)  # line → full height, hot
    t = (u - 0.6) / 0.4
    return (1.0, 1.0, 1.4 - 0.4 * smoothstep(t))                  # settle the overshoot flash


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp"); ap.add_argument("out")
    ap.add_argument("--on", type=float, default=0.5, help="power-on duration (s); 0 = none")
    ap.add_argument("--off", type=float, default=0.7, help="power-off duration (s); 0 = none")
    ap.add_argument("--no-audio", action="store_true")
    a = ap.parse_args()

    w, h, fps, n = probe(a.inp)
    if n <= 0:
        # fallback: count via duration
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                    "-of", "default=nk=1:nw=1", a.inp], capture_output=True, text=True).stdout)
        n = int(round(dur * fps))
    on_f = int(round(a.on * fps))
    off_f = int(round(a.off * fps))
    print(f"crt_power: {w}x{h} {fps:.2f}fps {n} frames | on={on_f}f off={off_f}f", flush=True)

    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", a.inp, "-f", "rawvideo",
                            "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc_cmd = ["ffmpeg", "-v", "error", "-y",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", f"{fps}", "-i", "-"]
    if not a.no_audio:
        enc_cmd += ["-i", a.inp, "-map", "0:v", "-map", "1:a?", "-c:a", "aac", "-b:a", "256k", "-shortest"]
    enc_cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", a.out]
    enc = subprocess.Popen(enc_cmd, stdin=subprocess.PIPE)

    fsize = w * h * 3
    warped = 0
    for i in range(n):
        buf = dec.stdout.read(fsize)
        if len(buf) < fsize:
            break
        frame = np.frombuffer(buf, np.uint8).reshape(h, w, 3)
        if on_f and i < on_f:
            sy, sx, br = envelope_on(i / max(1, on_f))
            frame = vertical_collapse(frame, sy, sx, br); warped += 1
        elif off_f and i >= n - off_f:
            sy, sx, br = envelope_off((i - (n - off_f)) / max(1, off_f))
            frame = vertical_collapse(frame, sy, sx, br); warped += 1
        enc.stdin.write(np.ascontiguousarray(frame).tobytes())
    enc.stdin.close()
    dec.wait(); enc.wait()
    print(f"crt_power: done, warped {warped} frames → {a.out}", flush=True)


if __name__ == "__main__":
    sys.exit(main())

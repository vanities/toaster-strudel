#!/usr/bin/env python3
"""Score how closely an audio clip matches a text description, via LAION-CLAP.

Usage:
  uv run --with laion-clap --with torch --with soundfile tools/clap-score.py \\
    <wav-file> --target "warm cinematic ambient" [--target "..." ...]

Output: JSON with per-target cosine similarity. Values are in roughly [-0.2, 0.5]
for normal text — higher is better. Compare across calls, not against a fixed
threshold, since CLAP scores aren't calibrated.

Model: laion/clap-htsat-unfused (~600MB, downloads on first run).
Runs on Apple Silicon via PyTorch MPS automatically. Cached in ~/.cache/clap.
"""

import argparse
import json
import os
import sys
import warnings
from pathlib import Path

# CLAP and HuggingFace love printing irrelevant warnings — quiet them down so
# the JSON output stays parseable.
warnings.filterwarnings("ignore")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")


def load_audio(path: Path, target_sr: int = 48000):
    import soundfile as sf
    import numpy as np
    data, sr = sf.read(str(path), dtype="float32", always_2d=True)
    # Mono mix for CLAP
    if data.shape[1] > 1:
        data = data.mean(axis=1)
    else:
        data = data[:, 0]
    if sr != target_sr:
        # Naive linear resample — fine for CLAP's purposes
        import math
        n_out = int(round(len(data) * target_sr / sr))
        x_old = np.linspace(0, 1, num=len(data), endpoint=False)
        x_new = np.linspace(0, 1, num=n_out, endpoint=False)
        data = np.interp(x_new, x_old, data).astype("float32")
        sr = target_sr
    return data, sr


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("wav", type=Path, help="audio file (wav/flac/mp3)")
    ap.add_argument(
        "--target", "-t", action="append", required=True,
        help="text description to score against (repeatable)",
    )
    ap.add_argument(
        "--model", default="laion/clap-htsat-unfused",
        help="HuggingFace CLAP model id (default: laion/clap-htsat-unfused)",
    )
    args = ap.parse_args()

    if not args.wav.exists():
        print(json.dumps({"error": f"file not found: {args.wav}"}), file=sys.stderr)
        sys.exit(1)

    # Lazy imports — uv won't install torch unless we actually need it
    import numpy as np
    import torch
    from transformers import ClapModel, ClapProcessor

    device = "mps" if torch.backends.mps.is_available() else (
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print(f"loading {args.model} on {device}…", file=sys.stderr)
    model = ClapModel.from_pretrained(args.model).to(device).eval()
    processor = ClapProcessor.from_pretrained(args.model)

    audio, sr = load_audio(args.wav)
    print(f"audio: {len(audio)/sr:.1f}s at {sr}Hz", file=sys.stderr)

    with torch.no_grad():
        # Audio embedding
        a_in = processor(audios=audio, sampling_rate=sr, return_tensors="pt")
        a_in = {k: v.to(device) for k, v in a_in.items()}
        a_emb = model.get_audio_features(**a_in)
        a_emb = a_emb / a_emb.norm(dim=-1, keepdim=True)

        # Text embeddings (batched)
        t_in = processor(text=args.target, return_tensors="pt", padding=True)
        t_in = {k: v.to(device) for k, v in t_in.items()}
        t_emb = model.get_text_features(**t_in)
        t_emb = t_emb / t_emb.norm(dim=-1, keepdim=True)

        # Cosine similarity (vectors are already L2-normalised)
        sims = (a_emb @ t_emb.T).squeeze(0).cpu().tolist()

    out = {
        "audio": str(args.wav),
        "duration_s": round(len(audio) / sr, 2),
        "scores": [
            {"target": t, "score": round(float(s), 4)}
            for t, s in zip(args.target, sims)
        ],
    }
    # Sort highest first
    out["scores"].sort(key=lambda x: -x["score"])
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

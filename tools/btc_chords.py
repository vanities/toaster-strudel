#!/usr/bin/env python3
"""BTC large-vocabulary chord recognition (Jang et al., ISMIR 2019).

Richer than the chroma-template fallback in transcribe.py: the 170-chord
large-vocabulary model recognises maj/min/7/maj7/min7/dim/aug/dim7/hdim7/
min6/maj6/minmaj7/sus2/sus4 — actual extensions, not just triads. Outputs
timed chord intervals [(start_s, end_s, "C:maj7"), ...].

    tools/.venv-btc/bin/python tools/btc_chords.py <audio> [--json]

Vendored code + pretrained weights under tools/vendor/BTC-ISMIR19/ (clone of
github.com/jayg996/BTC-ISMIR19). Override location with BTC_DIR=.
"""
import argparse
import json
import os
import sys
from pathlib import Path

BTC_DIR = Path(os.environ.get("BTC_DIR", Path(__file__).resolve().parent / "vendor" / "BTC-ISMIR19"))


def _compat():
    """Shim 2019-era APIs for modern deps: PyYAML's required Loader arg and the
    numpy aliases (np.float/int/...) removed in numpy>=1.24."""
    import numpy as np
    import yaml
    for name, typ in (("float", float), ("int", int), ("bool", bool),
                      ("object", object), ("complex", complex)):
        if not hasattr(np, name):
            setattr(np, name, typ)
    if not getattr(yaml, "_btc_patched", False):
        _orig = yaml.load
        yaml.load = lambda stream, **kw: _orig(stream, Loader=kw.pop("Loader", yaml.FullLoader))
        yaml._btc_patched = True


def load_model(device: str = "cpu"):
    _compat()
    if str(BTC_DIR) not in sys.path:
        sys.path.insert(0, str(BTC_DIR))
    import torch
    from btc_model import BTC_model
    from utils.hparams import HParams

    config = HParams.load(str(BTC_DIR / "run_config.yaml"))
    config.feature["large_voca"] = True
    config.model["num_chords"] = 170
    model = BTC_model(config=config.model).to(device)
    ckpt = torch.load(str(BTC_DIR / "test" / "btc_model_large_voca.pt"),
                      map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model"])
    model.eval()
    return model, config, ckpt["mean"], ckpt["std"]


def chords(audio_path, device: str = "cpu", model_cfg=None) -> list[tuple[float, float, str]]:
    """Return timed chord intervals for one audio file."""
    _compat()
    import numpy as np
    import torch
    if str(BTC_DIR) not in sys.path:
        sys.path.insert(0, str(BTC_DIR))
    from utils.mir_eval_modules import audio_file_to_features, idx2voca_chord

    model, config, mean, std = model_cfg or load_model(device)
    idx2voca = idx2voca_chord()
    feature, fps, _ = audio_file_to_features(str(audio_path), config)
    feature = (feature.T - mean) / std
    n = config.model["timestep"]
    pad = n - (feature.shape[0] % n)
    feature = np.pad(feature, ((0, pad), (0, 0)), mode="constant", constant_values=0)
    ninst = feature.shape[0] // n

    out: list[tuple[float, float, str]] = []
    start, prev = 0.0, None
    with torch.no_grad():
        ft = torch.tensor(feature, dtype=torch.float32).unsqueeze(0).to(device)
        for t in range(ninst):
            enc, _ = model.self_attn_layers(ft[:, n * t:n * (t + 1), :])
            pred, _ = model.output_layer(enc)
            pred = pred.squeeze()
            for i in range(n):
                idx = int(pred[i].item())
                if prev is None:
                    prev = idx
                    continue
                if idx != prev:
                    out.append((round(start, 3), round(fps * (n * t + i), 3), idx2voca[prev]))
                    start, prev = fps * (n * t + i), idx
    if prev is not None:
        out.append((round(start, 3), round(fps * ninst * n, 3), idx2voca[prev]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    cps = chords(args.audio, device)
    if args.json:
        print(json.dumps(cps))
    else:
        for s, e, c in cps:
            print(f"{s:.3f}\t{e:.3f}\t{c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

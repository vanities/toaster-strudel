#!/usr/bin/env python3
"""Caption reference/corpus tracks with ACE-Step's own training captioner.

`ACE-Step/acestep-captioner` (Qwen2.5-Omni-7B fine-tune) is the exact model that
labeled ACE-Step 1.5's training data — captions it writes are IN-DISTRIBUTION
prose ("flowing paragraphs covering style, instrumentation, structure, timbre"),
which is what the DiT actually understands. Hand-written tag-soup is not.

Use the output (edited to taste) as:
  - brief captions (briefs/*.json "caption")
  - LoRA training captions (replace the per-artist one-liners for a v2 corpus)

  uv run --project vendor/ACE-Step python caption_refs.py datasets/handpicked/bonobo-03-kong.flac [...]
  uv run --project vendor/ACE-Step python caption_refs.py --all-corpus handpicked

Writes <track>.acecaption.txt next to each audio file and prints the caption.
Audio is windowed (default 90s starting at 30s) — enough for the body groove,
within the captioner's audio context. ~8GB model; loads on MPS/CUDA, takes a
couple of minutes to load.
"""

from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CAPTIONER = HERE / "vendor" / "ACE-Step" / "checkpoints" / "acestep-captioner"
if not CAPTIONER.exists():  # sibling/ACE_ROOT layouts
    import os
    CAPTIONER = Path(os.environ.get("ACE_ROOT", HERE / "vendor" / "ACE-Step")) / "checkpoints" / "acestep-captioner"

PROMPT = "*Task* Describe this audio in detail"
SR = 16000  # Qwen2.5-Omni feature extractor rate

log = logging.getLogger("caption-refs")


def load_window(path: Path, offset_s: float, window_s: float) -> np.ndarray:
    import soundfile as sf
    info = sf.info(str(path))
    start = int(min(offset_s, max(0.0, info.duration - window_s)) * info.samplerate)
    frames = int(window_s * info.samplerate)
    audio, file_sr = sf.read(str(path), start=start, frames=frames, dtype="float32", always_2d=True)
    mono = audio.mean(axis=1)
    if file_sr != SR:
        import torch, torchaudio
        mono = torchaudio.functional.resample(torch.from_numpy(mono), file_sr, SR).numpy()
    return mono


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", nargs="*", help="audio files to caption")
    ap.add_argument("--all-corpus", default=None, help="caption every track in datasets/<name>/")
    ap.add_argument("--offset", type=float, default=30.0, help="window start seconds (skip the intro)")
    ap.add_argument("--window", type=float, default=90.0, help="window length seconds")
    ap.add_argument("--max-new-tokens", type=int, default=320)
    args = ap.parse_args()
    logging.basicConfig(level="INFO", format="%(message)s")

    files = [Path(a).expanduser().resolve() for a in args.audio]
    if args.all_corpus:
        ds = HERE / "datasets" / args.all_corpus
        files += sorted(p for p in ds.iterdir() if p.suffix.lower() in {".flac", ".wav", ".mp3", ".ogg", ".m4a"})
    if not files:
        raise SystemExit("no audio given (pass files or --all-corpus <name>)")

    import torch
    from transformers import Qwen2_5OmniProcessor
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    dtype = torch.bfloat16 if device != "cpu" else torch.float32

    t0 = time.perf_counter()
    log.info("[caption] loading %s on %s (%s)…", CAPTIONER.name, device, dtype)
    # thinker-only: captioning needs no speech synthesis (saves the talker weights)
    try:
        from transformers import Qwen2_5OmniThinkerForConditionalGeneration
        model = Qwen2_5OmniThinkerForConditionalGeneration.from_pretrained(
            str(CAPTIONER), dtype=dtype).to(device).eval()
    except Exception as e:  # noqa: BLE001
        log.info("[caption] thinker-only load failed (%s); loading full Omni", type(e).__name__)
        from transformers import Qwen2_5OmniForConditionalGeneration
        model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
            str(CAPTIONER), dtype=dtype).to(device).eval()
        if hasattr(model, "disable_talker"):
            model.disable_talker()
    processor = Qwen2_5OmniProcessor.from_pretrained(str(CAPTIONER))
    log.info("[caption] model ready in %.1fs", time.perf_counter() - t0)

    conversation_text = processor.apply_chat_template(
        [{"role": "user", "content": [{"type": "audio", "audio": "placeholder"},
                                      {"type": "text", "text": PROMPT}]}],
        add_generation_prompt=True, tokenize=False)

    for f in files:
        t0 = time.perf_counter()
        audio = load_window(f, args.offset, args.window)
        inputs = processor(text=conversation_text, audio=[audio], sampling_rate=SR,
                           return_tensors="pt", padding=True).to(device)
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=args.max_new_tokens, do_sample=False)
        text = processor.batch_decode(out[:, inputs["input_ids"].shape[1]:],
                                      skip_special_tokens=True)[0].strip()
        dst = f.with_suffix("").with_suffix("")  # strip one ext safely below
        dst = Path(str(f)[: -len(f.suffix)] + ".acecaption.txt")
        dst.write_text(text + "\n", encoding="utf-8")
        log.info("\n[caption] %s (%.1fs):\n%s\n  -> %s", f.name, time.perf_counter() - t0, text, dst.name)


if __name__ == "__main__":
    main()

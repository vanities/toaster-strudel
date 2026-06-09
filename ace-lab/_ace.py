"""Shared ACE-Step 1.5 bootstrap for the ace-lab scripts.

Loads the vendored ACE-Step DiT + 5Hz LLM planner once and exposes a single
`generate()` helper. Apple-Silicon aware (uses the MLX LM backend on arm64 Macs,
PyTorch elsewhere). Everything here is INSTRUMENTAL: callers pass
instrumental=True + lyrics="[Instrumental]", so nothing ever sings.

API surface confirmed from vendor/ACE-Step/run_generate_test.py and
acestep/inference.py — not guessed.
"""

from __future__ import annotations

import logging
import os
import platform
import sys
import time
from pathlib import Path

def _find_ace_root():
    """Locate the ACE-Step-1.5 checkout. Override with $ACE_ROOT; else prefer a
    `vendor/ACE-Step` (Mac layout) or a sibling `ACE-Step` (remote-box layout)."""
    env = os.environ.get("ACE_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    here = Path(__file__).resolve().parent
    for cand in (here / "vendor" / "ACE-Step", here / "ACE-Step"):
        if cand.exists():
            return cand
    return here / "vendor" / "ACE-Step"


ACE_ROOT = _find_ace_root()
CHECKPOINT_DIR = ACE_ROOT / "checkpoints"

if not ACE_ROOT.exists():
    sys.exit(f"[ace] ACE-Step not found at {ACE_ROOT} — run ./setup.sh first (or set $ACE_ROOT).")
sys.path.insert(0, str(ACE_ROOT))

# their smoke test strips proxies before importing torch/mlx; mirror it
for _v in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
    os.environ.pop(_v, None)

_IS_MAC_ARM = platform.system() == "Darwin" and platform.machine() == "arm64"
LM_BACKEND = "mlx" if _IS_MAC_ARM else "pt"  # MLX = native Apple-Silicon path
if _IS_MAC_ARM:
    os.environ.setdefault("ACESTEP_LM_BACKEND", "mlx")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

log = logging.getLogger("ace-lab")

# DiT config name (the macOS launcher's turbo pair).
DIT_CONFIG = "acestep-v15-turbo"


def _resolve_lm_model():
    """Use $ACESTEP_LM_MODEL if set; else an already-downloaded 5Hz LM under
    checkpoints/ (prefer 1.7B — it ships with the main bundle); else a default.
    The handler does NOT auto-download the LM, so pick one that's present."""
    env = os.environ.get("ACESTEP_LM_MODEL")
    if env:
        return env
    if CHECKPOINT_DIR.exists():
        avail = sorted(p.name for p in CHECKPOINT_DIR.iterdir()
                       if p.is_dir() and p.name.startswith("acestep-5Hz-lm-"))
        for pref in ("acestep-5Hz-lm-1.7B", "acestep-5Hz-lm-0.6B"):
            if pref in avail:
                return pref
        if avail:
            return avail[0]
    return "acestep-5Hz-lm-1.7B"


LM_MODEL = _resolve_lm_model()

_handlers = None


def _init():
    """Load DiT + LLM once; weights download to checkpoints/ on first call."""
    global _handlers
    if _handlers is not None:
        return _handlers

    from acestep.handler import AceStepHandler
    from acestep.llm_inference import LLMHandler

    t0 = time.perf_counter()
    log.info("[ace] loading DiT (%s, device=auto) — first run downloads weights…", DIT_CONFIG)
    dit = AceStepHandler()
    msg, ok = dit.initialize_service(
        project_root=str(ACE_ROOT), config_path=DIT_CONFIG, device="auto", offload_to_cpu=False,
    )
    if not ok:
        sys.exit(f"[ace] DiT init failed: {msg}")
    log.info("[ace] DiT ready in %.1fs", time.perf_counter() - t0)

    t0 = time.perf_counter()
    log.info("[ace] loading 5Hz LLM planner (%s, backend=%s)…", LM_MODEL, LM_BACKEND)
    llm = LLMHandler()
    msg, ok = llm.initialize(
        checkpoint_dir=str(CHECKPOINT_DIR), lm_model_path=LM_MODEL,
        backend=LM_BACKEND, device="auto", offload_to_cpu=False, dtype=None,
    )
    if not ok:
        sys.exit(f"[ace] LLM init failed: {msg}")
    log.info("[ace] LLM ready in %.1fs", time.perf_counter() - t0)

    _handlers = (dit, llm)
    return _handlers


def generate(params, out_dir, batch_size: int = 1, lora_path=None, lora_scale: float = 1.0):
    """Run one generation. `params` is an acestep GenerationParams. Returns wav paths.
    Pass `lora_path` (an adapter dir with adapter_model.safetensors) to apply a trained
    LoRA; `lora_scale` (0-1) controls how strongly it pulls toward the learned style."""
    from acestep.inference import GenerationConfig, generate_music

    dit, llm = _init()
    if lora_path:
        p = str(Path(lora_path).expanduser())
        log.info("[ace] loading LoRA: %s", p)
        log.info("[ace] %s", dit.load_lora(p))
        try:
            dit.set_use_lora(True)
        except Exception:
            pass
        if lora_scale != 1.0:
            try:
                dit.set_lora_scale(lora_scale)
                log.info("[ace] LoRA scale=%.2f", lora_scale)
            except Exception as e:  # noqa: BLE001
                log.warning("[ace] could not set LoRA scale: %s", e)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg = GenerationConfig(batch_size=batch_size, audio_format="wav")

    t0 = time.perf_counter()
    log.info("[ace] generating (task=%s, instrumental=%s, dur=%s)…",
             params.task_type, params.instrumental, params.duration)
    res = generate_music(dit, llm, params=params, config=cfg, save_dir=str(out_dir))
    dt = time.perf_counter() - t0
    if not res.success:
        sys.exit(f"[ace] generation FAILED in {dt:.1f}s: {res.status_message}")

    paths = [a.get("path") for a in res.audios if a.get("path")]
    log.info("[ace] done — %d clip(s) in %.1fs", len(paths), dt)
    for p in paths:
        log.info("[ace]   -> %s", p)
    return paths

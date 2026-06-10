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

# Short variant name -> checkpoint config. Tensors/LoRAs are variant-specific.
# "sftturbo50" = community 0.5 sft+turbo weight merge (Aryanne/acestep-v15-test-merges,
# assembled locally into checkpoints/acestep-v15-sftturbo50) — the consensus best
# LISTENING checkpoint: "less crust, higher sound quality, less wrong notes".
VARIANTS = ("turbo", "sftturbo50", "base", "sft", "xl-turbo", "xl-base", "xl-sft")


def set_variant(name: str) -> str:
    """Select the DiT variant by short name ('base', 'xl-sft', ...) or full
    config name. Must be called before the first generate()."""
    cfg = name if name.startswith("acestep-") else f"acestep-v15-{name}"
    os.environ["ACESTEP_DIT_CONFIG"] = cfg
    return cfg


def variant_defaults(cfg: str | None = None) -> dict:
    """Per-variant inference defaults (docs/en/INFERENCE.md). Mismatched
    shift/steps is a classic garbled-output cause: turbo wants shift 3.0 &
    8 steps (no CFG); base/sft want shift 1.0, ~50 steps, guidance 5-9."""
    cfg = cfg or os.environ.get("ACESTEP_DIT_CONFIG", DIT_CONFIG)
    if "sftturbo" in cfg:
        # merge checkpoints want more steps than turbo and LOW guidance
        # (community-tested: 32-50 steps, CFG 1.0-1.5; high CFG turns harsh)
        return {"steps": 32, "shift": 3.0, "guidance": 1.2}
    if "turbo" in cfg:
        shift = 1.0 if "shift1" in cfg else 3.0
        # 12 steps not 8: infer_steps is honored on turbo since upstream v0.1.7,
        # and 12-20 is the community recommendation. Turbo ignores CFG.
        return {"steps": 12, "shift": shift, "guidance": 7.0}
    return {"steps": 50, "shift": 1.0, "guidance": 7.0}


def _has_weights(d: Path) -> bool:
    """True if a checkpoint dir has finished downloading (has weight shards)."""
    return d.is_dir() and (any(d.glob("*.safetensors")) or any(d.glob("**/*.safetensors")))


def _resolve_lm_model():
    """Use $ACESTEP_LM_MODEL if set; else the LARGEST fully-downloaded 5Hz LM
    under checkpoints/ (4B > 1.7B > 0.6B — 4B is the quality move with enough
    RAM); else the 1.7B default. The handler does NOT auto-download the LM, so
    pick one that's actually present (and not a half-finished download)."""
    env = os.environ.get("ACESTEP_LM_MODEL")
    if env:
        return env
    if CHECKPOINT_DIR.exists():
        for pref in ("acestep-5Hz-lm-4B", "acestep-5Hz-lm-1.7B", "acestep-5Hz-lm-0.6B"):
            if _has_weights(CHECKPOINT_DIR / pref):
                return pref
        avail = sorted(p.name for p in CHECKPOINT_DIR.iterdir()
                       if p.name.startswith("acestep-5Hz-lm-") and _has_weights(p))
        if avail:
            return avail[0]
    return "acestep-5Hz-lm-1.7B"


LM_MODEL = _resolve_lm_model()

_handlers = None
_handlers_mlx_dit = None


def _init(use_mlx_dit: bool = True):
    """Load DiT + LLM once; weights download to checkpoints/ on first call.

    use_mlx_dit=False forces the PyTorch(-MPS) DiT. REQUIRED when loading a
    LoRA on a Mac: the MLX DiT converts decoder weights once at init and then
    silently ignores any PEFT adapter loaded afterward (mlx_dit_init.py)."""
    global _handlers, _handlers_mlx_dit
    if _handlers is not None:
        if _handlers_mlx_dit != use_mlx_dit:
            log.warning("[ace] handlers already initialized with use_mlx_dit=%s — "
                        "requested %s ignored (one init per process)",
                        _handlers_mlx_dit, use_mlx_dit)
        return _handlers

    from acestep.handler import AceStepHandler
    from acestep.llm_inference import LLMHandler

    dit_config = os.environ.get("ACESTEP_DIT_CONFIG", DIT_CONFIG)  # turbo (fast) | base/sft (quality)
    t0 = time.perf_counter()
    log.info("[ace] loading DiT (%s, device=auto, mlx_dit=%s) — first run downloads weights…",
             dit_config, use_mlx_dit)
    dit = AceStepHandler()
    msg, ok = dit.initialize_service(
        project_root=str(ACE_ROOT), config_path=dit_config, device="auto",
        offload_to_cpu=False, use_mlx_dit=use_mlx_dit,
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
    _handlers_mlx_dit = use_mlx_dit
    return _handlers


def generate(params, out_dir, batch_size: int = 1, lora_path=None, lora_scale: float = 1.0):
    """Run one generation. `params` is an acestep GenerationParams. Returns wav paths.
    Pass `lora_path` (an adapter dir with adapter_model.safetensors) to apply a trained
    LoRA; `lora_scale` (0-1) controls how strongly it pulls toward the learned style."""
    from acestep.inference import GenerationConfig, generate_music

    if lora_path:
        log.info("[ace] LoRA requested — using PyTorch DiT (MLX DiT would silently ignore it)")
    dit, llm = _init(use_mlx_dit=not lora_path)
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

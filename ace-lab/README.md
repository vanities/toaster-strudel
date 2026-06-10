# ace-lab — instrumental music gen + LoRA, in your taste

A lab for running **ACE-Step 1.5** (open, MIT, local) to generate **instrumental**
music, feed it reference tracks ("do it in this style"), and eventually **LoRA**
fine-tune it on a corpus you choose. For fun / personal use.

Why ACE-Step: it's the strongest open instrumental model that's local-first
(Apple-Silicon **MLX** path), full-length, and ships first-class LoRA training.
Everything here forces `instrumental=True` — no vocals, ever.

## Layout

```
ace-lab/
├── setup.sh          one-time: clone + `uv sync` ACE-Step's env
├── gen.sh            text -> instrumental            (wraps generate.py)
├── style.sh          reference track -> in that style (wraps style_of.py)
├── generate.py       text2music (caption, bpm, key, duration)
├── style_of.py       "cover" / style-transfer from a reference audio
├── _ace.py           shared model bootstrap (DiT + 5Hz LLM planner, MLX-aware)
├── prep_dataset.py   build a LoRA dataset from a folder of audio
├── train_lora.sh     preprocess + LoRA train (2 stages)
├── to_strudel.py     import a generated wav as a toaster-strudel sample (hybrid)
└── vendor/ACE-Step/  the upstream repo (gitignored; has its own git)
```

## Setup (once)

```bash
./setup.sh          # clones ACE-Step if missing, then `uv sync` (big install)
```

First **generation** downloads the model weights (~several GB) into
`vendor/ACE-Step/checkpoints/`. Be patient on the first run.

## Generate

```bash
# text -> instrumental (turbo: fast, 8-step; the default)
./gen.sh "warm bonobo-ish ambient, rhodes, vinyl crackle, 82 bpm" --duration 60 --key "F# minor"

# quality pass: base/sft at 50 steps (slower, richer; guidance 5-9 sane, 7 default)
./gen.sh "lush downtempo, rhodes, hazy" --variant sft
./gen.sh "lush downtempo, rhodes, hazy" --variant xl-sft       # 4B DiT, best non-LoRA quality

# in the style of a track you like (the Suno-ish "cover" feature)
./style.sh ~/Music/track_you_love.mp3 "make it ambient, keep the mood" --strength 0.2
```

## Briefs — the crank workflow, ported to generative audio

One-line genre prompts produce generic songs. A **brief** is turn-the-crank discipline
for ACE: ONE reference track's measured DNA (from the `style-*` skills, incl. the
"Adam's actual hearts" corrections) turned into the three inputs that actually steer
the model:

| input | carries | comes from |
|---|---|---|
| caption | style+instruments+timbre+production descriptor stack (NO bpm/key) | the style skill's verbatim production vocabulary |
| script (lyrics field!) | the ARRANGEMENT: `[Intro - …]` `[Build]` `[Drop]` `[Breakdown]` tags | the reference card's section arc |
| bpm / key / duration params | the frame | the measured reference card |

```bash
./brief.sh briefs/skee-mask-terminal.json --seed 7                    # plain base
./brief.sh briefs/bonobo-kong.json --lora lora_output/handpicked-base/final --lora-scale 0.4
```

Output: `out/briefs/<name>/`. Each brief carries `targets` (centroid/flatness/dyn goals)
— measure with `tools/measure-wav.py`, iterate caption/script like a crank changelog.
The bare-`[Instrumental]` default gives the model NO arrangement at all; the script is
the temporal plan (vendored guidance: `vendor/ACE-Step/.claude/skills/acestep-songwriting/`).

`--strength` (style transfer dial): **0.2** = take the vibe & reinvent · **0.8** = stay close to the reference.

Steps/shift/guidance default to **variant-correct** values (turbo: 12 steps @ shift 3.0;
sftturbo50 merge: 32 @ 3.0, CFG 1.2; base/sft: 50 @ 1.0, CFG 7). Mismatched shift is a
classic garbled-output cause — earlier versions ran turbo at shift 1.0, which audibly hurt.

**Listening hierarchy (community consensus):** `sftturbo50` (local sft+turbo 0.5 merge,
"less crust, less wrong notes") ≳ `turbo` ≈ `sft` > `base` (the undistilled teacher —
TRAIN on it, don't listen to it). XL = more fidelity, shakier composition.

**ScragVAE** (community decoder retrain; restores the >6kHz air the stock VAE rolls off,
LoRA-compatible): `ACESTEP_VAE_CHECKPOINT=scragvae ./gen.sh ...` — flows through the MLX
decode path too.

**Captions:** prose in the training distribution beats hand-written tag-soup. Caption
your reference tracks with ACE's own training captioner and edit to taste:
`uv run --project vendor/ACE-Step python caption_refs.py datasets/handpicked/<track>.flac`
(writes `<track>.acecaption.txt`; `--all-corpus handpicked` for LoRA-v2 captions).

**Nobody keeps one-shot output**: batch 8-16 takes (use the 5090 — `./remote.sh`),
expect ~1 usable per 3-4, then fix the keeper with repaint/retake/cover instead of
re-rolling.

Outputs land in `out/`.

## LoRA — tune it on YOUR music  (VERIFIED ON THIS M4 MAX)

```bash
# 1. build a dataset from a manifest of favorites (full-quality source, no chopping)
python3 build_corpus.py --manifest corpora/handpicked.txt --name handpicked
#    (or prep_dataset.py for a quick folder; add per-track {"bpm":..,"keyscale":..} .json
#     sidecars if you have them — real bpm/key measurably helps conditioning)

# 2. bridge + preprocess + train, all in one (base variant, 200 epochs ≈ 2-3 h)
./train_lora.sh handpicked base 200

# 3. monitor
uv run --project vendor/ACE-Step tensorboard --logdir lora_output/handpicked-base/runs

# 4. use it (works on base AND cross-applies to turbo; scale 0.2-0.7, NOT 1.0)
./gen.sh "warm organic downtempo, rhodes" --variant base --lora lora_output/handpicked-base/final --lora-scale 0.6
./gen.sh "warm organic downtempo, rhodes" --variant turbo --lora lora_output/handpicked-base/final --lora-scale 0.4
```

Trains fine on Apple Silicon (MPS, bf16 — see `patches/0001-mps-bf16-training.patch`,
re-apply with `cd vendor/ACE-Step && git apply ../../patches/*.patch` after re-cloning):
~1.4-2.3 s/step at ≤180 s clips, ~2-3 h for 22 tracks × 200 epochs on an M4 Max.
Train against **base** (recommended adapter target — turbo is distilled and tunes worse);
checkpoints save every 10 epochs so you can A/B for the best one before `final`.
**Mac gotcha**: the MLX DiT silently ignores LoRAs — `--lora` automatically switches
to the PyTorch DiT (slower per step, correct output).

## Hybrid with toaster-strudel (optional)

You don't have to choose generative *or* Strudel. Use ACE-Step as a **texture/stem
source** and sequence it in code:

```bash
python3 to_strudel.py out/text2music/SOMETHING.wav --name acepad
# then in a track:  samples({ acepad: "/tracks/_ace_samples/acepad/acepad.wav" })
#                   s("acepad").chop(16).slow(4)
```

## Honest notes

- **For fun / personal use.** If you LoRA on copyrighted favorites, keep it local
  — don't distribute the adapter or sell outputs.
- The static analyzer / annealer in `../tools/` is the *controllable* path; this is
  the *generative* path. Different jobs — use whichever fits the goal.
- ACE-Step is fast-moving (2025); if an arg/flag drifts, the on-disk
  `vendor/ACE-Step/` is the source of truth (that's what these scripts were built
  against).

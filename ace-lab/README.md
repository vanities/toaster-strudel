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
# text -> instrumental
./gen.sh "warm bonobo-ish ambient, rhodes, vinyl crackle, 82 bpm" --duration 60 --key "F# minor"

# in the style of a track you like (the Suno-ish "cover" feature)
./style.sh ~/Music/track_you_love.mp3 "make it ambient, keep the mood" --strength 0.2
```

`--strength` (style transfer dial): **0.2** = take the vibe & reinvent · **0.8** = stay close to the reference.

Outputs land in `out/`.

## LoRA — tune it on YOUR music

```bash
# 1. build a dataset (writes [Instrumental] + caption sidecars; --chop for more clips)
python3 prep_dataset.py ~/Music/faves --caption "warm organic downtempo, rhodes, vinyl crackle" --chop 30

# 2. train the adapter (read vendor/ACE-Step/docs/en/LoRA_Training_Tutorial.md first)
./train_lora.sh faves
```

Adapter lands in `lora_output/<name>/`. **Hardware:** comfortable on a 16GB+ GPU;
doable on an M-series Mac but slow — for a real run, rent a GPU box and copy the
adapter back. `train_lora.sh`'s preprocess args + hyperparams may need a tweak
for your build (ACE-Step also has an interactive wizard: `cd vendor/ACE-Step && uv run python train.py`).

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

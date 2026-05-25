#!/usr/bin/env python3
"""Distill each analysis card into its style-* skill — repeatably.

For every references/analysis/<skill>/ dir, generate an "## Extracted DNA" block
(per-track progression + section arc + keys + dyn, plus links to the full card
files) and insert/replace it in the skill's markdown — resolving the symlink into
the Artist-Vault-Kit and writing the real file. Idempotent: re-run after adding
songs and it refreshes the block in place (keyed off the "## Extracted DNA"
heading), never duplicating.

    python3 tools/distill-skills.py
"""
import json
import os
import re
from pathlib import Path

ANALYSIS = Path("references/analysis")
SKILLS = Path("skills/skills")
MARK = "## Extracted DNA"


def collapse(seq):
    out = []
    for c in seq:
        if not out or out[-1] != c:
            out.append(c)
    return out


def arc_of(sections):
    out = []
    for s in sections:
        n = s.get("name", "?")
        if not out or out[-1] != n:
            out.append(n)
    return out


def block_for(skill_dir: Path) -> str | None:
    rows, cards = [], []
    for jp in sorted(skill_dir.glob("*.json")):
        r = json.loads(jp.read_text())
        v = r.get("voices", {})
        bk = ((v.get("bass") or {}).get("key") or {}).get("key", "?")
        mk = ((v.get("melody") or {}).get("key") or (v.get("full-mix") or {}).get("key") or {}).get("key", "?")
        prog = " ".join(collapse(r.get("chords", []))[:8]) or "—"
        arc = "→".join(arc_of(r.get("sections", []))) or "—"
        track = r["label"].split("·")[-1].strip()
        rows.append(f"| {track} | {r['stats']['bpm']} | {bk}/{mk} | `{prog}` | {arc} | {r['stats']['dyn_x']}× |")
        cards.append(f"`{jp.stem}.md`")
    if not rows:
        return None
    skill = skill_dir.name
    method = "btc" if any("chord_method" in json.loads(p.read_text()) for p in skill_dir.glob("*.json")) else "chroma"
    return "\n".join([
        MARK + " — measured loops + section arcs (analysis pipeline)", "",
        "Ripped from the reference audio (demucs stems → Basic Pitch → music21 → BTC large-voca "
        "chords → allin1 sections). **Progression = harmonic skeleton, arc = structural "
        "blueprint** — feeding these into a compose is what made the crank land vs. style-prose alone.", "",
        "| Track | BPM | key (bass/mel) | progression | section arc | dyn |",
        "|---|---|---|---|---|---|",
        *rows, "",
        f"**Full cards** (per-section Strudel `note()` seeds + register/interval/octave-displacement "
        f"DNA) — in the vault at `02_SOURCES/Music/analysis/pipeline-cards/{skill}/`: " + ", ".join(cards) + ".",
        "",
    ])


def upsert(real_path: str, block: str) -> None:
    txt = Path(real_path).read_text()
    if MARK in txt:
        before = txt[:txt.index(MARK)]
        region = txt[txt.index(MARK):]
        m = re.search(r"\n## ", region)            # next heading after our block
        after = region[m.start() + 1:] if m else ""
        new = before.rstrip() + "\n\n" + block.rstrip() + "\n\n" + after
    else:
        new = txt.rstrip() + "\n\n" + block.rstrip() + "\n"
    Path(real_path).write_text(new)


def main() -> int:
    n = 0
    for skill_dir in sorted(ANALYSIS.glob("style-*")):
        skill = skill_dir.name
        link = SKILLS / skill / "SKILL.md"
        if not link.exists():
            print(f"  skip {skill}: no skill symlink at {link}")
            continue
        block = block_for(skill_dir)
        if not block:
            print(f"  skip {skill}: no cards")
            continue
        real = os.path.realpath(link)
        upsert(real, block)
        n += 1
        print(f"  ✓ {skill} → {real}")
    print(f"\ndistilled {n} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

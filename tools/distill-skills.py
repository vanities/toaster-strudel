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
MARK_MIDI = "## MIDI DNA (exact)"
MARK_HOOK = "## Melody & Harmony DNA (Hooktheory)"


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


def _cards(skill_dir: Path, kind: str):
    """kind ∈ {audio, midi, hooktheory}."""
    out = []
    for jp in sorted(skill_dir.glob("*.json")):
        r = json.loads(jp.read_text())
        s = r.get("source")
        k = "midi" if s == "midi" else "hooktheory" if s == "hooktheory" else "audio"
        if k == kind:
            out.append((jp, r))
    return out


def audio_block(skill_dir: Path) -> str | None:
    rows, cards = [], []
    for jp, r in _cards(skill_dir, "audio"):
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


def _ivs(dna, n=4):
    return ", ".join(f"{i['interval']} ×{i['count']}" for i in dna.get("top_intervals", [])[:n])


def _voice_full(role: str, v: dict) -> str:
    dna, key = v.get("dna"), v.get("key")
    if not dna:
        return f"- **{role}** — `{v['strudel_voice']}` ({v['gm']}) — sparse"
    reg = dna["register"]
    disp = " · **octave-displaced**" if dna["octave_displaced"] else ""
    ks = (key or {}).get("key", "?")
    notes = v.get("strudel_full") or v.get("strudel_seed")
    line = (f"- **{role}** — {v['gm']} `{v['strudel_voice']}` · key {ks} · "
            f"{reg['low']}↔{reg['high']} (med {reg['median']}, {reg['span_semitones']}st){disp}\n"
            f"    - pcs {' '.join(dna['top_pitch_classes'][:7])} · {_ivs(dna, 6)}")
    if notes:
        line += f'\n    - notes ({dna["n_notes"]}, full): `note("{notes}")`'
    return line


def _voice_brief(role: str, v: dict) -> str:
    """Compact one-liner for inner voices when a style has too many tracks to
    inline every voice's full line (those live in the per-track card)."""
    dna = v.get("dna")
    if not dna:
        return f"- {role} — `{v['strudel_voice']}` ({v['gm']}) — sparse"
    reg = dna["register"]
    disp = " · octave-displaced" if dna["octave_displaced"] else ""
    return (f"- {role} — {v['gm']} `{v['strudel_voice']}` · {reg['low']}↔{reg['high']} "
            f"({dna['n_notes']} notes){disp} · {_ivs(dna, 3)}")


def hook_block(skill_dir: Path) -> str | None:
    cards = _cards(skill_dir, "hooktheory")
    if not cards:
        return None
    rows, details, sites = [], [], {}
    for jp, r in cards:
        track = r["label"].split("·")[-1].strip()
        site = r.get("source_site") or "Hooktheory"
        sites.setdefault(site, r.get("source_url"))
        prog = " ".join(r.get("chords", [])[:12]) or "—"
        rom = " ".join(r.get("romans", [])[:12])
        rows.append(f"| {track} | {r.get('key_str', '?')} | `{prog}` | {site} |")
        m = r.get("melody", {})
        dna = m.get("dna")
        d = [f"**{track}** — key {r.get('key_str', '?')} · src {site}",
             f"`progression: {' '.join(r.get('chords', [])[:16])}`  ({rom})"]
        if dna:
            reg = dna["register"]
            d.append(f"- melody — {reg['low']}↔{reg['high']} (med {reg['median']}, {reg['span_semitones']}st) · "
                     f"pcs {' '.join(dna['top_pitch_classes'][:7])} · {_ivs(dna, 6)}")
            if m.get("strudel_full"):
                d.append(f'- notes ({dna["n_notes"]}, full): `note("{m["strudel_full"]}")`')
        details.append("\n".join(d))
    credit = ", ".join(f"[{s}]({u})" if u else s for s, u in sorted(sites.items()))
    return "\n".join([
        MARK_HOOK + " — melody + functional harmony", "",
        "Scale-degree transcriptions from Hooktheory/TheoryTab — melody contour + chord "
        "function, free & community-sourced. Usually partial (the song's hook), not the full "
        "multitrack: internalize the melodic/harmonic shape and write original around it, "
        "don't just transcribe.", "",
        "| Track | key | progression | source |", "|---|---|---|---|",
        *rows, "",
        *[f"### {d}" for d in details], "",
        f"**Sourced from:** {credit}.", "",
    ])


def midi_block(skill_dir: Path) -> str | None:
    cards = _cards(skill_dir, "midi")
    if not cards:
        return None
    skill = skill_dir.name
    grid = (cards[0][1].get("midi") or {}).get("grid", "16th")
    full_inline = len(cards) <= 8            # few tracks → every voice's full line inline;
    rows, details, links, sites = [], [], [], {}   # many → leads full + brief inner voices (cards have all)
    for jp, r in cards:
        m, s = r["midi"], r["stats"]
        track = r["label"].split("·")[-1].strip()
        key = (s.get("key") or {}).get("key", "?")
        site = r.get("source_site") or "?"
        sites.setdefault(site, r.get("source_url"))
        v = r.get("voices", {})
        prog8 = " ".join(r.get("chords", [])[:8]) or "—"
        rows.append(f"| {track} | {m['tempo_bpm']} | {key} | {m['time_sig']} | `{prog8}` | "
                    f"{len(v)}{' +drm' if m['drums'] else ''} | {site} |")
        d = [f"**{track}** — {m['tempo_bpm']} BPM · {m['time_sig']} · key {key} · {len(v)} voices · src {site}",
             f"`progression: {' '.join(r.get('chords', [])[:16])}`"]
        for vname, vv in v.items():
            if full_inline or vname in ("bass", "melody"):
                d.append(_voice_full(vname, vv))   # full note-for-note line
            else:
                d.append(_voice_brief(vname, vv))  # gm/register/intervals; full line in the card
        details.append("\n".join(d))
        links.append(f"`{jp.stem}.md`")
    detail_note = (
        f"Every voice below carries its **complete** note-for-note line (full {grid}-note grid, "
        "all bars), GM patch, register, and interval fingerprint."
        if full_inline else
        f"With {len(cards)} tracks, each shows its **bass + melody** complete lines (full {grid}-note "
        "grid) plus a summary of every other voice; each inner voice's complete line is in its "
        "per-track card.")
    return "\n".join([
        MARK_MIDI + " — real sequenced notes, ground truth", "",
        "Parsed note-for-note from real Standard-MIDI sequences (see [[research-midi]] for "
        "sourcing). **Tempo, voices, and harmony are the composer's actual data — not estimated "
        "from audio.** Prefer these over the audio Extracted DNA above: BPM is exact (no "
        "octave-doubling), every voice is a real instrument line, and the progression comes from "
        "the notes themselves. Each voice names its GM patch → the Strudel `gm_*` voice that "
        "recreates that timbre.", "",
        "_Use as STYLE DNA, not a transcript — internalize the harmonic language, the "
        "octave-displaced bass moves, the interval signatures and voice choices, then write "
        "ORIGINAL material. A pasted seed is a cover; see [[feedback-capture-reference]]._", "",
        "| Track | BPM | key | time | progression | voices | source |",
        "|---|---|---|---|---|---|---|",
        *rows, "",
        detail_note + " Paste a `note(\"…\")` to hear that exact line; recombine/transform "
        "to write original.", "",
        *[f"### {d}" for d in details], "",
        "**MIDI sourced from:** " + ", ".join(
            f"[{site}]({url})" if url else site for site, url in sorted(sites.items())) +
        " — community-sequenced; credit the source if you ship a cover. Lossless `.mid` in vault "
        f"`02_SOURCES/Music/midi-sourced/{skill}/`; JSON cards "
        f"`02_SOURCES/Music/analysis/pipeline-cards/{skill}/`: {', '.join(links)}.",
        "",
    ])


def upsert(real_path: str, mark: str, block: str, before: str | None = None) -> None:
    txt = Path(real_path).read_text()
    if mark in txt:                                  # replace existing block in place
        head = txt[:txt.index(mark)]
        region = txt[txt.index(mark):]
        m = re.search(r"\n## ", region)              # next heading after our block
        after = region[m.start() + 1:] if m else ""
        new = head.rstrip() + "\n\n" + block.rstrip() + "\n\n" + after
    elif before and before in txt:                   # insert just before an anchor heading
        i = txt.index(before)
        new = txt[:i].rstrip() + "\n\n" + block.rstrip() + "\n\n" + txt[i:]
    else:                                            # append at end
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
        ab, mb, hb = audio_block(skill_dir), midi_block(skill_dir), hook_block(skill_dir)
        if not ab and not mb and not hb:
            print(f"  skip {skill}: no cards")
            continue
        real = os.path.realpath(link)
        if ab:
            upsert(real, MARK, ab)
        if mb:                                       # exact-MIDI block sits above the audio block
            upsert(real, MARK_MIDI, mb, before=MARK)
        if hb:                                       # Hooktheory melody+harmony, also above audio
            upsert(real, MARK_HOOK, hb, before=MARK)
        tag = "+".join(t for t, x in (("audio", ab), ("midi", mb), ("hook", hb)) if x)
        n += 1
        print(f"  ✓ {skill} ({tag}) → {real}")
    print(f"\ndistilled {n} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

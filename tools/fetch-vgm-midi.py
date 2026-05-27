#!/usr/bin/env python3
"""Scrape VGMusic.com — one good MIDI per distinct track of a game — into the vault.

VGMusic lays out each system as one flat page: a `<td class="header">Game</td>`
row starts a game section, then `<a href="x.mid">Title</a>` rows until the next
header. Many tracks have several sequences (numbered "(2)", "(XG)", "(Remix)"…);
we keep the FIRST (the canonical/base sequence) per distinct title and skip the
alternates.

    # all Donkey Kong Country games → style-david-wise
    python3 tools/fetch-vgm-midi.py \
      --page https://www.vgmusic.com/music/console/nintendo/snes/ \
      --game "Donkey Kong Country" --skill style-david-wise

    # repeatable: re-running skips files already downloaded
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

VAULT = Path.home() / "git/work/matty/Artist-Vault-Kit/vault/02_SOURCES/Music/midi-sourced"
UA = {"User-Agent": "Mozilla/5.0"}
HEADER_RE = re.compile(r'<td class="header"[^>]*>(.*?)</td>', re.I | re.S)
ANCHOR_RE = re.compile(r'<a href="([^"]+\.mid)">(.*?)</a>', re.I | re.S)
SMALL = {"of", "the", "a", "in", "to", "and", "on", "for", "s"}


def slugify(s: str) -> str:
    s = re.sub(r"&[a-z]+;", " ", s)               # &quot; &amp; …
    s = re.sub(r"[^\w\s-]", " ", s).strip().lower()
    return re.sub(r"[\s_-]+", "-", s) or "track"


def titleize(slug: str) -> str:
    return " ".join(w if (w in SMALL and i) else w.capitalize() for i, w in enumerate(slug.split("-")))


def clean_title(raw: str) -> str:
    t = re.sub(r"<[^>]+>", "", raw)               # strip stray tags
    t = re.sub(r"&[a-z]+;", "", t)
    t = re.sub(r"\s*\([^)]*\)", "", t)             # drop ALL parentheticals — on VGMusic
    return t.strip().strip('"').strip()            # they're version/soundfont/mix markers


def fetch(url: str) -> bytes:
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()


def sections(html: str):
    """Yield (game_name, [(href, title), …]) in document order."""
    parts = HEADER_RE.split(html)                  # [pre, game1, body1, game2, body2, …]
    for i in range(1, len(parts), 2):
        game = re.sub(r"<[^>]+>|&[a-z]+;", "", parts[i]).strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        yield game, ANCHOR_RE.findall(body)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--page", required=True, help="VGMusic system listing URL")
    ap.add_argument("--game", action="append", required=True, help="game-name substring (repeatable)")
    ap.add_argument("--exact-game", action="store_true", help="match the game header exactly, not as a substring "
                    "(needed when one title is a prefix of another, e.g. 'Final Fantasy II' ⊂ 'Final Fantasy III')")
    ap.add_argument("--prefix", default="", help="prepend to each output filename — keeps same-titled tracks from "
                    "different games (FF4/5/6 all share 'Prelude') from colliding when merged into one skill")
    ap.add_argument("--skill", required=True)
    ap.add_argument("--min-bytes", type=int, default=3000, help="skip files smaller than this (jingles)")
    ap.add_argument("--limit", type=int, default=0, help="cap downloads (0 = no cap)")
    ap.add_argument("--record-only", action="store_true", help="don't download; just write _sources.json for files already on disk")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    base = args.page.rsplit("/", 1)[0] + "/"
    html = fetch(args.page).decode("latin-1", "replace")
    wants = [g.strip().lower() for g in args.game]
    dest = VAULT / args.skill
    dest.mkdir(parents=True, exist_ok=True)

    cand: dict[str, list[tuple[str, str, str]]] = {}   # clean-title -> [(href, raw, game)]
    for game, anchors in sections(html):
        g = game.strip().lower()
        if not (any(g == w for w in wants) if args.exact_game else any(w in g for w in wants)):
            continue
        for href, raw in anchors:
            ct = clean_title(raw)
            if ct:
                cand.setdefault(ct, []).append((href, raw, game))
    picked: dict[str, tuple[str, str]] = {}        # clean-title -> (href, game)
    for ct, lst in cand.items():
        bases = [x for x in lst if "(" not in x[1]]  # prefer a non-alternate sequence
        href, _raw, game = (bases or lst)[0]
        picked[ct] = (href, game)
    print(f"  {args.skill}: {len(picked)} distinct tracks across "
          f"{sorted({g for _h, g in picked.values()})}", file=sys.stderr)

    sources_path = dest / "_sources.json"             # per-file attribution {file: {site, url}}
    sources = json.loads(sources_path.read_text()) if sources_path.exists() else {}
    got = skipped_small = existed = recorded = 0
    for ct, (href, _game) in sorted(picked.items()):
        if args.limit and got >= args.limit:
            break
        fname = f"{args.prefix}{slugify(ct)}.mid"
        out = dest / fname
        url = urllib.parse.urljoin(base, href)
        if out.exists():                               # attribute files already on disk
            existed += 1
            sources[fname] = {"site": "VGMusic.com", "url": url}
            recorded += 1
            continue
        if args.record_only:
            continue
        if args.dry_run:
            print(f"    would fetch {titleize(slugify(ct))} <- {href}", file=sys.stderr)
            continue
        try:
            data = fetch(url)
        except Exception as e:
            print(f"    FAIL {ct}: {e}", file=sys.stderr)
            continue
        if len(data) < args.min_bytes:
            skipped_small += 1
            continue
        out.write_bytes(data)
        sources[fname] = {"site": "VGMusic.com", "url": url}
        recorded += 1
        got += 1
        time.sleep(0.15)                            # be polite
    if not args.dry_run:
        sources_path.write_text(json.dumps(sources, indent=2, sort_keys=True))
    print(f"  → downloaded {got}, had {existed}, skipped {skipped_small} tiny; "
          f"recorded {recorded} sources → {sources_path.name}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

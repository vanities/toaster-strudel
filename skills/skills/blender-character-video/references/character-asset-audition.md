# Character Asset Audition Notes

Use this reference when searching, downloading, and presenting candidate character models for a Blender music video.

## Durable lesson

When the user asks whether assets were downloaded "so I can look," they need reviewable local artifacts, not just candidate descriptions. Be explicit about which candidates are merely researched and which are actually downloaded/imported/rendered.

## Minimum audition packet for downloaded candidates

For every model that makes it past search, produce reviewable local evidence without creating unnecessary folder sprawl.

Preferred lightweight layout when the user asks to “download a few” or “don’t make too many folders”:

```text
renders/<project>/assets/candidates/
├── <candidate-a>.<glb|fbx|zip|rar>
├── <candidate-b>.<glb|fbx|zip|rar>
├── <candidate-a>_front.png
├── <candidate-a>_threeq.png
├── <candidate-b>_front.png
├── <candidate-b>_threeq.png
├── candidate_contact_sheet.png
└── CANDIDATE_INSPECT.txt
```

Use per-candidate subfolders only when extraction or texture dependencies require them. If you create extra `downloads/`, `models/`, probe, or frame folders during exploration, consolidate or clean them before reporting unless the user explicitly wants the full archive.

For each candidate in the packet:

1. Save the original source asset or archive locally.
2. Import it into Blender when possible and render quick front / 3/4 previews; side views are optional unless silhouette matters.
3. Build one combined `candidate_contact_sheet.png` for user review.
4. Write `CANDIDATE_INSPECT.txt` or markdown notes with:
   - source page / license summary
   - file formats downloaded
   - Blender import status
   - armatures / animation clips, if present
   - mesh names and approximate vertex/poly counts, if available
   - material / texture structure
   - fit for the brief, including what it is *not* good at
   - blocked imports/extractions stated as candidate-specific status, not global tool limitations
5. Present the combined contact sheet as a `MEDIA:` attachment or direct path for user review.

## Reporting rule

Say one of:

- `Downloaded and inspected:` followed by local asset + preview paths.
- `Researched only, not downloaded:` followed by candidate links and why.
- `Blocked:` followed by the missing credential/paywall/license/format issue.

Do not imply that all researched candidates were downloaded. If only one candidate was downloaded, say so plainly.

## Candidate comparison

Keep a candidate log such as `renders/<project>/assets/CHARACTER_CANDIDATES.md`. After inspection, update entries from speculative notes to actual local paths and verdicts. This makes future sessions resume from evidence instead of re-searching.

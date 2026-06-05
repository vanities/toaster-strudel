# Vendored Blender skills — attribution

The following eight skills under `skills/skills/blender-*` are **third-party, vendored verbatim** (not original to this GPLv3 repo):

| Skill | Domain |
|---|---|
| `blender-python-scripting` | bpy operators, panels, add-ons, handlers, property system (Python 3.13 / Blender 5.1) |
| `blender-geometry-nodes` | ~373 geometry nodes, procedural modeling, fields, volume grids |
| `blender-shader-nodes` | ~95 shader nodes, PBR/procedural/glass/metal recipes |
| `blender-compositing-nodes` | ~80 compositor nodes, denoise/color-grade/keying |
| `blender-animation-rigging` | keyframes, FCurves, drivers, ~45 constraints, IK/FK, NLA |
| `blender-modeling-modifiers` | ~50 modifiers, bmesh API, hard-surface/retopo |
| `blender-physics-simulation` | rigid body, cloth, fluid (Mantaflow), soft body, particles |
| `blender-scene-rendering` | Cycles/EEVEE, output formats, import/export, color management |

**Source:** [ra100/blender-claude-plugin](https://github.com/ra100/blender-claude-plugin) (plugin name `blender-skills`, author *svarba*).
**Commit:** `78e9151fdc9e01ce37f1d16a9b677c3047411885` (copied 2026-05-30).
**License:** MIT — full text in `blender-skills-LICENSE.txt` (Copyright © 2026 ra100). MIT is GPLv3-compatible; the notice is preserved here per its terms.

## Notes for this repo

- **MCP-optional.** Each skill prefers the official Blender MCP Server (`blender-mcp`, Blender 5.1+) when connected, but explicitly **falls back to emitting Python (`bpy`) scripts** when it is not — which matches this repo's headless `tools/blender_*.py` → Blender-CLI render workflow. No MCP server is required to benefit from the API references/recipes.
- Each skill is self-contained: `SKILL.md` + a `references/` catalog. They cross-reference `../../docs/blender-mcp-setup.md` (copied to `skills/docs/`), which resolves from `skills/skills/<skill>/`.
- Complements the repo's own `blender-music-video` and `blender-datamosh-shader-filter` skills (which stay GPLv3, authored here).
- Optional setup guidance for the MCP path is in `skills/docs/blender-mcp-setup.md`.

## Considered but not copied

- **Dev-GOM/claude-code-marketplace › blender-toolkit** (Apache-2.0) — one monolithic MCP-driven toolkit skill; overlaps this set, MCP-centric. Available on request.
- **freshtechbro/claudedesignskills › blender-web-pipeline** (MIT) — Blender→glTF→Three.js/Babylon web export; aimed at web 3D, not MP4 music videos.
- **Impertio-Studio/Blender-Bonsai-…** — 73 AEC/BIM/IFC skills; too domain-specific (architecture).

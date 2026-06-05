# Blender MCP Server Setup

This plugin's skills are designed to work with the **official Blender MCP Server** from Blender Lab. Without the MCP server, skills fall back to generating Python scripts that you paste/run manually. With it, Claude can drive Blender directly.

Project: <https://www.blender.org/lab/mcp-server/>
Source: <https://projects.blender.org/lab/blender_mcp>

> **Security:** the MCP server executes LLM-generated Python code in your Blender session with no sandbox. Use a VM or a workstation without sensitive data.

## Architecture

```
Claude Code ──MCP (stdio/http)──► blender-mcp server ──TCP localhost:9876──► Blender Add-on (bpy)
```

Two pieces required:

1. **Blender Add-on** (in Blender 5.1+) — runs the TCP bridge inside Blender on `localhost:9876`.
2. **MCP Server** (`blender-mcp` Python package) — Claude talks to this; it forwards code to the add-on.

## 1. Install the Add-on (Blender 5.1+)

Requires Blender 5.1 or newer.

**Option A — drag & drop** (recommended, gets update notifications):

1. Open this URL in a browser, then drag the link into Blender once to add the Blender Lab repository, then drag again to install:
   <https://projects.blender.org/lab/blender_mcp/releases/download/v1.0.0/mcp-1.0.0.zip?repository=https%3A%2F%2Flab.blender.org%2F&blender_version_min=5.1.0>

**Option B — manual zip install:**

1. Download `mcp-1.0.0.zip`: <https://projects.blender.org/lab/blender_mcp/releases/download/v1.0.0/mcp-1.0.0.zip>
2. `Edit → Preferences → Get Extensions → Install from Disk…` → select the zip.

Then in `Edit → Preferences → Add-ons → MCP`:

- Enable "Online Access" in System preferences (required).
- Defaults: host `localhost`, port `9876`, auto-start enabled.
- Verify the server is running (status panel in add-on prefs).

## 2. Install the MCP Server

### Option A — `.mcpb` bundle (Claude Desktop, Cursor, any client supporting `.mcpb`)

1. Download `blender-1.0.0.mcpb`: <https://projects.blender.org/lab/blender_mcp/releases/download/v1.0.0/blender-1.0.0.mcpb>
2. Install per your client's `.mcpb` flow (Claude Desktop: `Settings → Extensions → Install from file`).

The bundle ships with `uv` config — your client launches `uv run blender-mcp` automatically.

### Option B — pip install (Claude Code, any stdio MCP client)

```bash
# requires Python 3.10+
pip install --user "git+https://projects.blender.org/lab/blender_mcp"
# or with uv:
uv tool install "git+https://projects.blender.org/lab/blender_mcp"
```

Verify:

```bash
blender-mcp --help
```

## 3. Wire it into Claude Code

Add to `~/.claude/settings.json` (or project `.claude/settings.json`) under `mcpServers`:

```json
{
  "mcpServers": {
    "blender": {
      "command": "blender-mcp",
      "args": ["--transport", "stdio"]
    }
  }
}
```

Or with uv:

```json
{
  "mcpServers": {
    "blender": {
      "command": "uv",
      "args": ["tool", "run", "blender-mcp", "--transport", "stdio"]
    }
  }
}
```

HTTP transport (for clients that prefer streamable HTTP):

```bash
blender-mcp --transport http --host 127.0.0.1 --port 8000
```

Restart Claude Code. Open Blender (with the add-on running). Verify the `blender` MCP server reports connected and tools are listed.

## Tools Provided

| Tool | Purpose |
| --- | --- |
| `execute_blender_code` | Run arbitrary `bpy` Python in Blender. Primary action tool. |
| `get_objects_summary` | List scene objects with type/transform/poly counts. |
| `get_object_detail_summary` | Per-object details (materials, modifiers, constraints). |
| `get_blendfile_summary_datablocks` | All datablocks (meshes, materials, images, node groups, …). |
| `get_blendfile_summary_missing_files` | Broken file paths. |
| `get_blendfile_summary_of_linked_libraries` | Linked/appended `.blend` libraries. |
| `get_blendfile_summary_path_info` | File path resolution info. |
| `get_blendfile_summary_usage_guess` | Heuristic usage classification of datablocks. |
| `get_python_api_docs` | Fetch full doc for an API symbol. |
| `search_api_docs` | Full-text search the bundled Python API reference. |
| `search_manual_docs` | Full-text search the bundled user manual. |
| `get_screenshot_of_area_as_image` | Screenshot one editor area as PNG. |
| `get_screenshot_of_window_as_image` | Full-window screenshot as PNG. |
| `get_screenshot_of_window_as_json` | Window layout as structured JSON. |
| `jump_to_tab_by_name` | Switch workspace tab by name. |
| `jump_to_tab_by_space_type` | Switch to a tab containing a given editor type. |
| `jump_to_view3d_object_by_name` | Frame an object in the 3D viewport. |
| `jump_to_view3d_object_data_by_name` | Frame by object-data name. |
| `render_thumbnail_to_path` | Quick low-res render to disk. |
| `render_viewport_to_path` | Viewport OpenGL render to disk. |

## Headless / Background Mode

Run Blender headless with the bridge:

```bash
blender --background scene.blend --online-mode --command blender_mcp -- --host localhost --port 9876
```

In background mode each request must complete before returning (no deferred/interactive responses).

## Troubleshooting

- **"Online access must be enabled"** — toggle System preferences → Network → Allow Online Access.
- **MCP server can't connect** — confirm the add-on is enabled and running (`Preferences → Add-ons → MCP`), check port 9876 is free.
- **Tools missing in Claude** — restart Claude Code after editing `mcpServers`. Run `claude mcp list` to confirm registration.
- **Code errors silently** — set add-on `Log` toggle on; tool requests print to Blender's terminal.

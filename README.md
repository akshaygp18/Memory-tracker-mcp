# Memory Tracker MCP

An MCP server that gives an AI assistant persistent memory, backed by an OpenAI vector store.

Memories are plain text. `save_memory` uploads each one as a file into a vector store named `MEMORIES`; `search_memory` runs a semantic search over that store and returns the matching chunks. The store is created on first use and reused after that, so memories persist across sessions and across clients.

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- An OpenAI API key

## Setup

```bash
uv sync
```

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-...
```

`.env` is gitignored. The server calls `load_dotenv()` at import, which resolves relative to the working directory — this is why the client configs below pass `--directory`.

## Tools

| Tool | Argument | Returns |
| --- | --- | --- |
| `save_memory` | `memory: str` — the text to remember | `{"status": "saved", "vector store id": ...}` |
| `search_memory` | `query: str` — what to look for | `{"results": [chunk, ...]}` |

## Running it

Development, with the MCP Inspector:

```bash
uv run mcp dev server.py
```

Directly over stdio (what MCP clients do):

```bash
uv run python server.py
```

## Client configuration

### Claude Code

[`.mcp.json`](.mcp.json) in this repo is picked up automatically when you start Claude Code in this directory. No further setup.

### Claude Desktop

Add the block below to `claude_desktop_config.json`, then fully quit Claude Desktop (right-click the system tray icon → Quit — closing the window is not enough) and relaunch.

```json
{
  "mcpServers": {
    "memory-tracker": {
      "command": "C:\\Users\\shivu\\.local\\bin\\uv.exe",
      "args": [
        "run",
        "--directory",
        "f:\\Agentic AI\\Memory_tracker_mcp",
        "python",
        "server.py"
      ]
    }
  }
}
```

Two things differ from the Claude Code config:

- **Absolute path to `uv.exe`.** Claude Desktop launches servers with a minimal `PATH` that usually excludes `~\.local\bin`, so a bare `uv` fails to spawn. Claude Code inherits your shell's `PATH`, so the short form works there.
- **Where the config file lives.** For the standard installer it is `%APPDATA%\Claude\claude_desktop_config.json`. For the **Microsoft Store (MSIX) build**, AppData is redirected and the real path is:

  ```
  %LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json
  ```

  Editing the non-packaged path on a Store install has no effect. Reach it from the app instead via Settings → Developer → Edit Config.

## Troubleshooting

**`Failed to build ... Expected a Python module at src\memory_tracker_mcp\__init__.py`**

`pyproject.toml` sets `package = false` under `[tool.uv]`, which tells uv to treat this as a flat script project rather than build it as a package. Without it, every `uv run` tries to build an installable package and fails, because the server is a single `server.py` at the repo root and there is no `src/` layout. Note that `[project.scripts]` still declares a `memory_tracker_mcp:main` entry point that does not exist — harmless while `package = false` is set, but it will break the build again if that line is ever removed.

**Tools appear in the client but every call errors**

Almost always a missing `OPENAI_API_KEY`. The `--directory` argument is what lets `load_dotenv()` find `.env`; drop it and the server still starts, but the OpenAI client has no key. As a fallback, pass the key through the config instead:

```json
"env": { "OPENAI_API_KEY": "sk-..." }
```

That hardcodes the key into the config file, so prefer `.env` when it works.

**Server shows as failed to start**

Check the client's MCP log — for Claude Desktop, `logs\mcp-server-memory-tracker.log` in the same config directory. A spawn/ENOENT error means the `uv.exe` path is wrong; confirm it with `where uv`.

## Notes

- Every `save_memory` call writes a temp file with `delete=False` and opens it without closing the handle, so temp files accumulate in `%TEMP%`. Passing the text directly (`file=("memory.txt", memory.encode())`) would avoid the temp file entirely.
- `get_or_create_vector_store` scans stores by name on every call, so each tool invocation costs an extra list request.

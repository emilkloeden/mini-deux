# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the editor
uv run mini <filename>

# Install dependencies
uv sync

# Add a dependency
uv add <package>
```

There are no tests or linter configurations currently in this project.

## Architecture

`mini` is a terminal text editor written in Python, modeled after the `kilo` editor (a C-based tutorial editor). It uses raw terminal mode and ANSI escape codes to drive the display directly.

### Data flow

The main loop (`main.py`) alternates between two calls: `editor_refresh_screen()` and `editor_process_keypress()`. All editor state lives in a single `EditorConfig` dataclass (`types.py`) that is passed by reference throughout.

Each line of the file is stored as an `EditorRow` (also in `types.py`). Each row maintains two representations:
- `chars` — the raw characters as stored on disk
- `render` — the display-space string after tab expansion (tabs → spaces)
- `hl` — per-character highlight array aligned with `render` (populated by `highlight.py`)

The `cx`/`cy` cursor coordinates are in `chars`-space; `rx` is the render-space column. The functions `editor_row_cx_to_rx` / `editor_row_rx_to_cx` in `editor.py` convert between them.

### Module responsibilities

| Module | Responsibility |
|--------|---------------|
| `main.py` | Entry point, terminal setup, main loop |
| `types.py` | `EditorRow` and `EditorConfig` dataclasses |
| `editor.py` | All editor operations: input handling, rendering, file I/O, scrolling, search |
| `highlight.py` | Tree-sitter parsing and `update_syntax()` — called once per frame in `editor_refresh_screen()` |
| `terminal.py` | Raw mode enable/disable, `editor_read_key()`, `die()` |
| `ansi.py` | ANSI escape code constants and helpers |
| `append_buffer.py` | `AppendBuffer` — accumulates output then flushes in one `write()` call |
| `config.py` | Constants: `TAB_STOP=8`, `QUIT_TIMES=3`, editor name/version |
| `keyboard.py` | `EditorKey` IntEnum for special keys |
| `constants.py` | Low-level constants (e.g. `STDIN_FILENO`) |

### Syntax highlighting

`highlight.py` owns all tree-sitter logic and has no circular imports (it only imports from `types.py` and `config.py`). `update_syntax(E)` re-parses the full file every frame using tree-sitter-python. It only activates for `.py` files; all other files get empty `row.hl` lists (no highlighting). Highlight types are integer constants (`HL_NORMAL` through `HL_TYPE`), and `HL_COLORS` maps them to ANSI SGR codes.

### Key bindings

| Key | Action |
|-----|--------|
| Ctrl-S | Save |
| Ctrl-Q | Quit (×3 if unsaved changes) |
| Ctrl-F | Find (arrow keys navigate matches) |
| Ctrl-H / Backspace | Delete character |

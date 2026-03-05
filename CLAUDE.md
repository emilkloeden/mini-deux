# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the editor
uv run mini <filename>

# Run tests
uv run pytest

# Install dependencies
uv sync

# Add a dependency
uv add <package>
```

## Architecture

`mini` is a modal terminal text editor written in Python, modeled after the `kilo` editor but extended with a Vim-inspired modal interface, multi-language tree-sitter syntax highlighting, themes, and undo/redo. It uses raw terminal mode and ANSI escape codes to drive the display directly.

### Data flow

The main loop (`main.py`) alternates between two calls: `editor_refresh_screen()` and `editor_process_keypress()`. All editor state lives in a single `EditorConfig` dataclass (`types.py`) that is passed by reference throughout.

Each line of the file is stored as an `EditorRow` (also in `types.py`). Each row maintains two representations:
- `chars` — the raw characters as stored on disk
- `render` — the display-space string after tab expansion (tabs → spaces)
- `hl` — per-character highlight array aligned with `render` (populated by `highlight.py`)

The `cx`/`cy` cursor coordinates are in `chars`-space; `rx` is the render-space column. `editor_row_cx_to_rx` / `editor_row_rx_to_cx` in `editor.py` convert between them.

### Module responsibilities

| Module | Responsibility |
|--------|---------------|
| `main.py` | Entry point, terminal setup, main loop |
| `types.py` | `EditorRow` and `EditorConfig` dataclasses, `Mode` enum |
| `editor.py` | All editor operations: input handling, rendering, file I/O, scrolling, search, undo/redo |
| `highlight.py` | Tree-sitter parsing and `update_syntax()` — called once per frame in `editor_refresh_screen()` |
| `themes.py` | `Theme` dataclass and all built-in theme definitions; `get_theme()` |
| `terminal.py` | Raw mode enable/disable, `editor_read_key()`, `die()` |
| `ansi.py` | ANSI escape code constants and helpers |
| `append_buffer.py` | `AppendBuffer` — accumulates output then flushes in one `write()` call |
| `config.py` | Constants: `TAB_STOP=8`, `QUIT_TIMES=3`, editor name/version |
| `keyboard.py` | `EditorKey` IntEnum for special keys including `ALT_DIGIT_0..9` |
| `constants.py` | Low-level constants (e.g. `STDIN_FILENO`) |

### Modes

The editor is modal with two modes stored in `EditorConfig.mode` (a `Mode` enum):

- **NORMAL** — Vim-style navigation and commands; the default on startup
- **INSERT** — character insertion; entered via `i`, `a`, `A`, `o`, `O`

`_normal_key()` and `_insert_key()` in `editor.py` dispatch keypresses for each mode.

### Normal mode key bindings

| Key(s) | Action |
|--------|--------|
| `h` / `←` | Move left |
| `l` / `→` | Move right |
| `j` / `↓` | Move down |
| `k` / `↑` | Move up |
| `w` | Word forward |
| `b` | Word backward |
| `e` | Word end |
| `0` / `Home` | Start of line |
| `$` / `End` | End of line |
| `gg` | Go to top |
| `G` | Go to bottom (or line N with count) |
| `i` | Enter INSERT before cursor |
| `a` | Enter INSERT after cursor |
| `A` | Enter INSERT at end of line |
| `o` | Open line below, INSERT |
| `O` | Open line above, INSERT |
| `x` | Delete character under cursor |
| `dd` | Delete line |
| `dw` / `db` / `de` | Delete to word motion |
| `dh` / `dl` | Delete char left/right |
| `dgg` / `dG` | Delete to top/bottom |
| `u` | Undo |
| Ctrl-R | Redo |
| Ctrl-S | Save |
| Ctrl-Q | Quit (×3 if unsaved changes) |
| Ctrl-F | Find (arrow keys navigate matches) |
| `Esc` | Cancel pending operator / count |
| Alt-0..9 | Switch theme |

Counts work for most motions: `5j`, `3w`, `2dd`, etc.

### Insert mode key bindings

| Key | Action |
|-----|--------|
| `Esc` | Return to NORMAL mode |
| Printable chars | Insert character |
| Enter | Insert newline |
| Backspace / Ctrl-H | Delete character before cursor |
| Arrow keys | Move cursor |
| Home / End | Start / end of line |
| Page Up / Down | Scroll |

### Syntax highlighting

`highlight.py` owns all tree-sitter logic and has no circular imports (it only imports from `types.py` and `config.py`). `update_syntax(E)` re-parses the full file every frame. The extension of `E.file_name` selects the language; unknown extensions leave `row.hl` empty.

Highlight types are integer constants (`HL_NORMAL=0` … `HL_TYPE=6`). The active theme's `hl_colors` tuple maps each constant to an ANSI SGR sequence.

Supported languages: `.py`, `.js`, `.mjs`, `.cjs`, `.ts`, `.tsx`, `.rs`, `.go`, `.sh`, `.bash`, `.json`, `.toml`, `.c`, `.h`, `.java`, `.md`

### Themes

`themes.py` defines 10 built-in themes. The active theme is stored as a name string in `EditorConfig.theme_name` and looked up via `get_theme()` each frame. Themes control syntax highlight colours, status-bar colours, and gutter colours.

| Alt key | Theme |
|---------|-------|
| Alt-0 | default |
| Alt-1 | Tokyo Night |
| Alt-2 | Nord |
| Alt-3 | Catppuccin Mocha |
| Alt-4 | Dracula |
| Alt-5 | Gruvbox |
| Alt-6 | Solarized Dark |
| Alt-7 | One Dark |
| Alt-8 | Monokai |
| Alt-9 | Rosé Pine |

### Undo / redo

Each mutating operation calls `_push_undo(E)` before making changes. Snapshots are `(list[str], cx, cy)` tuples stored on `EditorConfig.undo_stack`. `editor_undo` / `editor_redo` move snapshots between the undo and redo stacks and call `_restore_snapshot`.

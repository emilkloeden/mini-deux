# mini

A modal terminal text editor written in Python. Inspired by the [`kilo`](https://github.com/antirez/kilo) tutorial editor, extended with a Vim-style modal interface, tree-sitter syntax highlighting, themes, and undo/redo.

## Installation

Requires Python 3.11+ and [`uv`](https://docs.astral.sh/uv/).

```bash
git clone <repo>
cd mini
uv sync
```

## Usage

```bash
uv run mini <filename>
```

## Key bindings

### Normal mode (default)

**Navigation**

| Key | Action |
|-----|--------|
| `h` / `←` | Left |
| `l` / `→` | Right |
| `j` / `↓` | Down |
| `k` / `↑` | Up |
| `w` | Word forward |
| `b` | Word backward |
| `e` | Word end |
| `0` / `Home` | Start of line |
| `$` / `End` | End of line |
| `gg` | Top of file |
| `G` | Bottom of file |
| `5G` | Go to line 5 |

Most motions accept a count prefix: `3w`, `10j`, etc.

**Editing**

| Key | Action |
|-----|--------|
| `i` | Insert before cursor |
| `a` | Insert after cursor |
| `A` | Insert at end of line |
| `o` | Open new line below |
| `O` | Open new line above |
| `x` | Delete character under cursor |
| `dd` | Delete line |
| `dw` / `db` / `de` | Delete to word motion |
| `dh` / `dl` | Delete character left / right |
| `dgg` / `dG` | Delete to top / bottom of file |
| `u` | Undo |
| `Ctrl-R` | Redo |

**File & search**

| Key | Action |
|-----|--------|
| `Ctrl-S` | Save |
| `Ctrl-Q` | Quit (press ×3 with unsaved changes) |
| `Ctrl-F` | Search (arrow keys cycle matches, `Esc` to cancel) |

**Themes**

| Key | Theme |
|-----|-------|
| `Alt-0` | Default |
| `Alt-1` | Tokyo Night |
| `Alt-2` | Nord |
| `Alt-3` | Catppuccin Mocha |
| `Alt-4` | Dracula |
| `Alt-5` | Gruvbox |
| `Alt-6` | Solarized Dark |
| `Alt-7` | One Dark |
| `Alt-8` | Monokai |
| `Alt-9` | Rosé Pine |

### Insert mode

| Key | Action |
|-----|--------|
| `Esc` | Return to Normal mode |
| Printable characters | Insert text |
| `Enter` | New line |
| `Backspace` / `Ctrl-H` | Delete character before cursor |
| Arrow keys / `Home` / `End` | Move cursor |

## Syntax highlighting

Highlighting is provided by [tree-sitter](https://tree-sitter.github.io/tree-sitter/) and activates automatically based on file extension.

| Extension | Language |
|-----------|----------|
| `.py` | Python |
| `.js` `.mjs` `.cjs` | JavaScript |
| `.ts` `.tsx` | TypeScript |
| `.rs` | Rust |
| `.go` | Go |
| `.c` `.h` | C |
| `.java` | Java |
| `.sh` `.bash` | Bash |
| `.json` | JSON |
| `.toml` | TOML |
| `.md` | Markdown (headings, code blocks, blockquotes) |

## Development

```bash
# Run tests
uv run pytest

# Add a dependency
uv add <package>
```

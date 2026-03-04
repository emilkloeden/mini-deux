from dataclasses import dataclass

from mini.terminal import term


def _rgb_fg(r: int, g: int, b: int) -> str:
    return f"\x1b[38;2;{r};{g};{b}m"


def _rgb_bg(r: int, g: int, b: int) -> str:
    return f"\x1b[48;2;{r};{g};{b}m"


@dataclass(frozen=True)
class Theme:
    hl_colors: tuple[str, ...]  # indexed by HL_NORMAL=0 … HL_TYPE=6
    statusbar_normal: str       # ANSI prefix applied at start of status bar
    statusbar_insert: str
    gutter_dim: str             # non-current line numbers
    gutter_current: str         # current line, NORMAL mode
    gutter_insert: str          # current line, INSERT mode


DEFAULT = Theme(
    hl_colors=(
        term.normal,        # HL_NORMAL
        term.bright_black,  # HL_COMMENT
        term.yellow,        # HL_KEYWORD
        term.green,         # HL_STRING
        term.cyan,          # HL_NUMBER
        term.bright_blue,   # HL_FUNCTION
        term.magenta,       # HL_TYPE
    ),
    statusbar_normal=term.reverse,
    statusbar_insert=term.on_green,
    gutter_dim=term.bright_black,
    gutter_current=term.normal,
    gutter_insert=term.green,
)

TOKYO_NIGHT = Theme(
    hl_colors=(
        _rgb_fg(192, 202, 245),  # HL_NORMAL   #c0caf5
        _rgb_fg(86, 95, 137),    # HL_COMMENT  #565f89
        _rgb_fg(187, 154, 247),  # HL_KEYWORD  #bb9af7
        _rgb_fg(158, 206, 106),  # HL_STRING   #9ece6a
        _rgb_fg(255, 158, 100),  # HL_NUMBER   #ff9e64
        _rgb_fg(122, 162, 247),  # HL_FUNCTION #7aa2f7
        _rgb_fg(42, 195, 222),   # HL_TYPE     #2ac3de
    ),
    statusbar_normal=_rgb_bg(59, 66, 97) + _rgb_fg(192, 202, 245),    # bg #3b4261 fg #c0caf5
    statusbar_insert=_rgb_bg(158, 206, 106) + _rgb_fg(26, 27, 38),    # bg #9ece6a fg #1a1b26
    gutter_dim=_rgb_fg(86, 95, 137),      # #565f89
    gutter_current=_rgb_fg(192, 202, 245),  # #c0caf5
    gutter_insert=_rgb_fg(158, 206, 106),   # #9ece6a
)

THEMES: dict[str, Theme] = {
    "default": DEFAULT,
    "tokyo_night": TOKYO_NIGHT,
    "tokyo-night": TOKYO_NIGHT,
}


def get_theme(name: str) -> Theme:
    return THEMES.get(name, DEFAULT)

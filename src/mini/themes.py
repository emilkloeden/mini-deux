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
    statusbar_insert=term.on_green + term.black,
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

NORD = Theme(
    hl_colors=(
        _rgb_fg(216, 222, 233),  # HL_NORMAL   #d8dee9
        _rgb_fg(76, 86, 106),    # HL_COMMENT  #4c566a
        _rgb_fg(129, 161, 193),  # HL_KEYWORD  #81a1c1
        _rgb_fg(163, 190, 140),  # HL_STRING   #a3be8c
        _rgb_fg(180, 142, 173),  # HL_NUMBER   #b48ead
        _rgb_fg(136, 192, 208),  # HL_FUNCTION #88c0d0
        _rgb_fg(143, 188, 187),  # HL_TYPE     #8fbcbb
    ),
    statusbar_normal=_rgb_bg(59, 66, 82) + _rgb_fg(216, 222, 233),   # bg #3b4252 fg #d8dee9
    statusbar_insert=_rgb_bg(163, 190, 140) + _rgb_fg(46, 52, 64),   # bg #a3be8c fg #2e3440
    gutter_dim=_rgb_fg(76, 86, 106),
    gutter_current=_rgb_fg(216, 222, 233),
    gutter_insert=_rgb_fg(163, 190, 140),
)

CATPPUCCIN = Theme(
    hl_colors=(
        _rgb_fg(205, 214, 244),  # HL_NORMAL   #cdd6f4
        _rgb_fg(108, 112, 134),  # HL_COMMENT  #6c7086
        _rgb_fg(203, 166, 247),  # HL_KEYWORD  #cba6f7
        _rgb_fg(166, 227, 161),  # HL_STRING   #a6e3a1
        _rgb_fg(250, 179, 135),  # HL_NUMBER   #fab387
        _rgb_fg(137, 180, 250),  # HL_FUNCTION #89b4fa
        _rgb_fg(137, 220, 235),  # HL_TYPE     #89dceb
    ),
    statusbar_normal=_rgb_bg(49, 50, 68) + _rgb_fg(205, 214, 244),   # bg #313244 fg #cdd6f4
    statusbar_insert=_rgb_bg(166, 227, 161) + _rgb_fg(30, 30, 46),   # bg #a6e3a1 fg #1e1e2e
    gutter_dim=_rgb_fg(108, 112, 134),
    gutter_current=_rgb_fg(205, 214, 244),
    gutter_insert=_rgb_fg(166, 227, 161),
)

DRACULA = Theme(
    hl_colors=(
        _rgb_fg(248, 248, 242),  # HL_NORMAL   #f8f8f2
        _rgb_fg(98, 114, 164),   # HL_COMMENT  #6272a4
        _rgb_fg(255, 121, 198),  # HL_KEYWORD  #ff79c6
        _rgb_fg(241, 250, 140),  # HL_STRING   #f1fa8c
        _rgb_fg(189, 147, 249),  # HL_NUMBER   #bd93f9
        _rgb_fg(80, 250, 123),   # HL_FUNCTION #50fa7b
        _rgb_fg(139, 233, 253),  # HL_TYPE     #8be9fd
    ),
    statusbar_normal=_rgb_bg(68, 71, 90) + _rgb_fg(248, 248, 242),   # bg #44475a fg #f8f8f2
    statusbar_insert=_rgb_bg(80, 250, 123) + _rgb_fg(40, 42, 54),    # bg #50fa7b fg #282a36
    gutter_dim=_rgb_fg(98, 114, 164),
    gutter_current=_rgb_fg(248, 248, 242),
    gutter_insert=_rgb_fg(80, 250, 123),
)

GRUVBOX = Theme(
    hl_colors=(
        _rgb_fg(235, 219, 178),  # HL_NORMAL   #ebdbb2
        _rgb_fg(146, 131, 116),  # HL_COMMENT  #928374
        _rgb_fg(251, 73, 52),    # HL_KEYWORD  #fb4934
        _rgb_fg(184, 187, 38),   # HL_STRING   #b8bb26
        _rgb_fg(211, 134, 155),  # HL_NUMBER   #d3869b
        _rgb_fg(131, 165, 152),  # HL_FUNCTION #83a598
        _rgb_fg(250, 189, 47),   # HL_TYPE     #fabd2f
    ),
    statusbar_normal=_rgb_bg(60, 56, 54) + _rgb_fg(235, 219, 178),   # bg #3c3836 fg #ebdbb2
    statusbar_insert=_rgb_bg(184, 187, 38) + _rgb_fg(40, 40, 40),    # bg #b8bb26 fg #282828
    gutter_dim=_rgb_fg(146, 131, 116),
    gutter_current=_rgb_fg(235, 219, 178),
    gutter_insert=_rgb_fg(184, 187, 38),
)

SOLARIZED_DARK = Theme(
    hl_colors=(
        _rgb_fg(131, 148, 150),  # HL_NORMAL   #839496
        _rgb_fg(88, 110, 117),   # HL_COMMENT  #586e75
        _rgb_fg(133, 153, 0),    # HL_KEYWORD  #859900
        _rgb_fg(42, 161, 152),   # HL_STRING   #2aa198
        _rgb_fg(211, 54, 130),   # HL_NUMBER   #d33682
        _rgb_fg(38, 139, 210),   # HL_FUNCTION #268bd2
        _rgb_fg(108, 113, 196),  # HL_TYPE     #6c71c4
    ),
    statusbar_normal=_rgb_bg(7, 54, 66) + _rgb_fg(131, 148, 150),    # bg #073642 fg #839496
    statusbar_insert=_rgb_bg(133, 153, 0) + _rgb_fg(0, 43, 54),      # bg #859900 fg #002b36
    gutter_dim=_rgb_fg(88, 110, 117),
    gutter_current=_rgb_fg(147, 161, 161),   # #93a1a1
    gutter_insert=_rgb_fg(133, 153, 0),
)

ONE_DARK = Theme(
    hl_colors=(
        _rgb_fg(171, 178, 191),  # HL_NORMAL   #abb2bf
        _rgb_fg(92, 99, 112),    # HL_COMMENT  #5c6370
        _rgb_fg(198, 120, 221),  # HL_KEYWORD  #c678dd
        _rgb_fg(152, 195, 121),  # HL_STRING   #98c379
        _rgb_fg(209, 154, 102),  # HL_NUMBER   #d19a66
        _rgb_fg(97, 175, 239),   # HL_FUNCTION #61afef
        _rgb_fg(229, 192, 123),  # HL_TYPE     #e5c07b
    ),
    statusbar_normal=_rgb_bg(62, 68, 82) + _rgb_fg(171, 178, 191),   # bg #3e4452 fg #abb2bf
    statusbar_insert=_rgb_bg(152, 195, 121) + _rgb_fg(40, 44, 52),   # bg #98c379 fg #282c34
    gutter_dim=_rgb_fg(92, 99, 112),
    gutter_current=_rgb_fg(171, 178, 191),
    gutter_insert=_rgb_fg(152, 195, 121),
)

MONOKAI = Theme(
    hl_colors=(
        _rgb_fg(248, 248, 242),  # HL_NORMAL   #f8f8f2
        _rgb_fg(117, 113, 94),   # HL_COMMENT  #75715e
        _rgb_fg(249, 38, 114),   # HL_KEYWORD  #f92672
        _rgb_fg(230, 219, 116),  # HL_STRING   #e6db74
        _rgb_fg(174, 129, 255),  # HL_NUMBER   #ae81ff
        _rgb_fg(166, 226, 46),   # HL_FUNCTION #a6e22e
        _rgb_fg(102, 217, 232),  # HL_TYPE     #66d9e8
    ),
    statusbar_normal=_rgb_bg(62, 61, 50) + _rgb_fg(248, 248, 242),   # bg #3e3d32 fg #f8f8f2
    statusbar_insert=_rgb_bg(166, 226, 46) + _rgb_fg(39, 40, 34),    # bg #a6e22e fg #272822
    gutter_dim=_rgb_fg(117, 113, 94),
    gutter_current=_rgb_fg(248, 248, 242),
    gutter_insert=_rgb_fg(166, 226, 46),
)

ROSE_PINE = Theme(
    hl_colors=(
        _rgb_fg(224, 222, 244),  # HL_NORMAL   #e0def4
        _rgb_fg(110, 106, 134),  # HL_COMMENT  #6e6a86
        _rgb_fg(196, 167, 231),  # HL_KEYWORD  #c4a7e7
        _rgb_fg(246, 193, 119),  # HL_STRING   #f6c177
        _rgb_fg(235, 188, 186),  # HL_NUMBER   #ebbcba
        _rgb_fg(156, 207, 216),  # HL_FUNCTION #9ccfd8
        _rgb_fg(49, 116, 143),   # HL_TYPE     #31748f
    ),
    statusbar_normal=_rgb_bg(38, 35, 58) + _rgb_fg(224, 222, 244),   # bg #26233a fg #e0def4
    statusbar_insert=_rgb_bg(156, 207, 216) + _rgb_fg(25, 23, 36),   # bg #9ccfd8 fg #191724
    gutter_dim=_rgb_fg(110, 106, 134),
    gutter_current=_rgb_fg(224, 222, 244),
    gutter_insert=_rgb_fg(156, 207, 216),
)

THEMES: dict[str, Theme] = {
    "default": DEFAULT,
    "tokyo_night": TOKYO_NIGHT,
    "tokyo-night": TOKYO_NIGHT,
    "nord": NORD,
    "catppuccin": CATPPUCCIN,
    "catppuccin_mocha": CATPPUCCIN,
    "dracula": DRACULA,
    "gruvbox": GRUVBOX,
    "gruvbox_dark": GRUVBOX,
    "solarized_dark": SOLARIZED_DARK,
    "solarized-dark": SOLARIZED_DARK,
    "one_dark": ONE_DARK,
    "one-dark": ONE_DARK,
    "monokai": MONOKAI,
    "rose_pine": ROSE_PINE,
    "rose-pine": ROSE_PINE,
}


# Ordered list for Ctrl+0..9 key bindings (index = digit)
THEME_LIST = [
    "default",
    "tokyo_night",
    "nord",
    "catppuccin",
    "dracula",
    "gruvbox",
    "solarized_dark",
    "one_dark",
    "monokai",
    "rose_pine",
]


def get_theme(name: str) -> Theme:
    return THEMES.get(name, DEFAULT)

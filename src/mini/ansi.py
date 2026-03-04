from mini.terminal import term

HIDE_CURSOR      = term.hide_cursor
SHOW_CURSOR      = term.normal_cursor
CLEAR_SCREEN     = term.clear
RESET_CURSOR_POS = term.home
INVERT_COLORS    = term.reverse
RESET_FORMATTING = term.normal
CLEAR_EOL        = term.clear_eol
RESET_FG_COLOR   = term.normal
GUTTER_COLOR     = term.bright_black

ESC_BYTE = 0x1B


def set_cursor_pos(x: int, y: int) -> str:
    # blessed.move is 0-indexed (row, col); callers pass 1-indexed (x, y)
    return term.move(y - 1, x - 1)


def iscntrl(byte: int) -> bool:
    return byte < 32 or byte == 127

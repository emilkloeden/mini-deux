import atexit
import os
import sys
import termios

from mini.config import QUIT_TIMES
from mini.constants import STDIN_FILENO
from mini.editor import (
    editor_process_keypress,
    editor_refresh_screen,
    editor_open,
    editor_set_status_message,
)
from mini.types import EditorConfig, Mode
from mini.terminal import disable_raw_mode, enable_raw_mode


def init_editor():
    cols, rows = os.get_terminal_size()
    return EditorConfig(
        orig_termios=termios.tcgetattr(STDIN_FILENO),
        screen_rows=rows - 2,
        screen_cols=cols,
        cx=0,
        cy=0,
        rx=0,
        row_offset=0,
        col_offset=0,
        num_rows=0,
        rows=[],
        file_name="",
        status_msg="",
        status_msg_time=0,
        dirty=0,
        quit_times=QUIT_TIMES,
        mode=Mode.NORMAL,
        count_buf="",
        pending_op="",
    )


def main():
    E = init_editor()
    E = enable_raw_mode(E)
    atexit.register(disable_raw_mode, E)

    if len(sys.argv) >= 2:
        editor_open(E, sys.argv[1])

    editor_set_status_message(E, "HELP: Ctrl-S = save | Ctrl-Q = quit | Ctrl-F = find")
    while True:
        editor_refresh_screen(E)
        editor_process_keypress(E)


if __name__ == "__main__":
    SystemExit(main())

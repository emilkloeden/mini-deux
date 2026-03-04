import argparse
import atexit

from mini.config import QUIT_TIMES
from mini.editor import (
    editor_process_keypress,
    editor_refresh_screen,
    editor_open,
    editor_set_status_message,
)
from mini.types import EditorConfig, Mode
from mini.terminal import disable_raw_mode, enable_raw_mode, term


def init_editor(theme_name: str = "default") -> EditorConfig:
    return EditorConfig(
        orig_termios=[],
        screen_rows=term.height - 2,
        screen_cols=term.width,
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
        theme_name=theme_name,
    )


def main():
    parser = argparse.ArgumentParser(prog="mini")
    parser.add_argument("filename", nargs="?", default="")
    parser.add_argument(
        "--theme",
        default="default",
        choices=["default", "tokyo_night", "tokyo-night"],
    )
    args = parser.parse_args()

    E = init_editor(theme_name=args.theme)
    E = enable_raw_mode(E)
    atexit.register(disable_raw_mode, E)

    if args.filename:
        editor_open(E, args.filename)

    editor_set_status_message(E, "HELP: Ctrl-S = save | Ctrl-Q = quit | Ctrl-F = find")
    while True:
        editor_refresh_screen(E)
        editor_process_keypress(E)


if __name__ == "__main__":
    SystemExit(main())

from mini.editor import editor_update_row
from mini.types import EditorConfig, EditorRow
from mini.config import QUIT_TIMES


def make_row(chars: str) -> EditorRow:
    row = EditorRow(size=len(chars), chars=chars, render="", render_size=0)
    editor_update_row(row)
    return row


def make_editor(
    lines=(),
    cx: int = 0,
    cy: int = 0,
    screen_rows: int = 24,
    screen_cols: int = 80,
) -> EditorConfig:
    rows = [make_row(ln) for ln in lines]
    return EditorConfig(
        orig_termios=[],
        screen_rows=screen_rows,
        screen_cols=screen_cols,
        cx=cx,
        cy=cy,
        rx=0,
        row_offset=0,
        col_offset=0,
        num_rows=len(rows),
        rows=rows,
        file_name="",
        status_msg="",
        status_msg_time=0,
        dirty=0,
        quit_times=QUIT_TIMES,
    )

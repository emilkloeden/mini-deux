from dataclasses import dataclass, field
from enum import Enum
from typing import Any

Termios = list[Any]
Snapshot = tuple[list[str], int, int]   # (row chars list, cx, cy)


class Mode(Enum):
    NORMAL = "NORMAL"
    INSERT = "INSERT"


@dataclass
class EditorRow:
    size: int
    chars: str
    render_size: int
    render: str
    hl: list[int] = field(default_factory=list)


@dataclass
class EditorConfig:
    orig_termios: Termios
    screen_rows: int
    screen_cols: int
    cx: int
    cy: int
    rx: int
    row_offset: int
    col_offset: int
    num_rows: int
    rows: list[EditorRow]
    file_name: str
    status_msg: str
    status_msg_time: int
    dirty: int
    quit_times: int
    mode: Mode = field(default_factory=lambda: Mode.NORMAL)
    count_buf: str = ""
    pending_op: str = ""
    undo_stack: list[Snapshot] = field(default_factory=list)
    redo_stack: list[Snapshot] = field(default_factory=list)
    theme_name: str = "default"

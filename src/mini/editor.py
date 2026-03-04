import sys
import logging
import time
from typing import Callable

from mini.keyboard import EditorKey
from mini.ansi import (
    CLEAR_EOL,
    GUTTER_COLOR,
    HIDE_CURSOR,
    INVERT_COLORS,
    RESET_CURSOR_POS,
    RESET_FG_COLOR,
    RESET_FORMATTING,
    SHOW_CURSOR,
    set_cursor_pos,
)
from mini.append_buffer import AppendBuffer
from mini.config import EDITOR_NAME, EDITOR_VERSION, QUIT_TIMES, TAB_STOP
from mini.highlight import HL_COLORS, update_syntax
from mini.ansi import iscntrl
from mini.terminal import editor_read_key, reset_screen, die
from mini.types import EditorConfig, EditorRow, Mode, Snapshot


logging.basicConfig(filename="app.log", level=logging.DEBUG)


def editor_row_cx_to_rx(row: EditorRow, cx: int) -> int:
    rx = 0
    for j in range(cx):
        if row.chars[j] == "\t":
            rx += (TAB_STOP - 1) - (rx % TAB_STOP)
        rx += 1
    return rx


def editor_row_rx_to_cx(row: EditorRow, rx: int) -> int:
    cur_rx = 0
    for cx in range(row.size):
        if row.chars[cx] == "\t":
            cur_rx += (TAB_STOP - 1) - (cur_rx % TAB_STOP)
        cur_rx += 1
        if cur_rx > rx:
            return cx
    return row.size


def editor_refresh_screen(E: EditorConfig):
    update_syntax(E)
    editor_scroll(E)

    ab = AppendBuffer()
    ab.append(HIDE_CURSOR)
    ab.append(RESET_CURSOR_POS)
    if E.rows:
        logging.debug(f"refresh_screen:{E.rows[0].chars=}")
        logging.debug(E.num_rows)

    editor_draw_rows(E, ab)
    editor_draw_status_bar(E, ab)
    editor_draw_message_bar(E, ab)

    ab.append(set_cursor_pos(x=(E.rx - E.col_offset) + _gutter_width(E) + 1, y=(E.cy - E.row_offset) + 1))
    ab.append(SHOW_CURSOR)
    ab.flush()


def editor_process_keypress(E: EditorConfig):
    key = editor_read_key()
    if E.mode == Mode.NORMAL:
        _normal_key(E, key)
    else:
        _insert_key(E, key)


def _insert_key(E: EditorConfig, key: int):
    match key:
        case EditorKey.ESCAPE:
            E.mode = Mode.NORMAL
            E.count_buf = ""
            E.pending_op = ""
        case _ if key == ctrl_key("h"):
            editor_del_char(E)
        case _ if key == ctrl_key("l"):
            pass
        case _ if key == ctrl_key("s"):
            editor_save(E)
        case _ if key == ctrl_key("q"):
            if E.dirty and E.quit_times > 0:
                editor_set_status_message(
                    E,
                    f"WARNING!!! File has unsaved changes. Press Ctrl-Q {E.quit_times} more times to quit.",
                )
                E.quit_times -= 1
                return
            reset_screen()
            sys.exit(0)
        case EditorKey.CARRIAGE_RETURN:
            editor_insert_newline(E)
        case EditorKey.HOME_KEY:
            E.cx = 0
        case EditorKey.END_KEY:
            if E.cy < E.num_rows:
                E.cx = E.rows[E.cy].size
        case _ if key == ctrl_key("f"):
            editor_find(E)
        case EditorKey.BACKSPACE | EditorKey.DEL_KEY:
            if key == EditorKey.DEL_KEY:
                editor_move_cursor(E, EditorKey.ARROW_RIGHT)
            editor_del_char(E)
        case EditorKey.PAGE_UP | EditorKey.PAGE_DOWN:
            if key == EditorKey.PAGE_UP:
                E.cy = E.row_offset
            elif key == EditorKey.PAGE_DOWN:
                E.cy = E.row_offset + E.screen_rows - 1
                if E.cy > E.num_rows:
                    E.cy = E.num_rows
            times = E.screen_rows
            while times > 0:
                editor_move_cursor(
                    E,
                    EditorKey.ARROW_UP
                    if key == EditorKey.PAGE_UP
                    else EditorKey.ARROW_DOWN,
                )
                times -= 1
        case (
            EditorKey.ARROW_UP
            | EditorKey.ARROW_DOWN
            | EditorKey.ARROW_LEFT
            | EditorKey.ARROW_RIGHT
        ):
            editor_move_cursor(E, key)
        case _:
            logging.debug(f"Default case insert char {key:d}")
            editor_insert_char(E, key)
    E.quit_times = QUIT_TIMES


def _apply_delete_motion(
    E: EditorConfig, from_cx: int, from_cy: int, to_cx: int, to_cy: int
) -> None:
    """Delete text from (from_cy, from_cx) up to (to_cy, to_cx), then place cursor at from."""
    if (from_cy, from_cx) > (to_cy, to_cx):
        from_cx, to_cx = to_cx, from_cx
        from_cy, to_cy = to_cy, from_cy
    if from_cy == to_cy:
        if from_cx == to_cx:
            return
        row = E.rows[from_cy]
        row.chars = row.chars[:from_cx] + row.chars[to_cx:]
        row.size = len(row.chars)
        editor_update_row(row)
        E.dirty += 1
    else:
        start_row = E.rows[from_cy]
        end_row = E.rows[to_cy]
        new_chars = start_row.chars[:from_cx] + end_row.chars[to_cx:]
        start_row.chars = new_chars
        start_row.size = len(new_chars)
        editor_update_row(start_row)
        E.dirty += 1
        for _ in range(to_cy - from_cy):
            editor_del_row(E, from_cy + 1)
    E.cy = min(from_cy, E.num_rows - 1) if E.num_rows > 0 else 0
    E.cx = from_cx
    if E.cy < E.num_rows:
        E.cx = min(E.cx, E.rows[E.cy].size)


def _delete_lines(E: EditorConfig, start_line: int, end_line: int) -> None:
    """Delete lines [start_line, end_line] inclusive (line-wise)."""
    start_line = max(0, start_line)
    end_line = min(end_line, E.num_rows - 1)
    for _ in range(end_line - start_line + 1):
        editor_del_row(E, start_line)
    E.cy = min(start_line, E.num_rows - 1) if E.num_rows > 0 else 0
    E.cx = 0


def _snapshot(E: EditorConfig) -> Snapshot:
    return ([row.chars for row in E.rows], E.cx, E.cy)


MAX_UNDO = 100


def _push_undo(E: EditorConfig) -> None:
    E.undo_stack.append(_snapshot(E))
    if len(E.undo_stack) > MAX_UNDO:
        E.undo_stack.pop(0)
    E.redo_stack.clear()


def _restore_snapshot(E: EditorConfig, snap: Snapshot) -> None:
    rows_chars, cx, cy = snap
    E.rows = []
    E.num_rows = 0
    for chars in rows_chars:
        row = EditorRow(chars=chars, size=len(chars), render="", render_size=0)
        editor_update_row(row)
        E.rows.append(row)
        E.num_rows += 1
    E.dirty = 1
    E.cy = min(cy, E.num_rows - 1) if E.num_rows > 0 else 0
    E.cx = min(cx, E.rows[E.cy].size) if E.num_rows > 0 else 0


def editor_undo(E: EditorConfig) -> None:
    if not E.undo_stack:
        editor_set_status_message(E, "Already at oldest change")
        return
    E.redo_stack.append(_snapshot(E))
    _restore_snapshot(E, E.undo_stack.pop())


def editor_redo(E: EditorConfig) -> None:
    if not E.redo_stack:
        editor_set_status_message(E, "Already at newest change")
        return
    E.undo_stack.append(_snapshot(E))
    _restore_snapshot(E, E.redo_stack.pop())


def _normal_key(E: EditorConfig, key: int):
    # Count accumulation: digits 1-9, or 0 when count already started
    if ord("1") <= key <= ord("9") or (key == ord("0") and E.count_buf):
        E.count_buf += chr(key)
        return

    count = int(E.count_buf) if E.count_buf else 1
    row = E.rows[E.cy] if E.cy < E.num_rows else None

    match key:
        case _ if key == ord("h") or key == EditorKey.ARROW_LEFT:
            old_cx, old_cy = E.cx, E.cy
            for _ in range(count):
                editor_move_cursor(E, EditorKey.ARROW_LEFT)
            if E.pending_op == "d":
                _push_undo(E)
                _apply_delete_motion(E, old_cx, old_cy, E.cx, E.cy)
        case _ if key == ord("l") or key == EditorKey.ARROW_RIGHT:
            old_cx, old_cy = E.cx, E.cy
            for _ in range(count):
                editor_move_cursor(E, EditorKey.ARROW_RIGHT)
            if E.pending_op == "d":
                _push_undo(E)
                _apply_delete_motion(E, old_cx, old_cy, E.cx, E.cy)
        case _ if key == ord("k") or key == EditorKey.ARROW_UP:
            if E.pending_op == "d":
                _push_undo(E)
                _delete_lines(E, E.cy - count, E.cy)
            else:
                for _ in range(count):
                    editor_move_cursor(E, EditorKey.ARROW_UP)
        case _ if key == ord("j") or key == EditorKey.ARROW_DOWN:
            if E.pending_op == "d":
                _push_undo(E)
                _delete_lines(E, E.cy, E.cy + count)
            else:
                for _ in range(count):
                    editor_move_cursor(E, EditorKey.ARROW_DOWN)
        case _ if key == ord("0"):
            old_cx, old_cy = E.cx, E.cy
            E.cx = 0
            if E.pending_op == "d":
                _push_undo(E)
                _apply_delete_motion(E, old_cx, old_cy, E.cx, E.cy)
        case _ if key == ord("$") or key == EditorKey.END_KEY:
            old_cx, old_cy = E.cx, E.cy
            if row:
                E.cx = row.size
            if E.pending_op == "d":
                _push_undo(E)
                _apply_delete_motion(E, old_cx, old_cy, E.cx, E.cy)
        case EditorKey.HOME_KEY:
            old_cx, old_cy = E.cx, E.cy
            E.cx = 0
            if E.pending_op == "d":
                _push_undo(E)
                _apply_delete_motion(E, old_cx, old_cy, E.cx, E.cy)
        case _ if key == ord("G"):
            if E.pending_op == "d":
                target = max(0, min(count - 1, E.num_rows - 1)) if E.count_buf else max(0, E.num_rows - 1)
                _push_undo(E)
                _delete_lines(E, min(E.cy, target), max(E.cy, target))
            else:
                if E.count_buf:
                    E.cy = max(0, min(count - 1, E.num_rows - 1))
                else:
                    E.cy = max(0, E.num_rows - 1)
                E.cx = 0
        case _ if key == ord("g"):
            if E.pending_op == "g":
                E.cy = 0
                E.cx = 0
                E.pending_op = ""
                E.count_buf = ""
                return
            elif E.pending_op == "d":
                # first g of dgg — wait for second g
                E.pending_op = "dg"
                return
            elif E.pending_op == "dg":
                # second g: dgg — delete to top of file
                _push_undo(E)
                _delete_lines(E, 0, E.cy)
            else:
                E.pending_op = "g"
                return
        case _ if key == ord("w"):
            old_cx, old_cy = E.cx, E.cy
            for _ in range(count):
                editor_move_word_forward(E)
            if E.pending_op == "d":
                _push_undo(E)
                _apply_delete_motion(E, old_cx, old_cy, E.cx, E.cy)
        case _ if key == ord("b"):
            old_cx, old_cy = E.cx, E.cy
            for _ in range(count):
                editor_move_word_backward(E)
            if E.pending_op == "d":
                _push_undo(E)
                _apply_delete_motion(E, old_cx, old_cy, E.cx, E.cy)
        case _ if key == ord("e"):
            old_cx, old_cy = E.cx, E.cy
            for _ in range(count):
                editor_move_word_end(E)
            if E.pending_op == "d":
                # e is inclusive of the end character
                _push_undo(E)
                _apply_delete_motion(E, old_cx, old_cy, E.cx + 1, E.cy)
        case _ if key == ord("x"):
            if row:
                _push_undo(E)
                for _ in range(count):
                    cur_row = E.rows[E.cy] if E.cy < E.num_rows else None
                    if cur_row and E.cx < cur_row.size:
                        editor_row_del_char(E, cur_row, E.cx)
                        if E.cx >= cur_row.size and cur_row.size > 0:
                            E.cx = cur_row.size - 1
        case _ if key == ord("d"):
            if E.pending_op == "d":
                _push_undo(E)
                for _ in range(count):
                    editor_del_row(E, E.cy)
                if E.cy >= E.num_rows and E.cy > 0:
                    E.cy = E.num_rows - 1
                E.cx = 0
                E.pending_op = ""
                E.count_buf = ""
                return
            else:
                E.pending_op = "d"
                return
        case _ if key == ord("i"):
            _push_undo(E)
            E.mode = Mode.INSERT
        case _ if key == ord("a"):
            _push_undo(E)
            if row:
                E.cx = min(E.cx + 1, row.size)
            E.mode = Mode.INSERT
        case _ if key == ord("A"):
            _push_undo(E)
            if row:
                E.cx = row.size
            E.mode = Mode.INSERT
        case _ if key == ord("o"):
            _push_undo(E)
            editor_insert_row(E, E.cy + 1, "")
            E.cy += 1
            E.cx = 0
            E.mode = Mode.INSERT
        case _ if key == ord("O"):
            _push_undo(E)
            editor_insert_row(E, E.cy, "")
            E.cx = 0
            E.mode = Mode.INSERT
        case EditorKey.ESCAPE:
            E.pending_op = ""
            E.count_buf = ""
            return
        case _ if key == ctrl_key("q"):
            if E.dirty and E.quit_times > 0:
                editor_set_status_message(
                    E,
                    f"WARNING!!! File has unsaved changes. Press Ctrl-Q {E.quit_times} more times to quit.",
                )
                E.quit_times -= 1
                return
            reset_screen()
            sys.exit(0)
        case _ if key == ctrl_key("s"):
            editor_save(E)
        case _ if key == ctrl_key("f"):
            editor_find(E)
        case _ if key == ord("u"):
            editor_undo(E)
        case _ if key == ctrl_key("r"):
            editor_redo(E)
        case _:
            pass

    E.count_buf = ""
    E.pending_op = ""
    E.quit_times = QUIT_TIMES


def editor_prompt(
    E: EditorConfig,
    prompt: str,
    callback: Callable[[EditorConfig, str, int], None] | None = None,
) -> str | None:
    buf: list[str] = []
    while True:
        editor_set_status_message(E, prompt, "".join(buf))
        editor_refresh_screen(E)
        key = editor_read_key()
        if (
            key == EditorKey.DEL_KEY
            or key == ctrl_key("h")
            or key == EditorKey.BACKSPACE
        ):
            if buf:
                buf.pop()
        if key == EditorKey.CARRIAGE_RETURN:
            if buf:
                editor_set_status_message(E, "")
                buf_str = "".join(buf)
                if callback:
                    callback(E, buf_str, key)
                return buf_str
        elif key == EditorKey.ESCAPE:
            editor_set_status_message(E, "")
            if callback:
                callback(E, "".join(buf), key)
            return None
        elif not iscntrl(key) and key < 128:
            buf.append(chr(key))
        if callback:
            callback(E, "".join(buf), key)


def editor_insert_char(E: EditorConfig, key: int):
    if E.cy == E.num_rows:
        editor_insert_row(E, E.num_rows, "")
    editor_row_insert_char(E, E.cy, E.cx, key)
    E.cx += 1


def editor_insert_newline(E: EditorConfig) -> None:
    if E.cx == 0:
        editor_insert_row(E, E.cy, "")
    else:
        row = E.rows[E.cy]
        editor_insert_row(E, E.cy + 1, row.chars[E.cx:])
        row = E.rows[E.cy]
        row.chars = row.chars[:E.cx]
        row.size = E.cx
        editor_update_row(row)
    E.cy += 1
    E.cx = 0


def editor_del_char(E: EditorConfig):
    if E.cy == E.num_rows:
        return
    if E.cx == 0 and E.cy == 0:
        return

    row = E.rows[E.cy]
    if E.cx > 0:
        editor_row_del_char(E, row, E.cx - 1)
        E.cx -= 1
    else:
        E.cx = E.rows[E.cy - 1].size
        editor_row_append_string(E, E.rows[E.cy - 1], row.chars)
        editor_del_row(E, E.cy)
        E.cy -= 1


def editor_row_insert_char(E: EditorConfig, row_num: int, col_num: int, key: int):
    row = E.rows[row_num]
    at = row.size if col_num < 0 or col_num > row.size else col_num
    chars_before = row.chars[:at]
    chars_after = row.chars[at:]
    row.chars = chars_before + chr(key) + chars_after
    row.size += 1
    editor_update_row(row)
    E.dirty += 1


def editor_row_append_string(E: EditorConfig, row: EditorRow, s: str) -> None:
    row.chars = row.chars + s
    row.size += len(s)
    editor_update_row(row)
    E.dirty += 1


def editor_row_del_char(E: EditorConfig, row: EditorRow, col_num: int) -> None:
    if col_num < 0 or col_num >= row.size:
        return
    chars_before = row.chars[:col_num]
    chars_after = row.chars[col_num + 1:]
    row.chars = chars_before + chars_after
    row.size -= 1
    editor_update_row(row)
    E.dirty += 1


def ctrl_key(k: str | int):
    return ord(str(k)) & 0x1F


def editor_update_row(row: EditorRow):
    row.render = ""
    tabs = 0
    for j in range(row.size):
        if row.chars[j] == tabs:
            tabs += 1

    idx = 0

    for j in range(row.size):
        if row.chars[j] == "\t":
            while idx % TAB_STOP != 0:
                row.render += " "
                idx += 1
        else:
            row.render += row.chars[j]
            idx += 1
    row.render_size = idx


def editor_insert_row(E: EditorConfig, at: int, s: str) -> None:
    if at < 0 or at > E.num_rows:
        return
    s = s.strip("\r\n")
    length = len(s)
    row = EditorRow(size=length, chars=s, render="", render_size=0)
    E.rows.insert(at, row)
    editor_update_row(row)
    E.num_rows += 1
    E.dirty += 1


def editor_append_row(E: EditorConfig, s: str):
    line = s.strip("\r\n")
    E.rows.append(EditorRow(chars=line, size=len(line), render="", render_size=0))
    editor_update_row(E.rows[E.num_rows])
    E.num_rows += 1
    E.dirty += 1


def editor_del_row(E: EditorConfig, at: int) -> None:
    if at < 0 or at >= E.num_rows:
        return
    del E.rows[at]
    E.num_rows -= 1
    E.dirty += 1


def _gutter_width(E: EditorConfig) -> int:
    """Digits needed for the largest line number + 1 space separator."""
    return len(str(max(E.num_rows, 1))) + 1


def editor_scroll(E: EditorConfig):
    E.rx = E.cx
    if E.cy < E.num_rows:
        E.rx = editor_row_cx_to_rx(E.rows[E.cy], E.cx)
    if E.cy < E.row_offset:
        E.row_offset = E.cy
    if E.cy >= E.row_offset + E.screen_rows:
        E.row_offset = E.cy - E.screen_rows + 1
    content_cols = E.screen_cols - _gutter_width(E)
    if E.rx < E.col_offset:
        E.col_offset = E.rx
    if E.rx >= E.col_offset + content_cols:
        E.col_offset = E.rx - content_cols + 1


def editor_draw_rows(E: EditorConfig, ab: AppendBuffer):
    gw = _gutter_width(E)
    num_width = gw - 1
    content_cols = E.screen_cols - gw

    for y in range(E.screen_rows):
        file_row = y + E.row_offset
        if file_row >= E.num_rows:
            ab.append(" " * gw)
            if E.num_rows == 0 and y == E.screen_rows // 3:
                welcome = f"{EDITOR_NAME} editor -- version {EDITOR_VERSION}"
                if len(welcome) > content_cols:
                    welcome = welcome[:content_cols]
                padding = (content_cols - len(welcome)) / 2
                if padding:
                    ab.append("~")
                    padding -= 1
                while padding > 0:
                    padding -= 1
                    ab.append(" ")
                ab.append(welcome)
            else:
                ab.append("~")
        else:
            # Gutter: absolute on current line, relative (dim) elsewhere
            if file_row == E.cy:
                ab.append(str(file_row + 1).rjust(num_width) + " ")
            else:
                rel = abs(file_row - E.cy)
                ab.append(GUTTER_COLOR + str(rel).rjust(num_width) + " " + RESET_FORMATTING)

            length = E.rows[file_row].render_size - E.col_offset
            if length < 0:
                length = 0
            if length > content_cols:
                length = content_cols
            row = E.rows[file_row]
            visible = row.render[E.col_offset:E.col_offset + length]
            if file_row == 0:
                logging.debug(
                    f"draw_rows row0: render_size={row.render_size} {length=} {visible=}"
                )
            if row.hl:
                hl_slice = row.hl[E.col_offset:E.col_offset + length]
                current_hl = -1
                for char, hl_type in zip(visible, hl_slice):
                    if hl_type != current_hl:
                        ab.append(HL_COLORS[hl_type])
                        current_hl = hl_type
                    ab.append(char)
                ab.append(RESET_FG_COLOR)
            else:
                ab.append(visible)
        ab.append(CLEAR_EOL)
        ab.append("\r\n")


def editor_draw_status_bar(E: EditorConfig, ab: AppendBuffer):
    ab.append(INVERT_COLORS)
    file_name = E.file_name if E.file_name else "[No Name]"
    mode_str = f"[{E.mode.value}]"
    status = f"{mode_str} {file_name:20s} - {E.num_rows} lines {'(modified)' if E.dirty else ''}"
    status_len = len(status)
    pending = f"{E.count_buf}{E.pending_op}"
    row_status = f"{pending + '  ' if pending else ''}{E.cy + 1}/{E.num_rows}"
    row_status_len = len(row_status)
    if status_len > E.screen_cols:
        status = status[: E.screen_cols]
    ab.append(status)
    padding_right = E.screen_cols - status_len - row_status_len
    if padding_right > 0:
        ab.append(" " * padding_right)
    ab.append(row_status)
    ab.append(RESET_FORMATTING)
    ab.append("\r\n")


def editor_set_status_message(E: EditorConfig, fmt: str, *args: object) -> None:
    E.status_msg = fmt % args if args else fmt
    E.status_msg_time = int(time.time())


def editor_draw_message_bar(E: EditorConfig, ab: AppendBuffer):
    ab.append(CLEAR_EOL)
    msg_len = len(E.status_msg)
    if msg_len > E.screen_cols:
        msg_len = E.screen_cols
    if msg_len and int(time.time()) - E.status_msg_time < 5:
        ab.append(E.status_msg)


def editor_move_word_forward(E: EditorConfig) -> None:
    """w — move to start of next word."""
    if E.num_rows == 0:
        return
    row = E.rows[E.cy]
    cx = E.cx
    # Skip current word characters
    while cx < row.size and not row.chars[cx].isspace():
        cx += 1
    # Skip whitespace to next word
    while cx < row.size and row.chars[cx].isspace():
        cx += 1
    if cx < row.size:
        E.cx = cx
    else:
        # Move to next line
        if E.cy < E.num_rows - 1:
            E.cy += 1
            row = E.rows[E.cy]
            cx = 0
            while cx < row.size and row.chars[cx].isspace():
                cx += 1
            E.cx = cx
        else:
            E.cx = row.size


def editor_move_word_backward(E: EditorConfig) -> None:
    """b — move to start of previous word."""
    if E.num_rows == 0:
        return
    row = E.rows[E.cy]
    cx = E.cx
    if cx == 0:
        if E.cy > 0:
            E.cy -= 1
            row = E.rows[E.cy]
            cx = row.size
        else:
            return
    cx -= 1
    # Skip whitespace backwards
    while cx > 0 and row.chars[cx].isspace():
        cx -= 1
    # Skip word characters backwards
    while cx > 0 and not row.chars[cx - 1].isspace():
        cx -= 1
    E.cx = cx


def editor_move_word_end(E: EditorConfig) -> None:
    """e — move to end of current/next word."""
    if E.num_rows == 0:
        return
    row = E.rows[E.cy]
    cx = E.cx
    # If already at end or on whitespace, skip whitespace first
    if cx + 1 >= row.size or row.chars[cx + 1].isspace():
        cx += 1
        while cx < row.size and row.chars[cx].isspace():
            cx += 1
        if cx >= row.size:
            if E.cy < E.num_rows - 1:
                E.cy += 1
                row = E.rows[E.cy]
                cx = 0
                while cx < row.size and row.chars[cx].isspace():
                    cx += 1
            else:
                E.cx = max(0, row.size - 1)
                return
    # Move to end of word
    while cx + 1 < row.size and not row.chars[cx + 1].isspace():
        cx += 1
    E.cx = min(cx, row.size - 1) if row.size > 0 else 0


def editor_move_cursor(E: EditorConfig, key: int):
    current_row = None if E.cy >= E.num_rows else E.rows[E.cy]

    match key:
        case EditorKey.ARROW_LEFT:
            if E.cx != 0:
                E.cx -= 1
            elif E.cy > 0:
                E.cy -= 1
                E.cx = E.rows[E.cy].size

        case EditorKey.ARROW_RIGHT:
            if current_row and E.cx < current_row.size:
                E.cx += 1
            elif current_row and E.cx == current_row.size:
                E.cy += 1
                E.cx = 0
        case EditorKey.ARROW_UP:
            if E.cy != 0:
                E.cy -= 1
        case EditorKey.ARROW_DOWN:
            if E.cy < E.num_rows - 1:
                E.cy += 1

    # Snap to end of line
    current_row = None if E.cy >= E.num_rows else E.rows[E.cy]
    row_len = current_row.size if current_row else 0
    if E.cx > row_len:
        E.cx = row_len


def editor_open(E: EditorConfig, filename: str) -> None:
    E.file_name = filename
    fp = open(filename)
    if not fp:
        die()

    for line in fp.readlines():
        editor_insert_row(E, E.num_rows, line)
    fp.close()
    E.dirty = 0


def editor_rows_to_string(E: EditorConfig) -> str:
    return "\n".join([row.chars for row in E.rows])


def editor_save(E: EditorConfig) -> None:
    if not E.file_name:
        resp = editor_prompt(E, "Save as: %s (ESC to cancel)")
        if not resp:
            editor_set_status_message(E, "Save aborted")
            return
        E.file_name = resp

    buf = editor_rows_to_string(E)
    try:
        with open(E.file_name, "w") as f:
            f.write(buf)
            E.dirty = 0
            editor_set_status_message(E, f"{len(buf)} bytes written to disk")
    except Exception as e:
        logging.debug(f"Error saving\n{e}")
        editor_set_status_message(E, "Can't save. I/O error.")


def make_editor_find_callback() -> Callable[[EditorConfig, str, int], None]:
    last_match = [-1]
    direction = [1]

    def callback(E: EditorConfig, query: str, key: int) -> None:
        if key in (EditorKey.CARRIAGE_RETURN, EditorKey.ESCAPE):
            last_match[0] = -1
            direction[0] = 1
            return
        elif key in (EditorKey.ARROW_RIGHT, EditorKey.ARROW_DOWN):
            direction[0] = 1
        elif key in (EditorKey.ARROW_LEFT, EditorKey.ARROW_UP):
            direction[0] = -1
        else:
            last_match[0] = -1
            direction[0] = 1

        if last_match[0] == -1:
            direction[0] = 1

        current = last_match[0]
        for _ in range(E.num_rows):
            current += direction[0]
            if current == -1:
                current = E.num_rows - 1
            elif current == E.num_rows:
                current = 0

            row = E.rows[current]
            match = row.render.find(query)
            if match != -1:
                last_match[0] = current
                E.cy = current
                E.cx = editor_row_rx_to_cx(row, match)
                E.row_offset = E.num_rows
                break

    return callback


def editor_find(E: EditorConfig) -> None:
    saved_cx = E.cx
    saved_cy = E.cy
    saved_col_offset = E.col_offset
    saved_row_offset = E.row_offset

    query = editor_prompt(E, "Search: %s (ESC to cancel)", make_editor_find_callback())

    if not query:
        E.cx = saved_cx
        E.cy = saved_cy
        E.col_offset = saved_col_offset
        E.row_offset = saved_row_offset
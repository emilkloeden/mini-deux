from conftest import make_row, make_editor

from mini.editor import (
    _apply_delete_motion,
    _delete_lines,
    _gutter_width,
    _push_undo,
    _restore_snapshot,
    _snapshot,
    ctrl_key,
    editor_del_char,
    editor_del_row,
    editor_insert_char,
    editor_insert_newline,
    editor_insert_row,
    editor_move_cursor,
    editor_move_word_backward,
    editor_move_word_end,
    editor_move_word_forward,
    editor_redo,
    editor_row_append_string,
    editor_row_cx_to_rx,
    editor_row_del_char,
    editor_row_insert_char,
    editor_row_rx_to_cx,
    editor_rows_to_string,
    editor_scroll,
    editor_set_status_message,
    editor_undo,
    editor_update_row,
)
from mini.keyboard import EditorKey
from mini.types import EditorRow


# ---------------------------------------------------------------------------
# Tab / cursor-position conversion
# ---------------------------------------------------------------------------

class TestCxToRx:
    def test_no_tabs(self):
        row = make_row("hello")
        assert editor_row_cx_to_rx(row, 3) == 3

    def test_cx_zero(self):
        row = make_row("hello")
        assert editor_row_cx_to_rx(row, 0) == 0

    def test_tab_at_start(self):
        # tab at col 0: rx jumps by (TAB_STOP-1)-(0%TAB_STOP)+1 = 8
        row = make_row("\tabc")
        assert editor_row_cx_to_rx(row, 1) == 8

    def test_tab_in_middle(self):
        # "a\tb": tab at col 1. After 'a' rx=1, tab → rx += 6 + 1 = 8
        row = make_row("a\tb")
        assert editor_row_cx_to_rx(row, 2) == 8

    def test_tab_at_col_4(self):
        # "abcd\te": tab at col 4. After 4 chars rx=4, tab → rx += 3+1=8
        row = make_row("abcd\te")
        assert editor_row_cx_to_rx(row, 5) == 8

    def test_cx_at_end(self):
        row = make_row("abc")
        assert editor_row_cx_to_rx(row, 3) == 3


class TestRxToCx:
    def test_no_tabs_roundtrip(self):
        row = make_row("hello")
        for cx in range(row.size + 1):
            rx = editor_row_cx_to_rx(row, cx)
            assert editor_row_rx_to_cx(row, rx) == cx

    def test_with_tabs_roundtrip(self):
        row = make_row("a\tb")
        for cx in range(row.size + 1):
            rx = editor_row_cx_to_rx(row, cx)
            assert editor_row_rx_to_cx(row, rx) == cx

    def test_rx_beyond_row_returns_size(self):
        row = make_row("abc")
        assert editor_row_rx_to_cx(row, 100) == row.size


# ---------------------------------------------------------------------------
# editor_update_row
# ---------------------------------------------------------------------------

class TestEditorUpdateRow:
    def test_no_tabs(self):
        row = make_row("hello")
        assert row.render == "hello"
        assert row.render_size == 5

    def test_empty(self):
        row = make_row("")
        assert row.render == ""
        assert row.render_size == 0

    def test_tab_expands_to_tab_stop(self):
        # "a\tb": tab at col 1 expands to fill up to col 8 (7 spaces)
        row = make_row("a\tb")
        assert row.render == "a" + " " * 7 + "b"
        assert row.render_size == 9

    def test_tab_at_col_4(self):
        # "abcd\te": tab at col 4 expands by 4 spaces to reach col 8
        row = make_row("abcd\te")
        assert row.render == "abcd" + " " * 4 + "e"
        assert row.render_size == 9


# ---------------------------------------------------------------------------
# editor_insert_row / editor_del_row
# ---------------------------------------------------------------------------

class TestInsertDelRow:
    def test_insert_at_end(self):
        E = make_editor(["hello"])
        editor_insert_row(E, 1, "world")
        assert E.num_rows == 2
        assert E.rows[1].chars == "world"

    def test_insert_at_start(self):
        E = make_editor(["hello"])
        editor_insert_row(E, 0, "world")
        assert E.num_rows == 2
        assert E.rows[0].chars == "world"
        assert E.rows[1].chars == "hello"

    def test_insert_in_middle(self):
        E = make_editor(["a", "c"])
        editor_insert_row(E, 1, "b")
        assert E.num_rows == 3
        assert E.rows[1].chars == "b"

    def test_insert_strips_newline(self):
        E = make_editor()
        editor_insert_row(E, 0, "hello\n")
        assert E.rows[0].chars == "hello"

    def test_del_removes_correct_row(self):
        E = make_editor(["a", "b", "c"])
        editor_del_row(E, 1)
        assert E.num_rows == 2
        assert E.rows[0].chars == "a"
        assert E.rows[1].chars == "c"

    def test_del_decrements_num_rows(self):
        E = make_editor(["a", "b"])
        editor_del_row(E, 0)
        assert E.num_rows == 1

    def test_del_out_of_range_is_noop(self):
        E = make_editor(["a", "b"])
        editor_del_row(E, 5)
        assert E.num_rows == 2

    def test_del_negative_is_noop(self):
        E = make_editor(["a", "b"])
        editor_del_row(E, -1)
        assert E.num_rows == 2


# ---------------------------------------------------------------------------
# Row character operations
# ---------------------------------------------------------------------------

class TestRowCharOps:
    def test_row_insert_char(self):
        E = make_editor(["helo"])
        editor_row_insert_char(E, 0, 2, ord("l"))
        assert E.rows[0].chars == "hello"
        assert E.rows[0].size == 5

    def test_row_insert_char_at_start(self):
        E = make_editor(["ello"])
        editor_row_insert_char(E, 0, 0, ord("h"))
        assert E.rows[0].chars == "hello"

    def test_row_insert_char_at_end(self):
        E = make_editor(["hell"])
        editor_row_insert_char(E, 0, 4, ord("o"))
        assert E.rows[0].chars == "hello"

    def test_row_del_char(self):
        E = make_editor(["hello"])
        editor_row_del_char(E, E.rows[0], 2)
        assert E.rows[0].chars == "helo"
        assert E.rows[0].size == 4

    def test_row_del_char_out_of_range_is_noop(self):
        E = make_editor(["hello"])
        editor_row_del_char(E, E.rows[0], 10)
        assert E.rows[0].chars == "hello"

    def test_row_del_char_negative_is_noop(self):
        E = make_editor(["hello"])
        editor_row_del_char(E, E.rows[0], -1)
        assert E.rows[0].chars == "hello"

    def test_row_append_string(self):
        E = make_editor(["hello"])
        editor_row_append_string(E, E.rows[0], " world")
        assert E.rows[0].chars == "hello world"
        assert E.rows[0].size == 11

    def test_row_append_string_empty(self):
        E = make_editor(["hello"])
        editor_row_append_string(E, E.rows[0], "")
        assert E.rows[0].chars == "hello"


# ---------------------------------------------------------------------------
# Text editing: insert_char, del_char, insert_newline
# ---------------------------------------------------------------------------

class TestTextEditing:
    def test_insert_char_on_empty_editor(self):
        E = make_editor()
        editor_insert_char(E, ord("a"))
        assert E.num_rows == 1
        assert E.rows[0].chars == "a"
        assert E.cx == 1

    def test_insert_char_creates_row_when_at_end(self):
        E = make_editor(["hello"], cx=5, cy=0)
        # cy == num_rows would be 1; cy=0 < 1 so no new row needed, but let's test at boundary
        E.cy = E.num_rows  # force cy == num_rows
        editor_insert_char(E, ord("x"))
        assert E.num_rows == 2

    def test_insert_char_advances_cx(self):
        E = make_editor(["hello"], cx=5)
        editor_insert_char(E, ord("!"))
        assert E.rows[0].chars == "hello!"
        assert E.cx == 6

    def test_del_char_removes_char_before_cursor(self):
        E = make_editor(["hello"], cx=5)
        editor_del_char(E)
        assert E.rows[0].chars == "hell"
        assert E.cx == 4

    def test_del_char_merges_with_previous_row(self):
        E = make_editor(["hello", "world"], cx=0, cy=1)
        editor_del_char(E)
        assert E.num_rows == 1
        assert E.rows[0].chars == "helloworld"
        assert E.cx == 5
        assert E.cy == 0

    def test_del_char_at_start_of_first_row_is_noop(self):
        E = make_editor(["hello"], cx=0, cy=0)
        editor_del_char(E)
        assert E.rows[0].chars == "hello"

    def test_insert_newline_at_cx_zero(self):
        E = make_editor(["hello"], cx=0, cy=0)
        editor_insert_newline(E)
        assert E.num_rows == 2
        assert E.rows[0].chars == ""
        assert E.rows[1].chars == "hello"
        assert E.cy == 1
        assert E.cx == 0

    def test_insert_newline_splits_row(self):
        E = make_editor(["hello"], cx=3, cy=0)
        editor_insert_newline(E)
        assert E.num_rows == 2
        assert E.rows[0].chars == "hel"
        assert E.rows[1].chars == "lo"
        assert E.cy == 1
        assert E.cx == 0


# ---------------------------------------------------------------------------
# Cursor movement
# ---------------------------------------------------------------------------

class TestCursorMovement:
    def test_left_wraps_to_previous_row(self):
        E = make_editor(["hello", "world"], cx=0, cy=1)
        editor_move_cursor(E, EditorKey.ARROW_LEFT)
        assert E.cy == 0
        assert E.cx == 5  # end of "hello"

    def test_left_at_first_col_first_row_is_noop(self):
        E = make_editor(["hello"], cx=0, cy=0)
        editor_move_cursor(E, EditorKey.ARROW_LEFT)
        assert E.cx == 0
        assert E.cy == 0

    def test_right_wraps_to_next_row(self):
        E = make_editor(["hello", "world"], cx=5, cy=0)
        editor_move_cursor(E, EditorKey.ARROW_RIGHT)
        assert E.cy == 1
        assert E.cx == 0

    def test_up_clamps_at_first_row(self):
        E = make_editor(["hello"], cx=2, cy=0)
        editor_move_cursor(E, EditorKey.ARROW_UP)
        assert E.cy == 0

    def test_down_clamps_at_last_row(self):
        E = make_editor(["hello", "world"], cx=2, cy=1)
        editor_move_cursor(E, EditorKey.ARROW_DOWN)
        assert E.cy == 1

    def test_down_snaps_cx_to_shorter_row(self):
        E = make_editor(["hello", "hi"], cx=5, cy=0)
        editor_move_cursor(E, EditorKey.ARROW_DOWN)
        assert E.cy == 1
        assert E.cx == 2  # snapped to len("hi")


# ---------------------------------------------------------------------------
# Word motions
# ---------------------------------------------------------------------------

class TestWordMotions:
    def test_word_forward_skips_to_next_word(self):
        E = make_editor(["hello world"], cx=0, cy=0)
        editor_move_word_forward(E)
        assert E.cx == 6  # start of "world"

    def test_word_forward_wraps_to_next_line(self):
        E = make_editor(["hello", "world"], cx=0, cy=0)
        editor_move_word_forward(E)
        assert E.cy == 1
        assert E.cx == 0

    def test_word_backward_moves_to_start_of_word(self):
        E = make_editor(["hello world"], cx=6, cy=0)
        editor_move_word_backward(E)
        assert E.cx == 0  # start of "hello"

    def test_word_backward_wraps_to_previous_line(self):
        E = make_editor(["hello", "world"], cx=0, cy=1)
        editor_move_word_backward(E)
        assert E.cy == 0

    def test_word_end_moves_to_last_char_of_word(self):
        E = make_editor(["hello world"], cx=0, cy=0)
        editor_move_word_end(E)
        assert E.cx == 4  # last char of "hello" (0-indexed)

    def test_word_end_from_end_of_word_jumps_to_next(self):
        E = make_editor(["hello world"], cx=4, cy=0)
        editor_move_word_end(E)
        assert E.cx == 10  # last char of "world"


# ---------------------------------------------------------------------------
# Scroll
# ---------------------------------------------------------------------------

class TestScroll:
    def test_scroll_up_when_cy_above_viewport(self):
        E = make_editor(["line"] * 30, cy=0)
        E.row_offset = 5
        editor_scroll(E)
        assert E.row_offset == 0

    def test_scroll_down_when_cy_below_viewport(self):
        E = make_editor(["line"] * 50, cy=25, screen_rows=24)
        editor_scroll(E)
        assert E.row_offset == 25 - 24 + 1  # == 2

    def test_scroll_col_left_when_rx_behind_offset(self):
        E = make_editor(["hello"], cx=0, screen_cols=80)
        E.col_offset = 10
        editor_scroll(E)
        assert E.col_offset == 0

    def test_scroll_col_right_when_rx_beyond_viewport(self):
        # 1 row → gutter_width=2, content_cols=78
        E = make_editor(["a" * 100], cx=85, screen_cols=80)
        editor_scroll(E)
        assert E.col_offset == 85 - 78 + 1  # == 8


# ---------------------------------------------------------------------------
# Undo / redo
# ---------------------------------------------------------------------------

class TestUndoRedo:
    def test_snapshot_captures_state(self):
        E = make_editor(["hello", "world"], cx=3, cy=1)
        snap = _snapshot(E)
        assert snap == (["hello", "world"], 3, 1)

    def test_push_undo_appends_to_stack(self):
        E = make_editor(["hello"])
        _push_undo(E)
        assert len(E.undo_stack) == 1

    def test_push_undo_clears_redo_stack(self):
        E = make_editor(["hello"])
        E.redo_stack.append((["hello"], 0, 0))
        _push_undo(E)
        assert E.redo_stack == []

    def test_restore_snapshot_reconstructs_rows(self):
        E = make_editor(["hello"], cx=5)
        snap = (["world", "foo"], 2, 1)
        _restore_snapshot(E, snap)
        assert E.num_rows == 2
        assert E.rows[0].chars == "world"
        assert E.rows[1].chars == "foo"
        assert E.cx == 2
        assert E.cy == 1
        assert E.dirty == 1

    def test_editor_undo_restores_previous_state(self):
        E = make_editor(["hello"])
        _push_undo(E)  # save state with "hello"
        E.rows[0].chars = "world"
        E.rows[0].size = 5
        editor_update_row(E.rows[0])
        editor_undo(E)
        assert E.rows[0].chars == "hello"

    def test_editor_undo_pushes_to_redo_stack(self):
        E = make_editor(["hello"])
        _push_undo(E)
        editor_undo(E)
        assert len(E.redo_stack) == 1

    def test_editor_undo_on_empty_stack_sets_message(self):
        E = make_editor(["hello"])
        editor_undo(E)
        assert "Already at oldest change" in E.status_msg

    def test_editor_redo_restores_undone_state(self):
        E = make_editor(["hello"])
        _push_undo(E)
        E.rows[0].chars = "world"
        E.rows[0].size = 5
        editor_update_row(E.rows[0])
        editor_undo(E)  # back to "hello"
        editor_redo(E)  # forward to "world"
        assert E.rows[0].chars == "world"

    def test_editor_redo_on_empty_stack_sets_message(self):
        E = make_editor(["hello"])
        editor_redo(E)
        assert "Already at newest change" in E.status_msg


# ---------------------------------------------------------------------------
# Delete motions
# ---------------------------------------------------------------------------

class TestDeleteMotions:
    def test_apply_delete_same_row(self):
        E = make_editor(["hello world"])
        _apply_delete_motion(E, 0, 0, 5, 0)  # delete "hello"
        assert E.rows[0].chars == " world"

    def test_apply_delete_same_row_normalized(self):
        # from_cx > to_cx: should be normalised automatically
        E = make_editor(["hello world"])
        _apply_delete_motion(E, 5, 0, 0, 0)
        assert E.rows[0].chars == " world"

    def test_apply_delete_same_row_same_pos_is_noop(self):
        E = make_editor(["hello"])
        _apply_delete_motion(E, 2, 0, 2, 0)
        assert E.rows[0].chars == "hello"

    def test_apply_delete_multi_row(self):
        E = make_editor(["hello", "world", "foo"])
        # from (cy=0, cx=3) to (cy=1, cx=2): merge "hel" with "rld"
        _apply_delete_motion(E, 3, 0, 2, 1)
        assert E.num_rows == 2
        assert E.rows[0].chars == "helrld"
        assert E.rows[1].chars == "foo"
        assert E.cy == 0
        assert E.cx == 3

    def test_delete_lines_removes_range(self):
        E = make_editor(["a", "b", "c", "d", "e"])
        _delete_lines(E, 1, 2)  # delete "b" and "c"
        assert E.num_rows == 3
        assert [r.chars for r in E.rows] == ["a", "d", "e"]
        assert E.cy == 1

    def test_delete_lines_all_rows(self):
        E = make_editor(["a", "b", "c"])
        _delete_lines(E, 0, 2)
        assert E.num_rows == 0
        assert E.cy == 0

    def test_delete_lines_clamps_out_of_range(self):
        E = make_editor(["a", "b", "c"])
        _delete_lines(E, 1, 10)  # end clamped to 2
        assert E.num_rows == 1
        assert E.rows[0].chars == "a"


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

class TestGutterWidth:
    def test_1_row(self):
        E = make_editor(["a"])
        assert _gutter_width(E) == 2  # len("1") + 1

    def test_9_rows(self):
        E = make_editor(["x"] * 9)
        assert _gutter_width(E) == 2

    def test_10_rows(self):
        E = make_editor(["x"] * 10)
        assert _gutter_width(E) == 3  # len("10") + 1

    def test_99_rows(self):
        E = make_editor(["x"] * 99)
        assert _gutter_width(E) == 3

    def test_100_rows(self):
        E = make_editor(["x"] * 100)
        assert _gutter_width(E) == 4  # len("100") + 1


class TestCtrlKey:
    def test_ctrl_q(self):
        assert ctrl_key("q") == 17

    def test_ctrl_s(self):
        assert ctrl_key("s") == 19

    def test_ctrl_f(self):
        assert ctrl_key("f") == 6


class TestRowsToString:
    def test_multiple_rows(self):
        E = make_editor(["hello", "world"])
        assert editor_rows_to_string(E) == "hello\nworld"

    def test_empty_editor(self):
        E = make_editor()
        assert editor_rows_to_string(E) == ""

    def test_single_row(self):
        E = make_editor(["hello"])
        assert editor_rows_to_string(E) == "hello"


class TestSetStatusMessage:
    def test_plain_message(self):
        E = make_editor()
        editor_set_status_message(E, "hello")
        assert E.status_msg == "hello"

    def test_format_args(self):
        E = make_editor()
        editor_set_status_message(E, "Count: %d", 5)
        assert E.status_msg == "Count: 5"

    def test_sets_timestamp(self):
        import time
        E = make_editor()
        before = int(time.time())
        editor_set_status_message(E, "hi")
        assert E.status_msg_time >= before

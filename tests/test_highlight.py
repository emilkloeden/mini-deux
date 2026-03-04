from conftest import make_row, make_editor

from mini.highlight import (
    HL_COMMENT,
    HL_FUNCTION,
    HL_KEYWORD,
    HL_NUMBER,
    _cx_to_rx,
    update_syntax,
)


# ---------------------------------------------------------------------------
# _cx_to_rx (highlight.py internal — clamps to row.size)
# ---------------------------------------------------------------------------

class TestCxToRx:
    def test_no_tabs(self):
        row = make_row("hello")
        assert _cx_to_rx(row, 3) == 3

    def test_cx_zero(self):
        row = make_row("hello")
        assert _cx_to_rx(row, 0) == 0

    def test_tab_at_start(self):
        row = make_row("\tabc")
        assert _cx_to_rx(row, 1) == 8

    def test_tab_in_middle(self):
        # "a\tb": tab at col 1. After 'a' rx=1, tab → rx += 6+1 = 8
        row = make_row("a\tb")
        assert _cx_to_rx(row, 2) == 8

    def test_clamps_cx_beyond_row_size(self):
        # cx > row.size is clamped to row.size (no IndexError)
        row = make_row("abc")
        # Same as cx == row.size
        assert _cx_to_rx(row, 100) == _cx_to_rx(row, row.size)

    def test_cx_equals_row_size(self):
        row = make_row("abc")
        assert _cx_to_rx(row, 3) == 3


# ---------------------------------------------------------------------------
# update_syntax — Python source
# ---------------------------------------------------------------------------

class TestUpdateSyntaxPython:
    def setup_method(self):
        lines = ["x = 1", "# comment", "def foo():", "    return x"]
        self.E = make_editor(lines)
        self.E.file_name = "test.py"
        update_syntax(self.E)

    def test_number_highlighted(self):
        # "x = 1": '1' is at char/render index 4
        assert self.E.rows[0].hl[4] == HL_NUMBER

    def test_comment_row_all_comment(self):
        row = self.E.rows[1]  # "# comment"
        assert all(hl == HL_COMMENT for hl in row.hl)

    def test_def_is_grammar_keyword_not_identifier(self):
        # tree-sitter-python treats 'def' as a grammar keyword token, not an
        # (identifier) node, so it is NOT highlighted via the keyword set.
        row = self.E.rows[2]  # "def foo():"
        from mini.highlight import HL_NORMAL
        assert row.hl[0] == HL_NORMAL
        assert row.hl[1] == HL_NORMAL
        assert row.hl[2] == HL_NORMAL

    def test_function_name_highlighted(self):
        row = self.E.rows[2]  # "def foo():"
        # 'foo' is at render positions 4, 5, 6
        assert row.hl[4] == HL_FUNCTION
        assert row.hl[5] == HL_FUNCTION
        assert row.hl[6] == HL_FUNCTION

    def test_return_is_grammar_keyword_not_identifier(self):
        # tree-sitter-python treats 'return' as a grammar keyword token, not an
        # (identifier) node, so it is NOT highlighted via the keyword set.
        row = self.E.rows[3]  # "    return x"
        from mini.highlight import HL_NORMAL
        assert row.hl[4] == HL_NORMAL
        assert row.hl[9] == HL_NORMAL  # last char of 'return'


class TestUpdateSyntaxNoHighlight:
    def test_no_filename_clears_hl(self):
        E = make_editor(["x = 1", "def foo():"])
        E.file_name = ""
        update_syntax(E)
        assert E.rows[0].hl == []
        assert E.rows[1].hl == []

    def test_unknown_extension_clears_hl(self):
        E = make_editor(["x = 1"])
        E.file_name = "README.md"
        update_syntax(E)
        assert E.rows[0].hl == []

    def test_no_crash_on_empty_rows(self):
        E = make_editor()
        E.file_name = "test.py"
        update_syntax(E)  # should not raise

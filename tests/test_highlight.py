import importlib.util

import pytest

from conftest import make_row, make_editor

from mini.highlight import (
    HL_COMMENT,
    HL_FUNCTION,
    HL_KEYWORD,
    HL_NORMAL,
    HL_NUMBER,
    HL_STRING,
    HL_TYPE,
    _cx_to_rx,
    update_syntax,
)

_java_available = importlib.util.find_spec("tree_sitter_java") is not None
_md_available = importlib.util.find_spec("tree_sitter_markdown") is not None


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

    def test_def_is_keyword(self):
        row = self.E.rows[2]  # "def foo():"
        assert row.hl[0] == HL_KEYWORD
        assert row.hl[1] == HL_KEYWORD
        assert row.hl[2] == HL_KEYWORD

    def test_function_name_highlighted(self):
        row = self.E.rows[2]  # "def foo():"
        # 'foo' is at render positions 4, 5, 6
        assert row.hl[4] == HL_FUNCTION
        assert row.hl[5] == HL_FUNCTION
        assert row.hl[6] == HL_FUNCTION

    def test_return_is_keyword(self):
        row = self.E.rows[3]  # "    return x"
        assert row.hl[4] == HL_KEYWORD   # first char of 'return'
        assert row.hl[9] == HL_KEYWORD   # last char of 'return'


class TestUpdateSyntaxNoHighlight:
    def test_no_filename_clears_hl(self):
        E = make_editor(["x = 1", "def foo():"])
        E.file_name = ""
        update_syntax(E)
        assert E.rows[0].hl == []
        assert E.rows[1].hl == []

    def test_unknown_extension_clears_hl(self):
        E = make_editor(["x = 1"])
        E.file_name = "file.xyz"
        update_syntax(E)
        assert E.rows[0].hl == []

    def test_no_crash_on_empty_rows(self):
        E = make_editor()
        E.file_name = "test.py"
        update_syntax(E)  # should not raise


def _hl(lines: list[str], filename: str) -> list[list[int]]:
    E = make_editor(lines)
    E.file_name = filename
    update_syntax(E)
    return [row.hl for row in E.rows]


# ---------------------------------------------------------------------------
# Java
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _java_available, reason="tree-sitter-java not installed")
class TestJavaHighlight:
    def test_line_comment(self):
        hl = _hl(["// this is a comment"], "Foo.java")
        assert all(c == HL_COMMENT for c in hl[0])

    def test_block_comment(self):
        hl = _hl(["/* block */"], "Foo.java")
        assert HL_COMMENT in hl[0]

    def test_string_literal(self):
        hl = _hl(['"hello"'], "Foo.java")
        assert all(c == HL_STRING for c in hl[0])

    def test_integer_literal(self):
        hl = _hl(["42"], "Foo.java")
        assert all(c == HL_NUMBER for c in hl[0])

    def test_keyword_public(self):
        hl = _hl(["public class Foo {}"], "Foo.java")
        assert hl[0][0] == HL_KEYWORD  # "public" starts at col 0

    def test_keyword_class(self):
        hl = _hl(["public class Foo {}"], "Foo.java")
        assert hl[0][7] == HL_KEYWORD  # "class" starts at col 7

    def test_class_name_is_type(self):
        hl = _hl(["public class Foo {}"], "Foo.java")
        assert hl[0][13] == HL_TYPE  # "Foo" starts at col 13

    def test_method_declaration_is_function(self):
        hl = _hl(["void foo() {}"], "Foo.java")
        assert hl[0][5] == HL_FUNCTION  # "foo" starts at col 5

    def test_method_call_is_function(self):
        hl = _hl(["foo();"], "Foo.java")
        assert hl[0][0] == HL_FUNCTION

    def test_return_keyword(self):
        hl = _hl(["return x;"], "Foo.java")
        assert hl[0][0] == HL_KEYWORD

    def test_true_literal(self):
        hl = _hl(["class A { boolean x = true; }"], "Foo.java")
        # "true" starts at col 23
        assert hl[0][23] == HL_KEYWORD

    def test_false_literal(self):
        hl = _hl(["class A { boolean x = false; }"], "Foo.java")
        # "false" starts at col 23
        assert hl[0][23] == HL_KEYWORD

    def test_null_literal(self):
        hl = _hl(["class A { Object x = null; }"], "Foo.java")
        # "null" starts at col 21
        assert hl[0][21] == HL_KEYWORD


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _md_available, reason="tree-sitter-markdown not installed")
class TestMarkdownHighlight:
    def test_h1_heading_is_type(self):
        # tree-sitter-markdown needs a trailing newline (second row) to parse headings
        hl = _hl(["# Hello", ""], "README.md")
        assert all(c == HL_TYPE for c in hl[0])

    def test_h2_heading_is_type(self):
        hl = _hl(["## Section", ""], "README.md")
        assert all(c == HL_TYPE for c in hl[0])

    def test_fenced_code_block_is_string(self):
        hl = _hl(["```", "x = 1", "```"], "README.md")
        assert HL_STRING in hl[0]  # opening fence line

    def test_blockquote_is_comment(self):
        hl = _hl(["> quoted text"], "README.md")
        assert HL_COMMENT in hl[0]

    def test_plain_text_is_normal(self):
        hl = _hl(["just plain text"], "README.md")
        assert all(c == HL_NORMAL for c in hl[0])

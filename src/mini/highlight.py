import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Query, QueryCursor

from mini.config import TAB_STOP
from mini.terminal import term
from mini.types import EditorConfig, EditorRow

HL_NORMAL = 0
HL_COMMENT = 1
HL_KEYWORD = 2
HL_STRING = 3
HL_NUMBER = 4
HL_FUNCTION = 5
HL_TYPE = 6

HL_COLORS = {
    HL_NORMAL:   term.normal,
    HL_COMMENT:  term.bright_black,
    HL_KEYWORD:  term.yellow,
    HL_STRING:   term.green,
    HL_NUMBER:   term.cyan,
    HL_FUNCTION: term.bright_blue,
    HL_TYPE:     term.magenta,
}

PYTHON_KEYWORDS = {
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
    "while", "with", "yield",
}

_LANG = Language(tspython.language())
_PARSER = Parser(_LANG)

_QUERY = Query(_LANG, """
(comment) @comment
(string) @string
(integer) @number
(float) @number
(function_definition name: (identifier) @function)
(class_definition name: (identifier) @type)
(identifier) @identifier
""")

_CAPTURE_HL = {
    "comment": HL_COMMENT,
    "string": HL_STRING,
    "number": HL_NUMBER,
    "function": HL_FUNCTION,
    "type": HL_TYPE,
}


def _cx_to_rx(row: EditorRow, cx: int) -> int:
    rx = 0
    for j in range(min(cx, row.size)):
        if row.chars[j] == "\t":
            rx += (TAB_STOP - 1) - (rx % TAB_STOP)
        rx += 1
    return rx


def update_syntax(E: EditorConfig) -> None:
    if not E.file_name or not E.file_name.endswith(".py"):
        for row in E.rows:
            row.hl = []
        return

    source = "\n".join(row.chars for row in E.rows)
    tree = _PARSER.parse(source.encode())

    for row in E.rows:
        row.hl = [HL_NORMAL] * row.render_size

    cursor = QueryCursor(_QUERY)
    captures = cursor.captures(tree.root_node)

    for capture_name, nodes in captures.items():
        hl_type = _CAPTURE_HL.get(capture_name)
        for node in nodes:
            if capture_name == "identifier":
                if node.text.decode() not in PYTHON_KEYWORDS:
                    continue
                hl_type = HL_KEYWORD

            start_row, start_col = node.start_point
            end_row, end_col = node.end_point

            for row_idx in range(start_row, end_row + 1):
                if row_idx >= len(E.rows):
                    break
                row = E.rows[row_idx]
                col_start = start_col if row_idx == start_row else 0
                col_end = end_col if row_idx == end_row else row.size

                rx_start = _cx_to_rx(row, col_start)
                rx_end = _cx_to_rx(row, col_end)

                for rx in range(rx_start, min(rx_end, row.render_size)):
                    row.hl[rx] = hl_type

import importlib
import os
from dataclasses import dataclass

from tree_sitter import Language, Parser, Query, QueryCursor

from mini.config import TAB_STOP
from mini.types import EditorConfig, EditorRow

HL_NORMAL = 0
HL_COMMENT = 1
HL_KEYWORD = 2
HL_STRING = 3
HL_NUMBER = 4
HL_FUNCTION = 5
HL_TYPE = 6

_CAPTURE_HL = {
    "comment":  HL_COMMENT,
    "keyword":  HL_KEYWORD,
    "string":   HL_STRING,
    "number":   HL_NUMBER,
    "function": HL_FUNCTION,
    "type":     HL_TYPE,
}


@dataclass(frozen=True)
class _LangDef:
    module: str           # importlib name, e.g. "tree_sitter_python"
    lang_fn: str          # attribute on module returning tree-sitter Language
    query: str            # tree-sitter s-expr query string
    keywords: frozenset   # identifiers to colour as HL_KEYWORD; empty = none


_REGISTRY: dict[str, _LangDef] = {
    ".py": _LangDef(
        module="tree_sitter_python",
        lang_fn="language",
        query="""
(comment) @comment
(string) @string
(integer) @number
(float) @number
(function_definition name: (identifier) @function)
(class_definition name: (identifier) @type)
(identifier) @identifier
""",
        keywords=frozenset({
            "False", "None", "True", "and", "as", "assert", "async", "await",
            "break", "class", "continue", "def", "del", "elif", "else", "except",
            "finally", "for", "from", "global", "if", "import", "in", "is",
            "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
            "while", "with", "yield",
        }),
    ),
    ".js": _LangDef(
        module="tree_sitter_javascript",
        lang_fn="language",
        query="""
(comment) @comment
(string) @string
(template_string) @string
(number) @number
(function_declaration name: (identifier) @function)
(method_definition name: _ @function)
(class_declaration name: (identifier) @type)
(identifier) @identifier
""",
        keywords=frozenset({
            "var", "let", "const", "function", "class", "return", "if", "else",
            "for", "while", "do", "switch", "case", "break", "continue", "new",
            "delete", "typeof", "instanceof", "in", "of", "import", "export",
            "default", "try", "catch", "finally", "throw", "async", "await",
            "this", "super", "yield", "static", "extends", "from", "null",
            "undefined", "true", "false",
        }),
    ),
    ".mjs": _LangDef(
        module="tree_sitter_javascript",
        lang_fn="language",
        query="""
(comment) @comment
(string) @string
(template_string) @string
(number) @number
(function_declaration name: (identifier) @function)
(method_definition name: _ @function)
(class_declaration name: (identifier) @type)
(identifier) @identifier
""",
        keywords=frozenset({
            "var", "let", "const", "function", "class", "return", "if", "else",
            "for", "while", "do", "switch", "case", "break", "continue", "new",
            "delete", "typeof", "instanceof", "in", "of", "import", "export",
            "default", "try", "catch", "finally", "throw", "async", "await",
            "this", "super", "yield", "static", "extends", "from", "null",
            "undefined", "true", "false",
        }),
    ),
    ".cjs": _LangDef(
        module="tree_sitter_javascript",
        lang_fn="language",
        query="""
(comment) @comment
(string) @string
(template_string) @string
(number) @number
(function_declaration name: (identifier) @function)
(method_definition name: _ @function)
(class_declaration name: (identifier) @type)
(identifier) @identifier
""",
        keywords=frozenset({
            "var", "let", "const", "function", "class", "return", "if", "else",
            "for", "while", "do", "switch", "case", "break", "continue", "new",
            "delete", "typeof", "instanceof", "in", "of", "import", "export",
            "default", "try", "catch", "finally", "throw", "async", "await",
            "this", "super", "yield", "static", "extends", "from", "null",
            "undefined", "true", "false",
        }),
    ),
    ".ts": _LangDef(
        module="tree_sitter_typescript",
        lang_fn="language_typescript",
        query="""
(comment) @comment
(string) @string
(template_string) @string
(number) @number
(function_declaration name: (identifier) @function)
(method_definition name: _ @function)
(class_declaration name: (type_identifier) @type)
(interface_declaration name: (type_identifier) @type)
(type_alias_declaration name: (type_identifier) @type)
(identifier) @identifier
""",
        keywords=frozenset({
            "var", "let", "const", "function", "class", "return", "if", "else",
            "for", "while", "do", "switch", "case", "break", "continue", "new",
            "delete", "typeof", "instanceof", "in", "of", "import", "export",
            "default", "try", "catch", "finally", "throw", "async", "await",
            "this", "super", "yield", "static", "extends", "from", "null",
            "undefined", "true", "false",
            "interface", "type", "readonly", "private", "public", "protected",
            "abstract", "enum", "namespace", "declare", "as",
        }),
    ),
    ".tsx": _LangDef(
        module="tree_sitter_typescript",
        lang_fn="language_tsx",
        query="""
(comment) @comment
(string) @string
(template_string) @string
(number) @number
(function_declaration name: (identifier) @function)
(method_definition name: _ @function)
(class_declaration name: (type_identifier) @type)
(interface_declaration name: (type_identifier) @type)
(type_alias_declaration name: (type_identifier) @type)
(identifier) @identifier
""",
        keywords=frozenset({
            "var", "let", "const", "function", "class", "return", "if", "else",
            "for", "while", "do", "switch", "case", "break", "continue", "new",
            "delete", "typeof", "instanceof", "in", "of", "import", "export",
            "default", "try", "catch", "finally", "throw", "async", "await",
            "this", "super", "yield", "static", "extends", "from", "null",
            "undefined", "true", "false",
            "interface", "type", "readonly", "private", "public", "protected",
            "abstract", "enum", "namespace", "declare", "as",
        }),
    ),
    ".rs": _LangDef(
        module="tree_sitter_rust",
        lang_fn="language",
        query="""
(line_comment) @comment
(block_comment) @comment
(string_literal) @string
(char_literal) @string
(integer_literal) @number
(float_literal) @number
(function_item name: (identifier) @function)
(struct_item name: (type_identifier) @type)
(enum_item name: (type_identifier) @type)
(type_identifier) @type
(identifier) @identifier
""",
        keywords=frozenset({
            "fn", "let", "mut", "const", "static", "use", "mod", "pub", "struct",
            "enum", "impl", "trait", "type", "where", "for", "while", "loop",
            "if", "else", "match", "return", "break", "continue", "self", "Self",
            "super", "crate", "async", "await", "move", "ref", "in", "as",
        }),
    ),
    ".go": _LangDef(
        module="tree_sitter_go",
        lang_fn="language",
        query="""
(comment) @comment
(interpreted_string_literal) @string
(raw_string_literal) @string
(int_literal) @number
(float_literal) @number
(function_declaration name: (identifier) @function)
(method_declaration name: (field_identifier) @function)
(type_spec name: (type_identifier) @type)
(identifier) @identifier
""",
        keywords=frozenset({
            "func", "var", "const", "type", "package", "import", "if", "else",
            "for", "switch", "case", "select", "return", "break", "continue",
            "goto", "defer", "go", "chan", "map", "struct", "interface", "nil",
            "true", "false", "make", "new", "append",
        }),
    ),
    ".sh": _LangDef(
        module="tree_sitter_bash",
        lang_fn="language",
        query="""
(comment) @comment
(string) @string
(raw_string) @string
(number) @number
(function_definition name: (word) @function)
(word) @identifier
""",
        keywords=frozenset({
            "if", "then", "else", "elif", "fi", "for", "while", "do", "done",
            "case", "esac", "function", "in", "return", "local", "export",
        }),
    ),
    ".bash": _LangDef(
        module="tree_sitter_bash",
        lang_fn="language",
        query="""
(comment) @comment
(string) @string
(raw_string) @string
(number) @number
(function_definition name: (word) @function)
(word) @identifier
""",
        keywords=frozenset({
            "if", "then", "else", "elif", "fi", "for", "while", "do", "done",
            "case", "esac", "function", "in", "return", "local", "export",
        }),
    ),
    ".json": _LangDef(
        module="tree_sitter_json",
        lang_fn="language",
        query="""
(string) @string
(number) @number
(true) @keyword
(false) @keyword
(null) @keyword
""",
        keywords=frozenset(),
    ),
    ".toml": _LangDef(
        module="tree_sitter_toml",
        lang_fn="language",
        query="""
(comment) @comment
(string) @string
(integer) @number
(float) @number
(boolean) @keyword
(bare_key) @function
""",
        keywords=frozenset(),
    ),
    ".c": _LangDef(
        module="tree_sitter_c",
        lang_fn="language",
        query="""
(comment) @comment
(string_literal) @string
(char_literal) @string
(number_literal) @number
(function_declarator declarator: (identifier) @function)
(type_identifier) @type
(identifier) @identifier
""",
        keywords=frozenset({
            "if", "else", "for", "while", "do", "switch", "case", "break",
            "continue", "return", "struct", "enum", "union", "typedef", "const",
            "static", "extern", "void", "int", "char", "float", "double", "long",
            "short", "unsigned", "signed", "sizeof", "goto",
        }),
    ),
    ".h": _LangDef(
        module="tree_sitter_c",
        lang_fn="language",
        query="""
(comment) @comment
(string_literal) @string
(char_literal) @string
(number_literal) @number
(function_declarator declarator: (identifier) @function)
(type_identifier) @type
(identifier) @identifier
""",
        keywords=frozenset({
            "if", "else", "for", "while", "do", "switch", "case", "break",
            "continue", "return", "struct", "enum", "union", "typedef", "const",
            "static", "extern", "void", "int", "char", "float", "double", "long",
            "short", "unsigned", "signed", "sizeof", "goto",
        }),
    ),
}

_lang_cache: dict[str, tuple | None] = {}


def _get_lang(ext: str) -> tuple[Language, Parser, Query, frozenset] | None:
    if ext not in _REGISTRY:
        return None
    if ext in _lang_cache:
        return _lang_cache[ext]
    defn = _REGISTRY[ext]
    try:
        mod = importlib.import_module(defn.module)
        lang = Language(getattr(mod, defn.lang_fn)())
        result: tuple | None = (lang, Parser(lang), Query(lang, defn.query), defn.keywords)
    except Exception:
        result = None  # don't retry
    _lang_cache[ext] = result
    return result


def _cx_to_rx(row: EditorRow, cx: int) -> int:
    rx = 0
    for j in range(min(cx, row.size)):
        if row.chars[j] == "\t":
            rx += (TAB_STOP - 1) - (rx % TAB_STOP)
        rx += 1
    return rx


def update_syntax(E: EditorConfig) -> None:
    if not E.file_name:
        for row in E.rows:
            row.hl = []
        return

    ext = os.path.splitext(E.file_name)[1]
    lang_info = _get_lang(ext)

    if lang_info is None:
        for row in E.rows:
            row.hl = []
        return

    _lang, _parser, query, keywords = lang_info

    source = "\n".join(row.chars for row in E.rows)
    tree = _parser.parse(source.encode())

    for row in E.rows:
        row.hl = [HL_NORMAL] * row.render_size

    cursor = QueryCursor(query)
    captures = cursor.captures(tree.root_node)

    for capture_name, nodes in captures.items():
        if capture_name == "identifier":
            if not keywords:
                continue
            for node in nodes:
                if node.text.decode() not in keywords:
                    continue
                _apply_hl(E, node, HL_KEYWORD)
        else:
            hl_type = _CAPTURE_HL.get(capture_name)
            if hl_type is None:
                continue
            for node in nodes:
                _apply_hl(E, node, hl_type)


def _apply_hl(E: EditorConfig, node: object, hl_type: int) -> None:
    start_row, start_col = node.start_point  # type: ignore[attr-defined]
    end_row, end_col = node.end_point        # type: ignore[attr-defined]

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

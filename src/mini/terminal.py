import re
import sys
import logging
from blessed import Terminal
from mini.keyboard import EditorKey

logging.basicConfig(filename="app.log", level=logging.DEBUG)

term = Terminal()
_raw_ctx = None


def enable_raw_mode(E):
    global _raw_ctx
    _raw_ctx = term.raw()
    _raw_ctx.__enter__()
    return E


def disable_raw_mode(E) -> None:
    global _raw_ctx
    if _raw_ctx:
        _raw_ctx.__exit__(None, None, None)
        _raw_ctx = None


def die():
    reset_screen()
    sys.exit(1)


def reset_screen():
    sys.stdout.write(term.clear + term.home)
    sys.stdout.flush()


def editor_read_key() -> int:
    key = term.inkey(timeout=None)  # blocks until keypress
    if not key:
        return EditorKey.ESCAPE

    if key.is_sequence:
        if key.code is None:
            # Unrecognised sequence — str(key) is the raw escape bytes.
            # Alt+digit: ESC {digit}  e.g. \x1b1
            m = re.match(r"^\x1b([0-9])$", str(key))
            if m:
                return EditorKey.ALT_DIGIT_0 + int(m.group(1))
            return EditorKey.ESCAPE
        mapping = {
            term.KEY_LEFT:      EditorKey.ARROW_LEFT,
            term.KEY_RIGHT:     EditorKey.ARROW_RIGHT,
            term.KEY_UP:        EditorKey.ARROW_UP,
            term.KEY_DOWN:      EditorKey.ARROW_DOWN,
            term.KEY_HOME:      EditorKey.HOME_KEY,
            term.KEY_END:       EditorKey.END_KEY,
            term.KEY_DELETE:    EditorKey.DEL_KEY,
            term.KEY_BACKSPACE: EditorKey.BACKSPACE,
            term.KEY_PPAGE:     EditorKey.PAGE_UP,
            term.KEY_NPAGE:     EditorKey.PAGE_DOWN,
            term.KEY_ENTER:     EditorKey.CARRIAGE_RETURN,
            term.KEY_ESCAPE:    EditorKey.ESCAPE,
        }
        return int(mapping.get(key.code, key.code))

    ch = str(key)
    code = ord(ch) if ch else EditorKey.ESCAPE

    if code == EditorKey.ESCAPE:
        # Some terminals send Alt+digit as two separate events: ESC then the
        # digit.  Drain the read-ahead buffer immediately (non-blocking).
        nk = term.inkey(timeout=0)
        if nk and not nk.is_sequence and str(nk).isdigit():
            return EditorKey.ALT_DIGIT_0 + int(str(nk))
        # Not an Alt+digit — return plain ESC.

    return code

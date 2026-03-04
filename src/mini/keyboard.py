from enum import IntEnum


class EditorKey(IntEnum):
    CARRIAGE_RETURN = 13
    ESCAPE = 27
    BACKSPACE = 127
    ARROW_LEFT = 1000
    ARROW_RIGHT = 1001
    ARROW_UP = 1002
    ARROW_DOWN = 1003
    DEL_KEY = 1004
    HOME_KEY = 1005
    END_KEY = 1006
    PAGE_UP = 1007
    PAGE_DOWN = 1008
    # Alt+0..9 theme selection
    ALT_DIGIT_0 = 1110
    ALT_DIGIT_1 = 1111
    ALT_DIGIT_2 = 1112
    ALT_DIGIT_3 = 1113
    ALT_DIGIT_4 = 1114
    ALT_DIGIT_5 = 1115
    ALT_DIGIT_6 = 1116
    ALT_DIGIT_7 = 1117
    ALT_DIGIT_8 = 1118
    ALT_DIGIT_9 = 1119


DIRECTION_KEYS = (
    EditorKey.ARROW_RIGHT,
    EditorKey.ARROW_LEFT,
    EditorKey.ARROW_DOWN,
    EditorKey.ARROW_UP,
)

from mini.themes import DEFAULT, TOKYO_NIGHT, get_theme


class TestGetTheme:
    def test_default_returns_default(self):
        assert get_theme("default") is DEFAULT

    def test_tokyo_night_underscore(self):
        assert get_theme("tokyo_night") is TOKYO_NIGHT

    def test_tokyo_night_hyphen_alias(self):
        assert get_theme("tokyo-night") is TOKYO_NIGHT

    def test_unknown_falls_back_to_default(self):
        assert get_theme("unknown") is DEFAULT

    def test_empty_string_falls_back_to_default(self):
        assert get_theme("") is DEFAULT


class TestThemeStructure:
    def test_default_hl_colors_length(self):
        assert len(DEFAULT.hl_colors) == 7

    def test_tokyo_night_hl_colors_length(self):
        assert len(TOKYO_NIGHT.hl_colors) == 7

    def test_tokyo_night_hl_colors_are_24bit_rgb(self):
        for color in TOKYO_NIGHT.hl_colors:
            assert "\x1b[38;2;" in color

    def test_tokyo_night_statusbar_insert_has_bg(self):
        assert "\x1b[48;2;" in TOKYO_NIGHT.statusbar_insert

    def test_tokyo_night_statusbar_insert_has_fg(self):
        assert "\x1b[38;2;" in TOKYO_NIGHT.statusbar_insert

    def test_tokyo_night_statusbar_normal_has_bg(self):
        assert "\x1b[48;2;" in TOKYO_NIGHT.statusbar_normal

    def test_tokyo_night_gutter_colors_are_rgb(self):
        for attr in ("gutter_dim", "gutter_current", "gutter_insert"):
            assert "\x1b[38;2;" in getattr(TOKYO_NIGHT, attr)

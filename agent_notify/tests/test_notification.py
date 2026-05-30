"""notification.py 测试。

覆盖: _escape_xml、_default_sound、play_sound、show_toast。
"""

from unittest.mock import MagicMock, patch

# ── _escape_xml 测试 ────────────────────────────────────────────────


class TestEscapeXml:
    """XML 转义函数测试 — 安全关键路径。"""

    def test_plain_text(self):
        from notification import _escape_xml

        assert _escape_xml("hello") == "hello"

    def test_ampersand(self):
        from notification import _escape_xml

        assert _escape_xml("a&b") == "a&amp;b"

    def test_less_than(self):
        from notification import _escape_xml

        assert _escape_xml("a<b") == "a&lt;b"

    def test_greater_than(self):
        from notification import _escape_xml

        assert _escape_xml("a>b") == "a&gt;b"

    def test_double_quote(self):
        from notification import _escape_xml

        assert _escape_xml('a"b') == "a&quot;b"

    def test_single_quote(self):
        from notification import _escape_xml

        assert _escape_xml("a'b") == "a&apos;b"

    def test_all_special_chars(self):
        from notification import _escape_xml

        result = _escape_xml("&<>\"'")
        assert result == "&amp;&lt;&gt;&quot;&apos;"

    def test_empty_string(self):
        from notification import _escape_xml

        assert _escape_xml("") == ""

    def test_xss_attempt(self):
        from notification import _escape_xml

        malicious = '<script>alert("xss")</script>'
        result = _escape_xml(malicious)
        assert "<" not in result.replace("&lt;", "")
        assert ">" not in result.replace("&gt;", "")
        assert '"' not in result.replace("&quot;", "")

    def test_xml_injection_attempt(self):
        from notification import _escape_xml

        malicious = "test</text><text>injected"
        result = _escape_xml(malicious)
        assert "&lt;/text&gt;" in result
        assert "&lt;text&gt;" in result


# ── _default_sound 测试 ─────────────────────────────────────────────


class TestDefaultSound:
    """默认提示音查找测试。"""

    def test_finds_mp3_file(self, tmp_path):
        resources = tmp_path / "resources"
        resources.mkdir()
        (resources / "notify.mp3").write_bytes(b"fake")

        with patch("notification.RESOURCES_DIR", resources):
            from notification import _default_sound

            result = _default_sound()
            assert result is not None
            assert result.name == "notify.mp3"

    def test_finds_wav_file(self, tmp_path):
        resources = tmp_path / "resources"
        resources.mkdir()
        (resources / "alert.wav").write_bytes(b"fake")

        with patch("notification.RESOURCES_DIR", resources):
            from notification import _default_sound

            result = _default_sound()
            assert result is not None
            assert result.name == "alert.wav"

    def test_no_audio_files(self, tmp_path):
        resources = tmp_path / "resources"
        resources.mkdir()
        (resources / "readme.txt").write_text("no audio")

        with patch("notification.RESOURCES_DIR", resources):
            from notification import _default_sound

            assert _default_sound() is None

    def test_no_resources_dir(self, tmp_path):
        with patch("notification.RESOURCES_DIR", tmp_path / "nonexistent"):
            from notification import _default_sound

            assert _default_sound() is None

    def test_unsupported_formats_ignored(self, tmp_path):
        resources = tmp_path / "resources"
        resources.mkdir()
        (resources / "video.mp4").write_bytes(b"fake")
        (resources / "image.png").write_bytes(b"fake")

        with patch("notification.RESOURCES_DIR", resources):
            from notification import _default_sound

            assert _default_sound() is None


# ── play_sound 测试 ─────────────────────────────────────────────────


class TestPlaySound:
    def test_no_audio_file_skips(self, tmp_path):
        with (
            patch("notification._default_sound", return_value=None),
            patch("notification._get_player") as mock_player,
        ):
            from notification import play_sound

            play_sound("")
            mock_player.assert_not_called()

    def test_custom_sound_path(self, tmp_path):
        sound_file = tmp_path / "custom.mp3"
        sound_file.write_bytes(b"fake")

        mock_player = MagicMock()
        with patch("notification._get_player", return_value=mock_player):
            from notification import play_sound

            play_sound(str(sound_file))
            mock_player.setSource.assert_called_once()
            mock_player.play.assert_called_once()

    def test_invalid_custom_path_falls_back_to_default(self, tmp_path):
        default_sound = tmp_path / "default.wav"
        default_sound.write_bytes(b"fake")

        mock_player = MagicMock()
        with (
            patch("notification._default_sound", return_value=default_sound),
            patch("notification._get_player", return_value=mock_player),
        ):
            from notification import play_sound

            play_sound("/nonexistent/path.mp3")
            mock_player.play.assert_called_once()


# ── show_toast 测试 ─────────────────────────────────────────────────


class TestShowToast:
    @patch("notification.subprocess.Popen")
    def test_calls_powershell(self, mock_popen):
        from notification import show_toast

        show_toast("Title", "Message", "source")
        mock_popen.assert_called_once()
        args = mock_popen.call_args
        assert "powershell" in args[0][0]

    @patch("notification.subprocess.Popen")
    def test_powershell_not_found(self, mock_popen):
        mock_popen.side_effect = FileNotFoundError
        from notification import show_toast

        # 不应抛异常
        show_toast("Title", "Message")

    @patch("notification.subprocess.Popen")
    def test_os_error_handled(self, mock_popen):
        mock_popen.side_effect = OSError("access denied")
        from notification import show_toast

        show_toast("Title", "Message")

"""updater.py 测试。

覆盖: _parse_version、check_update。
"""

import json
from unittest.mock import MagicMock, patch
from urllib.error import URLError

# ── _parse_version 测试 ─────────────────────────────────────────────


class TestParseVersion:
    """版本号解析测试。"""

    def test_standard_version(self):
        from updater import _parse_version
        assert _parse_version("1.2.3") == (1, 2, 3)

    def test_with_v_prefix(self):
        from updater import _parse_version
        assert _parse_version("v1.2.3") == (1, 2, 3)

    def test_two_segments(self):
        from updater import _parse_version
        assert _parse_version("1.2") == (1, 2, 0)

    def test_one_segment(self):
        from updater import _parse_version
        assert _parse_version("5") == (5, 0, 0)

    def test_pre_release_suffix(self):
        from updater import _parse_version
        assert _parse_version("1.2.0-beta1") == (1, 2, 0)

    def test_pre_release_with_v(self):
        from updater import _parse_version
        assert _parse_version("v2.0.0-rc1") == (2, 0, 0)

    def test_alpha_suffix(self):
        from updater import _parse_version
        assert _parse_version("1.0.0-alpha.3") == (1, 0, 0)

    def test_dev_suffix(self):
        from updater import _parse_version
        assert _parse_version("3.1.0.dev5") == (3, 1, 0)

    def test_trailing_whitespace(self):
        from updater import _parse_version
        assert _parse_version("v1.2.3 ") == (1, 2, 3)

    def test_zero_version(self):
        from updater import _parse_version
        assert _parse_version("0.0.0") == (0, 0, 0)

    def test_large_numbers(self):
        from updater import _parse_version
        assert _parse_version("10.20.30") == (10, 20, 30)


# ── check_update 测试 ───────────────────────────────────────────────


class TestCheckUpdate:
    """更新检查测试。"""

    def _make_release_response(self, tag: str, has_exe: bool = True) -> bytes:
        assets = []
        if has_exe:
            assets.append({
                "name": "AgentNotify.exe",
                "browser_download_url": "https://example.com/AgentNotify.exe",
            })
        return json.dumps({
            "tag_name": tag,
            "html_url": "https://github.com/example/releases/v9.9.9",
            "assets": assets,
        }).encode()

    @patch("updater.urllib.request.urlopen")
    def test_new_version_available(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = self._make_release_response("v9.9.9")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        with patch("updater.__version__", "1.0.0"):
            from updater import check_update
            result = check_update()
            assert result.available is True
            assert result.latest_version == "v9.9.9"
            assert "AgentNotify.exe" in result.download_url

    @patch("updater.urllib.request.urlopen")
    def test_same_version(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = self._make_release_response("v1.2.0")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        with patch("updater.__version__", "1.2.0"):
            from updater import check_update
            result = check_update()
            assert result.available is False

    @patch("updater.urllib.request.urlopen")
    def test_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("timeout")

        from updater import check_update
        result = check_update()
        assert result.available is False

    @patch("updater.urllib.request.urlopen")
    def test_no_exe_asset(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = self._make_release_response("v9.9.9", has_exe=False)
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        with patch("updater.__version__", "1.0.0"):
            from updater import check_update
            result = check_update()
            assert result.available is True
            # 无 exe 时回退到 html_url
            assert "github.com" in result.download_url

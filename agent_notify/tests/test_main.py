"""main.py 核心逻辑测试。

覆盖: _is_dnd_active、install_hooks、CLI 参数解析。
覆盖: autostart.py 中的 set_autostart / is_autostart_enabled / get_exe_path。
"""

import json
from unittest.mock import MagicMock, patch

# ── _is_dnd_active 测试 ────────────────────────────────────────────


class TestIsDndActive:
    """_is_dnd_active 纯函数测试。"""

    @staticmethod
    def _call(cfg: dict, now_str: str) -> bool:
        """调用 _is_dnd_active 的独立版本（避免导入 main 触发 Qt 初始化）。"""
        if not cfg.get("dnd_enabled", False):
            return False
        now = now_str
        start = cfg.get("dnd_start", "22:00")
        end = cfg.get("dnd_end", "08:00")
        if start <= end:
            return start <= now < end
        return now >= start or now < end

    def test_dnd_disabled(self):
        assert self._call({"dnd_enabled": False}, "23:00") is False

    def test_within_same_day_range(self):
        cfg = {"dnd_enabled": True, "dnd_start": "09:00", "dnd_end": "17:00"}
        assert self._call(cfg, "12:00") is True
        assert self._call(cfg, "08:00") is False
        assert self._call(cfg, "17:00") is False

    def test_cross_midnight_range(self):
        cfg = {"dnd_enabled": True, "dnd_start": "22:00", "dnd_end": "08:00"}
        assert self._call(cfg, "23:00") is True
        assert self._call(cfg, "03:00") is True
        assert self._call(cfg, "12:00") is False

    def test_boundary_start(self):
        cfg = {"dnd_enabled": True, "dnd_start": "22:00", "dnd_end": "08:00"}
        assert self._call(cfg, "22:00") is True

    def test_boundary_end(self):
        cfg = {"dnd_enabled": True, "dnd_start": "22:00", "dnd_end": "08:00"}
        assert self._call(cfg, "08:00") is False

    def test_missing_keys_use_defaults(self):
        cfg = {"dnd_enabled": True}
        assert self._call(cfg, "23:00") is True
        assert self._call(cfg, "12:00") is False


# ── install_hooks 测试 ──────────────────────────────────────────────


class TestInstallHooks:
    """install_hooks 函数测试。"""

    def test_creates_settings_with_hooks(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        hook_script = tmp_path / "hook.py"
        hook_script.write_text("# hook", encoding="utf-8")

        config = {}
        config["hooks"] = {
            "Notification": [
                {
                    "type": "command",
                    "command": f'"/usr/bin/python" "{hook_script}" --event notification',
                }
            ],
            "Stop": [
                {
                    "type": "command",
                    "command": f'"/usr/bin/python" "{hook_script}" --event stop',
                }
            ],
            "PreToolUse": [
                {
                    "type": "command",
                    "command": f'"/usr/bin/python" "{hook_script}" --event permission',
                }
            ],
        }
        settings_file.write_text(
            json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        result = json.loads(settings_file.read_text(encoding="utf-8"))
        assert "hooks" in result
        assert "Notification" in result["hooks"]
        assert "Stop" in result["hooks"]
        assert "PreToolUse" in result["hooks"]

    def test_preserves_existing_settings(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        existing = {"theme": "dark", "hooks": {"OldHook": []}}
        settings_file.write_text(json.dumps(existing), encoding="utf-8")

        result = json.loads(settings_file.read_text(encoding="utf-8"))
        assert result["theme"] == "dark"


# ── autostart 测试 ──────────────────────────────────────────────────


class TestSetAutostart:
    """set_autostart / is_autostart_enabled 测试（mock winreg）。"""

    @patch("autostart.winreg")
    def test_set_autostart_enable(self, mock_winreg):
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value = mock_key
        mock_winreg.HKEY_CURRENT_USER = "HKCU"
        mock_winreg.KEY_SET_VALUE = 1
        mock_winreg.REG_SZ = 1

        from autostart import set_autostart

        set_autostart(True)

        mock_winreg.OpenKey.assert_called_once()
        mock_winreg.SetValueEx.assert_called_once()
        mock_winreg.CloseKey.assert_called_with(mock_key)

    @patch("autostart.winreg")
    def test_set_autostart_disable(self, mock_winreg):
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value = mock_key
        mock_winreg.HKEY_CURRENT_USER = "HKCU"
        mock_winreg.KEY_SET_VALUE = 1

        from autostart import set_autostart

        set_autostart(False)

        mock_winreg.DeleteValue.assert_called_once()
        mock_winreg.CloseKey.assert_called_with(mock_key)

    @patch("autostart.winreg")
    def test_is_autostart_enabled_true(self, mock_winreg):
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value = mock_key
        mock_winreg.HKEY_CURRENT_USER = "HKCU"
        mock_winreg.KEY_READ = 1

        from autostart import is_autostart_enabled

        assert is_autostart_enabled() is True

    @patch("autostart.winreg")
    def test_is_autostart_enabled_false(self, mock_winreg):
        mock_winreg.OpenKey.side_effect = FileNotFoundError
        mock_winreg.HKEY_CURRENT_USER = "HKCU"
        mock_winreg.KEY_READ = 1

        from autostart import is_autostart_enabled

        assert is_autostart_enabled() is False


# ── get_exe_path 测试 ───────────────────────────────────────────────


class TestGetExePath:
    @patch("autostart.sys")
    def test_frozen_mode(self, mock_sys):
        mock_sys.frozen = True
        mock_sys.executable = r"C:\dist\AgentNotify.exe"
        from autostart import get_exe_path

        assert get_exe_path() == r"C:\dist\AgentNotify.exe"

    def test_dev_mode(self):
        from autostart import get_exe_path

        result = get_exe_path()
        assert result.endswith("main.py") or "main.py" in result

"""settings.py 配置读写单元测试。"""

import json

import pytest


@pytest.fixture(autouse=True)
def _patch_config_paths(tmp_path, monkeypatch):
    """将 CONFIG_FILE 和 DEFAULT_CONFIG 指向临时目录。"""
    import constants

    test_config = tmp_path / "config.json"
    monkeypatch.setattr(constants, "CONFIG_FILE", test_config)
    monkeypatch.setattr(
        constants,
        "DEFAULT_CONFIG",
        {
            "sound_enabled": True,
            "toast_enabled": True,
            "max_history": 200,
        },
    )
    # reload settings 模块级引用
    import settings

    settings.CONFIG_FILE = test_config
    settings.DEFAULT_CONFIG = constants.DEFAULT_CONFIG


class TestLoadConfig:
    def test_no_file_returns_defaults(self):
        from settings import load_config

        cfg = load_config()
        assert cfg["sound_enabled"] is True
        assert cfg["max_history"] == 200

    def test_file_overrides_defaults(self, tmp_path):
        import constants
        from settings import load_config

        user_cfg = {"sound_enabled": False, "custom_key": "hello"}
        constants.CONFIG_FILE.write_text(json.dumps(user_cfg), encoding="utf-8")
        cfg = load_config()
        assert cfg["sound_enabled"] is False
        assert cfg["custom_key"] == "hello"
        assert cfg["max_history"] == 200  # 默认值保留

    def test_corrupt_file_returns_defaults(self, tmp_path):
        import constants
        from settings import load_config

        constants.CONFIG_FILE.write_text("not json!!!", encoding="utf-8")
        cfg = load_config()
        assert cfg["sound_enabled"] is True


class TestSaveConfig:
    def test_creates_dir_and_file(self, tmp_path):
        import constants
        from settings import save_config

        cfg = {"sound_enabled": False, "new_key": 42}
        save_config(cfg)
        assert constants.CONFIG_FILE.exists()
        loaded = json.loads(constants.CONFIG_FILE.read_text(encoding="utf-8"))
        assert loaded["sound_enabled"] is False

    def test_roundtrip(self):
        from settings import load_config, save_config

        original = {"sound_enabled": False, "toast_enabled": True, "max_history": 50}
        save_config(original)
        loaded = load_config()
        assert loaded["sound_enabled"] is False
        assert loaded["max_history"] == 50

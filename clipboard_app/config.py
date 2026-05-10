import json
import os
import sys


def get_app_dir():
    """获取应用数据目录"""
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    app_dir = os.path.join(appdata, "ClipboardHistory")
    os.makedirs(app_dir, exist_ok=True)
    os.makedirs(os.path.join(app_dir, "images"), exist_ok=True)
    return app_dir


def get_config_path():
    return os.path.join(get_app_dir(), "config.json")


DEFAULT_CONFIG = {
    "retention_days": 3,
    "max_items": 500,
    "max_text_length": 5000,
    "poll_interval_ms": 500,
    "auto_paste": True,
}

_config_cache = None


def load_config():
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    path = get_config_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = v
            _config_cache = cfg
            return cfg
        except Exception:
            pass
    _config_cache = dict(DEFAULT_CONFIG)
    return _config_cache


def save_config(cfg):
    global _config_cache
    _config_cache = cfg
    path = get_config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

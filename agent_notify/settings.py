"""配置管理 — JSON 配置文件的读写与默认值合并。

配置文件路径: ~/.agent-notify/config.json
不存在或损坏时自动回退到 DEFAULT_CONFIG。
"""

import json
from constants import CONFIG_FILE, DEFAULT_CONFIG


def load_config() -> dict:
    """加载配置，与默认值合并后返回。

    合并策略：DEFAULT_CONFIG 提供基础值，用户配置覆盖同名键。
    文件不存在或 JSON 解析失败时返回纯默认配置。

    Returns:
        合并后的配置字典，保证所有 DEFAULT_CONFIG 中的键都存在。
    """
    if CONFIG_FILE.exists():
        try:
            return {**DEFAULT_CONFIG, **json.loads(CONFIG_FILE.read_text(encoding="utf-8"))}
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULT_CONFIG)


def save_config(config: dict) -> None:
    """保存配置到 JSON 文件（自动创建目录）。

    Args:
        config: 完整配置字典，将覆盖写入。
    """
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

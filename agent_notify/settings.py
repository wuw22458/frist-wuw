"""配置管理 — JSON 配置文件的读写、默认值合并与校验。

配置文件路径: ~/.agent-notify/config.json
不存在或损坏时自动回退到 DEFAULT_CONFIG。
"""

import json

from constants import CONFIG_FILE, DEFAULT_CONFIG
from log import get_logger

logger = get_logger("settings")

# 已知配置键（DEFAULT_CONFIG + adapter 动态键前缀）
_KNOWN_PREFIXES = (
    "source_",
    "custom_sound",
    "sound_enabled",
    "toast_enabled",
    "auto_start",
    "max_history",
    "dnd_",
)


def _validate_config(config: dict) -> dict:
    """校验配置，对未知键记录警告但不移除。"""
    for key in config:
        if key not in DEFAULT_CONFIG and not any(
            key.startswith(p) for p in _KNOWN_PREFIXES
        ):
            logger.debug("未知配置键: %s", key)
    return config


def load_config() -> dict:
    """加载配置，与默认值合并后返回。

    合并策略：DEFAULT_CONFIG 提供基础值，用户配置覆盖同名键。
    文件不存在或 JSON 解析失败时返回纯默认配置。

    Returns:
        合并后的配置字典，保证所有 DEFAULT_CONFIG 中的键都存在。
    """
    if CONFIG_FILE.exists():
        try:
            raw = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            validated = _validate_config(raw)
            return {**DEFAULT_CONFIG, **validated}
        except (json.JSONDecodeError, OSError) as e:
            logger.error("配置文件读取失败，使用默认配置: %s", e)
    return dict(DEFAULT_CONFIG)


def save_config(config: dict) -> None:
    """保存配置到 JSON 文件（自动创建目录）。

    Args:
        config: 完整配置字典，将覆盖写入。
    """
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(
            json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.debug("配置已保存: %s", CONFIG_FILE)
    except OSError as e:
        logger.error("配置文件写入失败: %s", e)

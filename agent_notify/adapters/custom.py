"""CustomAgentLoader — 从 YAML 配置文件加载用户自定义 Agent。

用户在 ~/.agent-notify/custom_agents.yaml 中声明自定义 Agent，
启动时自动加载并注册为 SignalFileAdapter 子类。

YAML 格式示例：
    agents:
      - agent_id: my-agent
        display_name: My Agent
        description: 监控我的自定义 agent
        type: signal_file
        glob_pattern: "my_agent_*.json"
        event_map:
          needs_input: waiting
          done: completed
        poll_interval_ms: 2000
"""

from __future__ import annotations

from pathlib import Path

from adapters.signal_file import SignalFileAdapter
from adapters.registry import AdapterRegistry
from events import EventType
from constants import SIGNAL_DIR

CUSTOM_AGENTS_FILE = SIGNAL_DIR / "custom_agents.yaml"

# YAML 中 event_map 的值映射
_EVENT_TYPE_MAP = {
    "waiting": EventType.WAITING,
    "completed": EventType.COMPLETED,
    "error": EventType.ERROR,
    "info": EventType.INFO,
}


def _create_adapter_class(agent_def: dict) -> type[SignalFileAdapter]:
    """从 YAML 定义动态创建 SignalFileAdapter 子类。"""
    agent_id = agent_def["agent_id"]
    display_name = agent_def.get("display_name", agent_id)
    description = agent_def.get("description", "")
    glob_pattern = agent_def.get("glob_pattern", f"{agent_id}_*.json")
    poll_interval = agent_def.get("poll_interval_ms", 1000)

    # 解析 event_map
    raw_map = agent_def.get("event_map", {})
    event_map = {}
    for raw_key, event_str in raw_map.items():
        event_map[raw_key] = _EVENT_TYPE_MAP.get(event_str, EventType.INFO)

    # 排除文件名
    exclude = set(agent_def.get("exclude_names", []))

    cls = type(
        f"Custom_{agent_id.replace('-', '_')}",
        (SignalFileAdapter,),
        {
            "agent_id": agent_id,
            "display_name": display_name,
            "description": description,
            "glob_pattern": glob_pattern,
            "exclude_names": exclude,
            "event_map": event_map,
            "poll_interval_ms": poll_interval,
        },
    )
    return cls


def _register_classes(data: dict) -> list[type[SignalFileAdapter]]:
    """从解析后的数据中创建并注册自定义 adapter 类。"""
    classes = []
    for agent_def in data.get("agents", []):
        if "agent_id" not in agent_def:
            continue
        cls = _create_adapter_class(agent_def)
        AdapterRegistry._register(cls)
        classes.append(cls)
    return classes


def load_custom_agents() -> list[type[SignalFileAdapter]]:
    """读取 YAML 配置文件，创建并注册自定义 adapter 类。"""
    if not CUSTOM_AGENTS_FILE.exists():
        return []

    try:
        import yaml
    except ImportError:
        return _load_custom_agents_json_fallback()

    try:
        with open(CUSTOM_AGENTS_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception:
        return []

    if not data or "agents" not in data:
        return []

    return _register_classes(data)


def _load_custom_agents_json_fallback() -> list[type[SignalFileAdapter]]:
    """PyYAML 不可用时，尝试用 JSON 格式解析（YAML 的子集）。"""
    import json

    try:
        data = json.loads(CUSTOM_AGENTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

    if not data or "agents" not in data:
        return []

    return _register_classes(data)


def create_template() -> None:
    """创建 custom_agents.yaml 模板文件。"""
    template = """\
# Agent Notify 自定义 Agent 配置
# 在此文件中声明你的自定义 Agent，无需编写 Python 代码。
#
# 每个 agent 需要：
#   agent_id:      唯一标识符（用于配置文件中的 source_* 键）
#   display_name:  UI 显示名称
#   description:   一行功能描述
#   glob_pattern:  匹配信号文件的 glob 模式（相对于 ~/.agent-notify/）
#   event_map:     原始 event 值 → 事件类型的映射
#                  支持的事件类型: waiting, completed, error, info
#
# 你的 agent 需要写入 JSON 信号文件到 ~/.agent-notify/，格式：
#   {"event": "<event_key>", "message": "<显示给用户的消息>"}
#
# 文件名格式：{agent_id}_<timestamp>.json

agents: []
  # 示例：
  # - agent_id: my-custom-agent
  #   display_name: My Agent
  #   description: 监控我的自定义 AI agent
  #   glob_pattern: "my_custom-agent_*.json"
  #   event_map:
  #     needs_input: waiting
  #     done: completed
  #   poll_interval_ms: 2000
"""
    CUSTOM_AGENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CUSTOM_AGENTS_FILE.write_text(template, encoding="utf-8")

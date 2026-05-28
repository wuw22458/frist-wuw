"""Agent Adapter 包 — 可扩展的多 Agent 检测适配器。

自动发现 adapters/ 目录下所有模块并触发 @register_adapter 注册。
新增 adapter 只需在 adapters/ 下新建 .py 文件，无需修改本文件。
"""

import importlib
import pkgutil

from adapters.base import AgentAdapter, PollingAdapter
from adapters.registry import AdapterRegistry, register_adapter

# 自动扫描并导入所有 adapter 模块（排除基础设施模块）
_SKIP = {"base", "registry", "signal_file", "__init__"}
for _importer, _modname, _ispkg in pkgutil.iter_modules(__path__):
    if _modname not in _SKIP:
        importlib.import_module(f".{_modname}", __package__)

# 加载用户自定义 Agent（从 YAML 配置文件）
from adapters.custom import load_custom_agents  # noqa: E402

load_custom_agents()

__all__ = ["AgentAdapter", "PollingAdapter", "AdapterRegistry", "register_adapter"]

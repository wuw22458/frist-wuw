"""AdapterRegistry — Agent Adapter 注册表.

通过 @register_adapter 装饰器自动注册所有 adapter 类.
运行时根据配置实例化并管理 adapter 生命周期.
"""

from __future__ import annotations

from adapters.base import AgentAdapter
from event_bus import EventBus


class AdapterRegistry:
    """管理所有已注册的 AgentAdapter 类和实例."""

    _classes: dict[str, type[AgentAdapter]] = {}
    _instances: dict[str, AgentAdapter] = {}

    @classmethod
    def _register(cls, adapter_cls: type[AgentAdapter]) -> None:
        agent_id = adapter_cls.agent_id
        if not agent_id:
            raise ValueError(f'{adapter_cls.__name__} 必须定义 agent_id')
        cls._classes[agent_id] = adapter_cls

    @classmethod
    def get_all_classes(cls) -> list[type[AgentAdapter]]:
        """返回所有已注册的 adapter 类."""
        return list(cls._classes.values())

    @classmethod
    def get_class(cls, agent_id: str) -> type[AgentAdapter] | None:
        """按 agent_id 获取 adapter 类."""
        return cls._classes.get(agent_id)

    @classmethod
    def create_enabled(cls, event_bus: EventBus, config: dict) -> list[AgentAdapter]:
        """根据配置实例化所有启用的 adapter."""
        instances = []
        for agent_id, adapter_cls in cls._classes.items():
            key = f'source_{agent_id}'
            if config.get(key, True):
                instance = adapter_cls(event_bus, config)
                cls._instances[agent_id] = instance
                instances.append(instance)
        return instances

    @classmethod
    def get_instance(cls, agent_id: str) -> AgentAdapter | None:
        """获取已实例化的 adapter."""
        return cls._instances.get(agent_id)

    @classmethod
    def get_all_instances(cls) -> list[AgentAdapter]:
        """返回所有已实例化的 adapter."""
        return list(cls._instances.values())

    @classmethod
    def stop_all(cls) -> None:
        """停止所有运行中的 adapter."""
        for instance in cls._instances.values():
            if instance.is_running():
                instance.stop()
        cls._instances.clear()

    @classmethod
    def get_default_config(cls) -> dict:
        """收集所有 adapter 的默认配置项(每个 adapter 自动拥有 source_{agent_id} 键)."""
        config = {}
        for adapter_cls in cls._classes.values():
            key = f'source_{adapter_cls.agent_id}'
            config[key] = True
        return config

    @classmethod
    def reset(cls) -> None:
        """重置注册表(仅用于测试)."""
        cls._classes.clear()
        cls._instances.clear()


def register_adapter(cls: type[AgentAdapter]) -> type[AgentAdapter]:
    """装饰器:将 AgentAdapter 子类注册到 AdapterRegistry.

    用法:
        @register_adapter
        class MyAdapter(AgentAdapter):
            agent_id = "my-agent"
            ...
    """
    AdapterRegistry._register(cls)
    return cls

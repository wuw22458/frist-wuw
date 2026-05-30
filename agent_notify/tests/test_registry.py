"""AdapterRegistry 注册表单元测试。"""

import pytest

from adapters.base import AgentAdapter
from adapters.registry import AdapterRegistry, register_adapter


@pytest.fixture(autouse=True)
def _clean_registry():
    """每个测试前后重置注册表。"""
    AdapterRegistry.reset()
    yield
    AdapterRegistry.reset()


class _DummyAdapter(AgentAdapter):
    agent_id = "dummy"
    display_name = "Dummy"
    description = "test"

    def start(self):
        pass

    def stop(self):
        pass

    def is_running(self):
        return False


class _NoIdAdapter(AgentAdapter):
    agent_id = ""

    def start(self):
        pass

    def stop(self):
        pass

    def is_running(self):
        return False


class TestAdapterRegistry:
    def test_register_and_get_all(self):
        AdapterRegistry._register(_DummyAdapter)
        classes = AdapterRegistry.get_all_classes()
        assert _DummyAdapter in classes

    def test_register_no_agent_id_raises(self):
        with pytest.raises(ValueError, match="agent_id"):
            AdapterRegistry._register(_NoIdAdapter)

    def test_get_class(self):
        AdapterRegistry._register(_DummyAdapter)
        assert AdapterRegistry.get_class("dummy") is _DummyAdapter
        assert AdapterRegistry.get_class("nonexistent") is None

    def test_reset(self):
        AdapterRegistry._register(_DummyAdapter)
        AdapterRegistry.reset()
        assert AdapterRegistry.get_all_classes() == []

    def test_get_default_config(self):
        AdapterRegistry._register(_DummyAdapter)
        cfg = AdapterRegistry.get_default_config()
        assert cfg["source_dummy"] is True

    def test_create_enabled(self, qapp):
        from event_bus import get_bus, reset_bus

        reset_bus()
        bus = get_bus()
        AdapterRegistry._register(_DummyAdapter)
        instances = AdapterRegistry.create_enabled(bus, {"source_dummy": True})
        assert len(instances) == 1
        assert instances[0].agent_id == "dummy"
        reset_bus()

    def test_create_enabled_disabled(self, qapp):
        from event_bus import get_bus, reset_bus

        reset_bus()
        bus = get_bus()
        AdapterRegistry._register(_DummyAdapter)
        instances = AdapterRegistry.create_enabled(bus, {"source_dummy": False})
        assert len(instances) == 0
        reset_bus()


class TestRegisterAdapterDecorator:
    def test_decorator_registers_class(self):
        @register_adapter
        class Decorated(AgentAdapter):
            agent_id = "decorated"

            def start(self):
                pass

            def stop(self):
                pass

            def is_running(self):
                return False

        assert AdapterRegistry.get_class("decorated") is Decorated

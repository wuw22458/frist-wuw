"""adapters/custom.py 自定义 Agent 加载单元测试。"""

import builtins
import json
import pytest
from adapters.registry import AdapterRegistry
from adapters.custom import (
    _create_adapter_class, _load_custom_agents_json_fallback,
    load_custom_agents, create_template,
)
from events import EventType


@pytest.fixture(autouse=True)
def _clean_registry():
    AdapterRegistry.reset()
    yield
    AdapterRegistry.reset()


def _no_yaml(monkeypatch):
    """让 import yaml 抛出 ImportError，触发 JSON fallback。"""
    real_import = builtins.__import__

    def _mock_import(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("no yaml")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _mock_import)


class TestCreateAdapterClass:
    def test_full_definition(self):
        cls = _create_adapter_class({
            "agent_id": "my-agent",
            "display_name": "My Agent",
            "description": "test agent",
            "glob_pattern": "my_*.json",
            "event_map": {"go": "waiting", "done": "completed"},
            "poll_interval_ms": 2000,
            "exclude_names": ["skip.json"],
        })
        assert cls.agent_id == "my-agent"
        assert cls.display_name == "My Agent"
        assert cls.glob_pattern == "my_*.json"
        assert cls.event_map["go"] == EventType.WAITING
        assert cls.event_map["done"] == EventType.COMPLETED
        assert cls.poll_interval_ms == 2000
        assert "skip.json" in cls.exclude_names

    def test_minimal_definition(self):
        cls = _create_adapter_class({"agent_id": "minimal"})
        assert cls.agent_id == "minimal"
        assert cls.display_name == "minimal"
        assert cls.glob_pattern == "minimal_*.json"
        assert cls.poll_interval_ms == 1000

    def test_unknown_event_map_value_defaults_to_info(self):
        cls = _create_adapter_class({
            "agent_id": "unknown-events",
            "event_map": {"weird_event": "nonexistent"},
        })
        assert cls.event_map["weird_event"] == EventType.INFO


class TestLoadCustomAgentsJsonFallback:
    def test_file_not_exists(self, signal_dir):
        result = _load_custom_agents_json_fallback()
        assert result == []

    def test_valid_json(self, signal_dir):
        config = {
            "agents": [
                {"agent_id": "custom1", "display_name": "Custom One"},
                {"agent_id": "custom2"},
            ]
        }
        (signal_dir / "custom_agents.yaml").write_text(json.dumps(config), encoding="utf-8")
        classes = _load_custom_agents_json_fallback()
        assert len(classes) == 2
        assert classes[0].agent_id == "custom1"
        assert classes[1].agent_id == "custom2"
        assert AdapterRegistry.get_class("custom1") is not None

    def test_missing_agent_id_skipped(self, signal_dir):
        config = {
            "agents": [
                {"agent_id": "valid"},
                {"display_name": "No ID"},
            ]
        }
        (signal_dir / "custom_agents.yaml").write_text(json.dumps(config), encoding="utf-8")
        classes = _load_custom_agents_json_fallback()
        assert len(classes) == 1

    def test_empty_agents_list(self, signal_dir):
        (signal_dir / "custom_agents.yaml").write_text(json.dumps({"agents": []}), encoding="utf-8")
        assert _load_custom_agents_json_fallback() == []


class TestLoadCustomAgents:
    def test_yaml_unavailable_falls_back(self, signal_dir, monkeypatch):
        _no_yaml(monkeypatch)
        config = {"agents": [{"agent_id": "fb"}]}
        (signal_dir / "custom_agents.yaml").write_text(json.dumps(config), encoding="utf-8")
        classes = load_custom_agents()
        assert len(classes) == 1
        assert classes[0].agent_id == "fb"


class TestCreateTemplate:
    def test_creates_file(self, signal_dir):
        create_template()
        f = signal_dir / "custom_agents.yaml"
        assert f.exists()
        content = f.read_text(encoding="utf-8")
        assert "agents:" in content
        assert "agent_id" in content

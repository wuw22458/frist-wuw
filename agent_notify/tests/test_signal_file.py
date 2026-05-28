"""SignalFileAdapter 信号文件轮询单元测试。"""

import json

import pytest

from events import EventType


@pytest.fixture()
def adapter(qapp, signal_dir):
    """创建一个测试用 SignalFileAdapter 子类实例。"""
    from event_bus import get_bus, reset_bus
    reset_bus()
    bus = get_bus()

    from adapters.signal_file import SignalFileAdapter

    class TestAdapter(SignalFileAdapter):
        agent_id = "test-agent"
        display_name = "Test"
        glob_pattern = "*.json"
        exclude_names = {"config.json"}
        event_map = {
            "waiting": EventType.WAITING,
            "done": EventType.COMPLETED,
        }

    instance = TestAdapter(bus, {"source_test-agent": True})
    return instance, bus, signal_dir


class TestSignalFileCheck:
    def test_no_files_no_event(self, adapter):
        inst, bus, sd = adapter
        received = []
        bus.event_received.connect(lambda e: received.append(e))
        inst.check()
        assert len(received) == 0

    def test_valid_json_emits_event(self, adapter):
        inst, bus, sd = adapter
        received = []
        bus.event_received.connect(lambda e: received.append(e))
        (sd / "signal.json").write_text(json.dumps({
            "event": "waiting", "message": "please confirm"
        }), encoding="utf-8")
        inst.check()
        assert len(received) == 1
        assert received[0].event_type == EventType.WAITING
        assert received[0].message == "please confirm"
        assert not (sd / "signal.json").exists()  # 文件已删除

    def test_exclude_names_skipped(self, adapter):
        inst, bus, sd = adapter
        received = []
        bus.event_received.connect(lambda e: received.append(e))
        (sd / "config.json").write_text(json.dumps({"event": "waiting"}), encoding="utf-8")
        inst.check()
        assert len(received) == 0
        assert (sd / "config.json").exists()  # 不删除

    def test_invalid_json_file_preserved_for_debug(self, adapter):
        """解析失败的信号文件保留不删除，便于排查问题。"""
        inst, bus, sd = adapter
        (sd / "bad.json").write_text("not json", encoding="utf-8")
        inst.check()
        assert (sd / "bad.json").exists()

    def test_processed_set_prevents_duplicate(self, adapter):
        inst, bus, sd = adapter
        received = []
        bus.event_received.connect(lambda e: received.append(e))
        (sd / "dup.json").write_text(json.dumps({"event": "done", "message": "ok"}), encoding="utf-8")
        inst.check()
        # 文件已删除，但再调一次 check 不应出错
        inst.check()
        assert len(received) == 1

    def test_unknown_event_maps_to_info(self, adapter):
        inst, bus, sd = adapter
        received = []
        bus.event_received.connect(lambda e: received.append(e))
        (sd / "unknown.json").write_text(json.dumps({
            "event": "something_weird", "message": "hmm"
        }), encoding="utf-8")
        inst.check()
        assert len(received) == 1
        assert received[0].event_type == EventType.INFO

"""CursorAdapter 状态机单元测试。"""

import pytest
from unittest.mock import patch, MagicMock
from events import EventType


@pytest.fixture()
def cursor_adapter(qapp, signal_dir):
    """创建 CursorAdapter 实例（需要 QApplication）。"""
    from event_bus import get_bus, reset_bus
    reset_bus()
    bus = get_bus()
    from adapters.cursor import CursorAdapter
    adapter = CursorAdapter(bus, {"source_cursor": True})
    return adapter, bus


class TestCursorStateMachine:
    def test_no_attention_no_event(self, cursor_adapter):
        adapter, bus = cursor_adapter
        received = []
        bus.event_received.connect(lambda e: received.append(e))
        with patch("adapters.cursor._get_cursor_window_titles", return_value=[]):
            adapter.check()
        assert len(received) == 0
        assert adapter._waiting is False

    def test_attention_emits_waiting(self, cursor_adapter):
        adapter, bus = cursor_adapter
        received = []
        bus.event_received.connect(lambda e: received.append(e))
        with patch("adapters.cursor._get_cursor_window_titles", return_value=["Cursor - needs attention"]):
            adapter.check()
        assert len(received) == 1
        assert received[0].event_type == EventType.WAITING
        assert adapter._waiting is True

    def test_no_duplicate_waiting(self, cursor_adapter):
        adapter, bus = cursor_adapter
        received = []
        bus.event_received.connect(lambda e: received.append(e))
        with patch("adapters.cursor._get_cursor_window_titles", return_value=["Cursor - needs attention"]):
            adapter.check()
            adapter.check()  # 第二次不应重复发射
        assert len(received) == 1

    def test_attention_gone_emits_completed(self, cursor_adapter):
        adapter, bus = cursor_adapter
        received = []
        bus.event_received.connect(lambda e: received.append(e))
        with patch("adapters.cursor._get_cursor_window_titles", return_value=["Cursor - needs attention"]):
            adapter.check()
        with patch("adapters.cursor._get_cursor_window_titles", return_value=[]):
            adapter.check()
        assert len(received) == 2
        assert received[1].event_type == EventType.COMPLETED
        assert adapter._waiting is False

    def test_exception_silent(self, cursor_adapter):
        adapter, bus = cursor_adapter
        with patch("adapters.cursor._get_cursor_window_titles", side_effect=Exception("ctypes error")):
            adapter.check()  # 不应抛异常
        assert adapter._waiting is False

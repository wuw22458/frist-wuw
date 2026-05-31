"""AgentEvent + EventType 单元测试."""

import time

from events import AgentEvent, EventType


class TestEventType:
    def test_values(self):
        assert EventType.WAITING == 'waiting'
        assert EventType.COMPLETED == 'completed'
        assert EventType.ERROR == 'error'
        assert EventType.INFO == 'info'

    def test_string_comparison(self):
        assert EventType.WAITING == 'waiting'
        assert EventType.WAITING == 'waiting'


class TestAgentEvent:
    def test_construct_with_enum(self):
        e = AgentEvent('test', EventType.WAITING, 'msg')
        assert e.event_type == 'waiting'

    def test_construct_with_string(self):
        e = AgentEvent('test', 'waiting', 'msg')
        assert e.event_type == 'waiting'

    def test_timestamp_default(self):
        before = time.time()
        e = AgentEvent('test', 'info', 'msg')
        after = time.time()
        assert before <= e.timestamp <= after

    def test_metadata_default(self):
        e = AgentEvent('test', 'info', 'msg')
        assert e.metadata == {}

    def test_metadata_custom(self):
        e = AgentEvent('test', 'info', 'msg', metadata={'k': 'v'})
        assert e.metadata == {'k': 'v'}

    def test_is_waiting(self):
        assert AgentEvent('t', 'waiting', 'm').is_waiting
        assert not AgentEvent('t', 'completed', 'm').is_waiting
        assert not AgentEvent('t', 'error', 'm').is_waiting
        assert not AgentEvent('t', 'info', 'm').is_waiting

    def test_is_completed(self):
        assert AgentEvent('t', 'completed', 'm').is_completed
        assert not AgentEvent('t', 'waiting', 'm').is_completed

    def test_is_error(self):
        assert AgentEvent('t', 'error', 'm').is_error
        assert not AgentEvent('t', 'info', 'm').is_error

    def test_unknown_type_all_false(self):
        e = AgentEvent('t', 'something_else', 'm')
        assert not e.is_waiting
        assert not e.is_completed
        assert not e.is_error

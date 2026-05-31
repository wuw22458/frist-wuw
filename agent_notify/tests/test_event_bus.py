"""EventBus 中央事件总线单元测试."""

from events import AgentEvent, EventType


class TestEventBus:
    def test_get_bus_singleton(self, qapp):
        from event_bus import get_bus, reset_bus

        reset_bus()
        bus1 = get_bus()
        bus2 = get_bus()
        assert bus1 is bus2
        reset_bus()

    def test_reset_bus(self, qapp):
        from event_bus import get_bus, reset_bus

        reset_bus()
        bus1 = get_bus()
        reset_bus()
        bus2 = get_bus()
        assert bus1 is not bus2
        reset_bus()

    def test_event_received_signal(self, qapp):
        from event_bus import get_bus, reset_bus

        reset_bus()
        bus = get_bus()
        received = []
        bus.event_received.connect(lambda e: received.append(e))
        event = AgentEvent('test', EventType.WAITING, 'hello')
        bus.event_received.emit(event)
        assert len(received) == 1
        assert received[0].agent_id == 'test'
        assert received[0].message == 'hello'
        reset_bus()

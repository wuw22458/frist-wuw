"""log.py 测试.

覆盖: get_logger.
"""

# ── get_logger 测试 ─────────────────────────────────────────────────


class TestGetLogger:
    """Logger 获取测试."""

    def test_returns_logger_with_correct_name(self):
        from log import get_logger

        logger = get_logger('test_module')
        assert logger.name == 'agent_notify.test_module'

    def test_returns_same_logger_on_repeat_call(self):
        from log import get_logger

        logger1 = get_logger('test_same')
        logger2 = get_logger('test_same')
        assert logger1 is logger2

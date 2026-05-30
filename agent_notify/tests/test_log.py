"""log.py 测试。

覆盖: check_crash_log、get_logger、_crash_hook。
"""

from pathlib import Path
from unittest.mock import patch

# ── check_crash_log 测试 ────────────────────────────────────────────


class TestCheckCrashLog:
    """崩溃日志检测测试。"""

    def test_no_crash_log(self, tmp_path):
        crash_file = tmp_path / "crash.log"
        with patch("log._CRASH_FILE", crash_file):
            from log import check_crash_log

            assert check_crash_log() is None

    def test_returns_content_and_deletes(self, tmp_path):
        crash_file = tmp_path / "crash.log"
        crash_file.write_text("Traceback: test error", encoding="utf-8")

        with patch("log._CRASH_FILE", crash_file):
            from log import check_crash_log

            result = check_crash_log()
            assert result == "Traceback: test error"
            assert not crash_file.exists()

    def test_long_content_truncated(self, tmp_path):
        crash_file = tmp_path / "crash.log"
        long_content = "x" * 1000
        crash_file.write_text(long_content, encoding="utf-8")

        with patch("log._CRASH_FILE", crash_file):
            from log import check_crash_log

            result = check_crash_log()
            assert len(result) == 500
            assert result == "x" * 500

    def test_empty_file(self, tmp_path):
        crash_file = tmp_path / "crash.log"
        crash_file.write_text("", encoding="utf-8")

        with patch("log._CRASH_FILE", crash_file):
            from log import check_crash_log

            result = check_crash_log()
            # 空文件 strip 后为空字符串，应返回 None
            assert result is None

    def test_whitespace_only_file(self, tmp_path):
        crash_file = tmp_path / "crash.log"
        crash_file.write_text("   \n  ", encoding="utf-8")

        with patch("log._CRASH_FILE", crash_file):
            from log import check_crash_log

            result = check_crash_log()
            assert result is None

    def test_read_error_returns_none(self, tmp_path):
        crash_file = tmp_path / "crash.log"
        crash_file.write_text("error", encoding="utf-8")

        with (
            patch("log._CRASH_FILE", crash_file),
            patch.object(Path, "read_text", side_effect=OSError("permission denied")),
        ):
            from log import check_crash_log

            result = check_crash_log()
            assert result is None


# ── get_logger 测试 ─────────────────────────────────────────────────


class TestGetLogger:
    """Logger 获取测试。"""

    def test_returns_logger_with_correct_name(self):
        from log import get_logger

        logger = get_logger("test_module")
        assert logger.name == "agent_notify.test_module"

    def test_returns_same_logger_on_repeat_call(self):
        from log import get_logger

        logger1 = get_logger("test_same")
        logger2 = get_logger("test_same")
        assert logger1 is logger2

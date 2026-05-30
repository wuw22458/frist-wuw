"""crash_reporter.py 测试。

覆盖: write_crash_report、has_crash_report、read_crash_report、clear_crash_report。
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest


class TestCrashReporter:
    """崩溃报告功能测试。"""

    def test_no_crash_report(self, tmp_path):
        with patch("crash_reporter.CRASH_LOG", tmp_path / "crash.log"):
            from crash_reporter import has_crash_report

            assert has_crash_report() is False

    def test_write_and_read_crash_report(self, tmp_path):
        crash_file = tmp_path / "crash.log"
        with patch("crash_reporter.CRASH_LOG", crash_file):
            from crash_reporter import has_crash_report, read_crash_report, write_crash_report

            # write_crash_report 需要真实的异常对象
            try:
                raise ValueError("test error")
            except ValueError:
                exc_type, exc_value, exc_tb = sys.exc_info()
                write_crash_report(exc_type, exc_value, exc_tb)

            assert has_crash_report() is True

            content = read_crash_report()
            assert "ValueError" in content
            assert "test error" in content

    def test_clear_crash_report(self, tmp_path):
        crash_file = tmp_path / "crash.log"
        crash_file.write_text("old crash", encoding="utf-8")

        with patch("crash_reporter.CRASH_LOG", crash_file):
            from crash_reporter import clear_crash_report, has_crash_report

            assert has_crash_report() is True
            clear_crash_report()
            assert has_crash_report() is False

    def test_read_returns_none_when_no_file(self, tmp_path):
        with patch("crash_reporter.CRASH_LOG", tmp_path / "crash.log"):
            from crash_reporter import read_crash_report

            assert read_crash_report() is None

    def test_rotation_max_blocks(self, tmp_path):
        """写入多个崩溃报告时，保留最新的。"""
        crash_file = tmp_path / "crash.log"
        with patch("crash_reporter.CRASH_LOG", crash_file):
            from crash_reporter import read_crash_report, write_crash_report

            # 写入 3 个报告
            for i in range(3):
                try:
                    raise ValueError(f"error #{i}")
                except ValueError:
                    exc_type, exc_value, exc_tb = sys.exc_info()
                    write_crash_report(exc_type, exc_value, exc_tb)

            content = read_crash_report()
            # 最新的报告应该包含 error #2
            assert "error #2" in content

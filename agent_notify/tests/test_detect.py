"""各 adapter 的 detect() 方法单元测试。"""

import pytest
from unittest.mock import patch, MagicMock


class TestClaudeCodeDetect:
    def test_found(self):
        with patch("shutil.which", return_value="/usr/bin/claude"):
            from adapters.claude_code import ClaudeCodeAdapter
            assert ClaudeCodeAdapter.detect() is True

    def test_not_found(self):
        with patch("shutil.which", return_value=None):
            from adapters.claude_code import ClaudeCodeAdapter
            assert ClaudeCodeAdapter.detect() is False


class TestAiderDetect:
    def test_found(self):
        with patch("shutil.which", return_value="/usr/bin/aider"):
            from adapters.aider import AiderAdapter
            assert AiderAdapter.detect() is True

    def test_not_found(self):
        with patch("shutil.which", return_value=None):
            from adapters.aider import AiderAdapter
            assert AiderAdapter.detect() is False


class TestCursorDetect:
    def test_which_found(self):
        with patch("shutil.which", return_value="/usr/bin/cursor"):
            from adapters.cursor import CursorAdapter
            assert CursorAdapter.detect() is True

    def test_which_not_found_path_exists(self):
        with patch("shutil.which", return_value=None), \
             patch("pathlib.Path.exists", return_value=True):
            from adapters.cursor import CursorAdapter
            assert CursorAdapter.detect() is True

    def test_which_not_found_no_path(self):
        with patch("shutil.which", return_value=None), \
             patch("pathlib.Path.exists", return_value=False):
            from adapters.cursor import CursorAdapter
            assert CursorAdapter.detect() is False

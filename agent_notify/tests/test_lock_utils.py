"""lock_utils.py 进程锁单元测试。"""

import os
from unittest.mock import patch

import pytest


@pytest.fixture()
def lock_env(tmp_path, monkeypatch):
    """将 LOCK_FILE 指向临时目录。"""
    import constants
    lock_file = tmp_path / ".lock"
    monkeypatch.setattr(constants, "LOCK_FILE", lock_file)
    import lock_utils
    monkeypatch.setattr(lock_utils, "LOCK_FILE", lock_file)
    return lock_file


class TestIsProcessRunning:
    @patch("ctypes.windll.kernel32.OpenProcess")
    @patch("ctypes.windll.kernel32.CloseHandle")
    def test_running(self, mock_close, mock_open):
        mock_open.return_value = 1234  # non-zero handle
        from lock_utils import is_process_running
        assert is_process_running(999) is True
        mock_close.assert_called_once_with(1234)

    @patch("ctypes.windll.kernel32.OpenProcess")
    def test_not_running(self, mock_open):
        mock_open.return_value = 0  # zero handle = process not found
        from lock_utils import is_process_running
        assert is_process_running(999) is False

    @patch("ctypes.windll.kernel32.OpenProcess", side_effect=OSError("access denied"))
    def test_os_error(self, mock_open):
        from lock_utils import is_process_running
        assert is_process_running(999) is False


class TestCheckSingleInstance:
    @patch("lock_utils.is_process_running", return_value=False)
    def test_no_lock_file(self, mock_running, lock_env):
        from lock_utils import check_single_instance
        result = check_single_instance()
        assert result is True
        assert lock_env.exists()
        assert lock_env.read_text() == str(os.getpid())

    @patch("lock_utils.is_process_running", return_value=True)
    def test_active_pid(self, mock_running, lock_env):
        lock_env.write_text("12345")
        from lock_utils import check_single_instance
        result = check_single_instance()
        assert result is False

    @patch("lock_utils.is_process_running", return_value=False)
    def test_stale_pid(self, mock_running, lock_env):
        lock_env.write_text("99999")
        from lock_utils import check_single_instance
        result = check_single_instance()
        assert result is True
        assert lock_env.read_text() == str(os.getpid())

    def test_corrupt_lock_file(self, lock_env):
        lock_env.write_text("not_a_pid")
        from lock_utils import check_single_instance
        result = check_single_instance()
        assert result is True


class TestCleanupLock:
    def test_deletes_file(self, lock_env):
        lock_env.write_text("123")
        from lock_utils import cleanup_lock
        cleanup_lock()
        assert not lock_env.exists()

    def test_no_file(self, lock_env):
        from lock_utils import cleanup_lock
        cleanup_lock()  # 不应抛异常

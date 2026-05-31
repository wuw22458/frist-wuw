"""lock_utils.py 进程锁单元测试。"""

from unittest.mock import MagicMock, patch

import pytest


class TestIsProcessRunning:
    @patch("ctypes.windll.kernel32.OpenProcess")
    @patch("ctypes.windll.kernel32.WaitForSingleObject")
    @patch("ctypes.windll.kernel32.CloseHandle")
    def test_running(self, mock_close, mock_wait, mock_open):
        mock_open.return_value = 1234  # non-zero handle
        mock_wait.return_value = 258  # WAIT_TIMEOUT = 进程存活
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

    @patch("ctypes.windll.kernel32.OpenProcess")
    @patch("ctypes.windll.kernel32.WaitForSingleObject")
    @patch("ctypes.windll.kernel32.CloseHandle")
    def test_process_terminated(self, mock_close, mock_wait, mock_open):
        mock_open.return_value = 1234
        mock_wait.return_value = 0  # WAIT_OBJECT_0 = 进程已终止
        from lock_utils import is_process_running

        assert is_process_running(999) is False


class TestCheckSingleInstance:
    @patch("ctypes.windll.kernel32.CreateMutexW")
    @patch("ctypes.windll.kernel32.GetLastError")
    def test_first_instance(self, mock_error, mock_create):
        """测试首次启动（创建 Mutex 成功）。"""
        mock_create.return_value = 1234  # 有效句柄
        mock_error.return_value = 0  # ERROR_SUCCESS
        from lock_utils import check_single_instance

        result = check_single_instance()
        assert result is True

    @patch("ctypes.windll.kernel32.CreateMutexW")
    @patch("ctypes.windll.kernel32.GetLastError")
    @patch("ctypes.windll.kernel32.CloseHandle")
    def test_already_running(self, mock_close, mock_error, mock_create):
        """测试已有实例在运行（Mutex 已存在）。"""
        mock_create.return_value = 1234
        mock_error.return_value = 183  # ERROR_ALREADY_EXISTS
        from lock_utils import check_single_instance

        result = check_single_instance()
        assert result is False
        mock_close.assert_called_once_with(1234)

    @patch("ctypes.windll.kernel32.CreateMutexW")
    def test_create_mutex_failed(self, mock_create):
        """测试 CreateMutexW 失败（降级处理）。"""
        mock_create.return_value = 0  # 失败
        from lock_utils import check_single_instance

        result = check_single_instance()
        assert result is True  # 降级允许启动

    @patch("ctypes.windll.kernel32.CreateMutexW", side_effect=Exception("test"))
    def test_exception_handling(self, mock_create):
        """测试异常处理（降级允许启动）。"""
        from lock_utils import check_single_instance

        result = check_single_instance()
        assert result is True


class TestCleanupLock:
    @patch("ctypes.windll.kernel32.CloseHandle")
    def test_cleanup_with_handle(self, mock_close):
        """测试有 Mutex 句柄时的清理。"""
        import lock_utils
        lock_utils._mutex_handle = 1234

        lock_utils.cleanup_lock()
        mock_close.assert_called_once_with(1234)
        assert lock_utils._mutex_handle is None

    def test_cleanup_without_handle(self):
        """测试无 Mutex 句柄时的清理（不应抛异常）。"""
        import lock_utils
        lock_utils._mutex_handle = None

        lock_utils.cleanup_lock()  # 不应抛异常

    @patch("ctypes.windll.kernel32.CloseHandle", side_effect=Exception("test"))
    def test_cleanup_exception_handling(self, mock_close):
        """测试清理时的异常处理。"""
        import lock_utils
        lock_utils._mutex_handle = 1234

        lock_utils.cleanup_lock()  # 不应抛异常
        assert lock_utils._mutex_handle is None

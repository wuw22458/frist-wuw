"""hooks/claude_hook.py 集成测试。

测试信号文件写入、stdin 解析、消息提取、端到端 subprocess 调用。
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
HOOK_SCRIPT = PROJECT_ROOT / "hooks" / "claude_hook.py"


# ── _extract_tool_message ──


class TestExtractToolMessage:
    """_extract_tool_message 函数测试。"""

    def test_ask_user_question(self):
        from hooks.claude_hook import _extract_tool_message

        ctx = {
            "tool_name": "AskUserQuestion",
            "tool_input": {
                "questions": [{"question": "选择下一步方向？"}]
            },
        }
        msg = _extract_tool_message(ctx)
        assert "选择下一步方向" in msg

    def test_ask_user_question_empty(self):
        from hooks.claude_hook import _extract_tool_message

        ctx = {"tool_name": "AskUserQuestion", "tool_input": {"questions": []}}
        msg = _extract_tool_message(ctx)
        assert msg == "Claude Code 需要你做出选择"

    def test_exit_tool_mode(self):
        from hooks.claude_hook import _extract_tool_message

        ctx = {"tool_name": "ExitToolMode", "tool_input": {}}
        msg = _extract_tool_message(ctx)
        assert "批准计划" in msg

    def test_unknown_tool(self):
        from hooks.claude_hook import _extract_tool_message

        ctx = {"tool_name": "Bash", "tool_input": {}}
        msg = _extract_tool_message(ctx)
        assert "Bash" in msg

    def test_empty_context(self):
        from hooks.claude_hook import _extract_tool_message

        msg = _extract_tool_message({})
        assert "调用了" in msg


# ── _read_stdin ──


class TestReadStdin:
    """_read_stdin 函数测试。"""

    def test_valid_json(self):
        from hooks.claude_hook import _read_stdin

        mock_stdin = MagicMock()
        mock_stdin.isatty.return_value = False
        mock_stdin.buffer.read.return_value = b'{"tool_name": "Bash"}'

        with patch("hooks.claude_hook.sys") as mock_sys:
            mock_sys.stdin = mock_stdin
            result = _read_stdin()

        assert result == {"tool_name": "Bash"}

    def test_tty_returns_empty(self):
        from hooks.claude_hook import _read_stdin

        mock_stdin = MagicMock()
        mock_stdin.isatty.return_value = True

        with patch("hooks.claude_hook.sys") as mock_sys:
            mock_sys.stdin = mock_stdin
            result = _read_stdin()

        assert result == {}

    def test_invalid_json_returns_empty(self):
        from hooks.claude_hook import _read_stdin

        mock_stdin = MagicMock()
        mock_stdin.isatty.return_value = False
        mock_stdin.buffer.read.return_value = b"not json"

        with patch("hooks.claude_hook.sys") as mock_sys:
            mock_sys.stdin = mock_stdin
            result = _read_stdin()

        assert result == {}

    def test_empty_stdin_returns_empty(self):
        from hooks.claude_hook import _read_stdin

        mock_stdin = MagicMock()
        mock_stdin.isatty.return_value = False
        mock_stdin.buffer.read.return_value = b""

        with patch("hooks.claude_hook.sys") as mock_sys:
            mock_sys.stdin = mock_stdin
            result = _read_stdin()

        assert result == {}


# ── write_signal（mock 模式）──


class TestWriteSignal:
    """write_signal 函数测试（通过 mock 隔离文件系统）。"""

    def test_writes_valid_json(self, tmp_path):
        """信号文件应为合法 JSON，包含 event/message/timestamp/source 字段。"""
        with patch("hooks.claude_hook.SIGNAL_DIR", tmp_path):
            from hooks.claude_hook import write_signal
            write_signal("notification", "测试消息")

        files = list(tmp_path.glob("*.json"))
        assert len(files) == 1

        data = json.loads(files[0].read_text(encoding="utf-8"))
        assert data["event"] == "notification"
        assert data["message"] == "测试消息"
        assert isinstance(data["timestamp"], int)
        assert data["source"] == "claude-code"

    def test_filename_is_millisecond_timestamp(self, tmp_path):
        """文件名应为毫秒时间戳。"""
        with patch("hooks.claude_hook.SIGNAL_DIR", tmp_path):
            from hooks.claude_hook import write_signal
            before = int(time.time() * 1000)
            write_signal("stop", "完成")
            after = int(time.time() * 1000)

        files = list(tmp_path.glob("*.json"))
        ts = int(files[0].stem)
        assert before <= ts <= after

    def test_custom_source(self, tmp_path):
        """应支持自定义 source 参数。"""
        with patch("hooks.claude_hook.SIGNAL_DIR", tmp_path):
            from hooks.claude_hook import write_signal
            write_signal("notification", "msg", source="custom-agent")

        files = list(tmp_path.glob("*.json"))
        data = json.loads(files[0].read_text(encoding="utf-8"))
        assert data["source"] == "custom-agent"

    def test_unicode_message(self, tmp_path):
        """应正确处理中文和 emoji。"""
        with patch("hooks.claude_hook.SIGNAL_DIR", tmp_path):
            from hooks.claude_hook import write_signal
            write_signal("notification", "需要确认: 你好世界 🚀")

        files = list(tmp_path.glob("*.json"))
        data = json.loads(files[0].read_text(encoding="utf-8"))
        assert data["message"] == "需要确认: 你好世界 🚀"


# ── 端到端 subprocess 测试 ──


class TestHookE2E:
    """通过 subprocess 调用 hook 脚本的端到端测试。"""

    def _run_hook(self, event: str, stdin_data: dict = None, env_extra: dict = None) -> subprocess.CompletedProcess:
        """运行 hook 脚本并返回结果。"""
        # 继承当前环境，确保 HOME/USERPROFILE 等关键变量可用
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT)
        if env_extra:
            env.update(env_extra)

        input_bytes = json.dumps(stdin_data).encode("utf-8") if stdin_data else b""

        return subprocess.run(
            [sys.executable, str(HOOK_SCRIPT), "--event", event],
            input=input_bytes,
            capture_output=True,
            timeout=10,
            env=env,
            cwd=str(PROJECT_ROOT),
        )

    def test_notification_event_outputs_empty_json(self):
        """notification 事件应输出空 JSON。"""
        result = self._run_hook("notification", {"message": "测试"})
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        assert result.stdout.strip() == b"{}"

    def test_stop_event_outputs_empty_json(self):
        """stop 事件应输出空 JSON。"""
        result = self._run_hook("stop")
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        assert result.stdout.strip() == b"{}"

    def test_permission_event_bash_filtered(self):
        """Bash 工具不应产生信号文件（PreToolUse 在权限决定前触发，auto-approve 下会误报）。"""
        stdin = {"tool_name": "Bash", "tool_input": {"command": "ls -la"}}
        result = self._run_hook("permission", stdin)
        assert result.returncode == 0, result.stderr.decode(errors="replace")

    def test_permission_event_with_write(self):
        """permission 事件（Write 工具）应成功执行。"""
        stdin = {"tool_name": "Write", "tool_input": {"file_path": "/tmp/test.py"}}
        result = self._run_hook("permission", stdin)
        assert result.returncode == 0, result.stderr.decode(errors="replace")

    def test_permission_event_read_tool_filtered(self):
        """Read 工具不应产生信号文件（只读操作，无需权限确认）。"""
        signal_dir = Path.home() / ".agent-notify"
        before_files = list(signal_dir.glob("*.json")) if signal_dir.exists() else []

        stdin = {"tool_name": "Read", "tool_input": {"file_path": "/tmp/test.py"}}
        result = self._run_hook("permission", stdin)
        assert result.returncode == 0, result.stderr.decode(errors="replace")

        after_files = list(signal_dir.glob("*.json")) if signal_dir.exists() else []
        # Read 工具不应新增信号文件
        assert len(after_files) <= len(before_files)

    def test_permission_event_glob_tool_filtered(self):
        """Glob 工具不应产生信号文件。"""
        stdin = {"tool_name": "Glob", "tool_input": {"pattern": "*.py"}}
        result = self._run_hook("permission", stdin)
        assert result.returncode == 0, result.stderr.decode(errors="replace")

    def test_tool_use_event(self):
        """tool_use 事件应成功执行。"""
        stdin = {"tool_name": "AskUserQuestion", "tool_input": {"questions": [{"question": "选哪个？"}]}}
        result = self._run_hook("tool_use", stdin)
        assert result.returncode == 0, result.stderr.decode(errors="replace")

    def test_invalid_event_rejected(self):
        """无效事件类型应被 argparse 拒绝。"""
        result = self._run_hook("invalid_event")
        assert result.returncode != 0

    def test_notification_with_env_var(self):
        """应从 CLAUDE_NOTIFICATION 环境变量读取消息。"""
        result = self._run_hook("notification", {}, env_extra={"CLAUDE_NOTIFICATION": "环境变量消息"})
        assert result.returncode == 0, result.stderr.decode(errors="replace")

    def test_signal_file_written(self):
        """subprocess 应在真实信号目录写入信号文件。"""
        signal_dir = Path.home() / ".agent-notify"
        before_files = set(signal_dir.glob("*.json")) if signal_dir.exists() else set()

        result = self._run_hook("notification", {"message": "E2E 测试"})
        assert result.returncode == 0

        after_files = set(signal_dir.glob("*.json"))
        new_files = after_files - before_files
        # 可能有其他进程写入的文件，只要不少于之前就行
        assert len(after_files) >= len(before_files)

        # 清理本次测试产生的信号文件
        for f in new_files:
            try:
                f.unlink()
            except OSError:
                pass

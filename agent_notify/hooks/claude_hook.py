#!/usr/bin/env python3
"""Claude Code hook 脚本

由 Claude Code hooks 系统调用。写信号文件到 ~/.agent-notify/，
触发 PySide6 托盘应用的通知。

用法：
  python claude_hook.py --event notification
  python claude_hook.py --event stop
  python claude_hook.py --event tool_use

stdin 接收 Claude Code 传入的 JSON 上下文。
环境变量 CLAUDE_NOTIFICATION 包含通知消息（Notification hook）。
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# 将项目根目录加入 sys.path，以便导入共享模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from constants import SIGNAL_DIR
from lock_utils import is_process_running, LOCK_FILE

APP_SCRIPT = Path(__file__).parent.parent / "main.py"
DEBUG_LOG = SIGNAL_DIR / "hook_debug.log"


def _debug(msg: str) -> None:
    """写调试日志（仅在 SIGNAL_DIR 已存在时写入）。"""
    try:
        SIGNAL_DIR.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except OSError:
        pass


def _read_stdin() -> dict:
    """读取 stdin 中的 JSON 数据（非阻塞，最多读取 64KB）。

    Claude Code 通过 stdin 传入 hook 上下文 JSON。
    如果 stdin 不可读（控制终端或无数据），立即返回空字典避免阻塞。
    """
    raw = ""
    try:
        if sys.stdin.isatty():
            _debug("stdin is a tty,跳过读取")
            return {}
        raw = sys.stdin.buffer.read(65536).decode("utf-8", errors="replace").strip()
    except (OSError, UnicodeDecodeError) as e:
        _debug(f"stdin 读取异常: {e}")
        return {}
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        _debug(f"stdin JSON 解析失败: {e} | raw={raw[:200]}")
        return {}


def write_signal(event: str, message: str, source: str = "claude-code") -> None:
    """写信号文件到信号目录，由托盘应用轮询检测。

    文件名使用毫秒时间戳，保证唯一且有序。格式:
    {"event": str, "message": str, "timestamp": int, "source": str}

    Args:
        event: 事件类型，"notification" 或 "stop"。
        message: 显示给用户的消息文本。
        source: 事件来源标识，默认 "claude-code"。
    """
    SIGNAL_DIR.mkdir(parents=True, exist_ok=True)
    ts = int(time.time() * 1000)
    signal_file = SIGNAL_DIR / f"{ts}.json"
    data = {
        "event": event,
        "message": message,
        "timestamp": ts,
        "source": source,
    }
    signal_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    _debug(f"信号已写入: {signal_file.name} event={event} msg={message[:80]}")


def ensure_app_running() -> bool:
    """如果托盘应用未运行，则后台启动它。

    通过锁文件中的 PID 判断是否已有实例。启动后轮询锁文件最多 2 秒。

    Returns:
        True 表示托盘应用已在运行或成功启动，False 表示启动失败。
    """
    try:
        if LOCK_FILE.exists():
            pid = int(LOCK_FILE.read_text().strip())
            if is_process_running(pid):
                _debug(f"托盘应用已在运行, PID={pid}")
                return True
    except (ValueError, OSError):
        pass

    _debug("托盘应用未运行，正在启动...")
    try:
        subprocess.Popen(
            [sys.executable, str(APP_SCRIPT)],
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
        )
        for _ in range(10):
            if LOCK_FILE.exists():
                try:
                    pid = int(LOCK_FILE.read_text().strip())
                    if pid > 0:
                        _debug(f"托盘应用已启动, PID={pid}")
                        return True
                except (ValueError, OSError):
                    pass
            time.sleep(0.2)
        _debug("启动超时: 锁文件未出现")
    except OSError as e:
        _debug(f"启动失败: {e}")
        return False
    return False


def _extract_tool_message(stdin_context: dict) -> str:
    """从 PreToolUse hook 的 stdin 上下文中提取消息文本。

    PreToolUse stdin 格式:
      {"tool_name": "AskUserQuestion", "tool_input": {"questions": [...]}}
      {"tool_name": "ExitToolMode", "tool_input": {"allowedPrompts": [...]}}
    """
    tool_name = stdin_context.get("tool_name", "")
    tool_input = stdin_context.get("tool_input", {})

    if tool_name == "AskUserQuestion":
        questions = tool_input.get("questions", [])
        if questions:
            first_q = questions[0].get("question", "")
            if first_q:
                return f"需要选择: {first_q}"
        return "Claude Code 需要你做出选择"

    if tool_name == "ExitToolMode":
        return "Claude Code 请求批准计划"

    return f"Claude Code 调用了 {tool_name}"


def main() -> None:
    """入口函数 — 解析事件类型，生成消息，写信号文件，确保托盘运行。

    stdin 接收 Claude Code 传入的 JSON 上下文，格式为:
      {"hook_event_name": "Notification", "message": "...", "session_id": "...", ...}
      {"hook_event_name": "Stop", "stop_hook_active": false, "session_id": "...", ...}

    环境变量 CLAUDE_NOTIFICATION 提供备用通知消息。
    输出空 JSON，不拦截 Claude Code 的后续操作。
    """
    _debug(f"hook 启动, args={sys.argv}")

    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True, choices=["notification", "stop", "tool_use"])
    args = parser.parse_args()

    # 读取 stdin（Claude Code 传入的 hook 上下文）
    stdin_context = _read_stdin()
    _debug(f"stdin 解析结果: keys={list(stdin_context.keys())}")

    # 从 stdin 或环境变量提取消息
    if args.event == "notification":
        notif_type = stdin_context.get("notification_type", "")
        message = (
            stdin_context.get("message")
            or os.environ.get("CLAUDE_NOTIFICATION")
            or "Claude Code 需要你的确认"
        )
        if notif_type == "permission_prompt":
            message = f"需要确认: {message}" if message else "Claude Code 需要工具权限"
    elif args.event == "tool_use":
        message = _extract_tool_message(stdin_context)
    else:
        message = "Claude Code 任务已完成"

    # 写信号文件
    write_signal(args.event, message)

    # 确保托盘应用在运行
    ensure_app_running()

    # 输出空 JSON（不拦截操作）
    print("{}")
    _debug("hook 完成")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        _debug(f"未捕获异常: {e}")
        print("{}")

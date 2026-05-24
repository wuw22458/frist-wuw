#!/usr/bin/env python3
"""Claude Code hook 脚本

由 Claude Code hooks 系统调用。写信号文件到 ~/.agent-notify/，
触发 PySide6 托盘应用的通知。

用法：
  python claude_hook.py --event notification
  python claude_hook.py --event stop
  python claude_hook.py --event tool_use
  python claude_hook.py --event permission

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
from log import get_logger

logger = get_logger("hook")

APP_SCRIPT = Path(__file__).parent.parent / "main.py"


def _read_stdin() -> dict:
    """读取 stdin 中的 JSON 数据（非阻塞，最多读取 64KB）。

    Claude Code 通过 stdin 传入 hook 上下文 JSON。
    如果 stdin 不可读（控制终端或无数据），立即返回空字典避免阻塞。
    """
    raw = ""
    try:
        if sys.stdin.isatty():
            logger.debug("stdin is a tty，跳过读取")
            return {}
        raw = sys.stdin.buffer.read(65536).decode("utf-8", errors="replace").strip()
    except (OSError, UnicodeDecodeError) as e:
        logger.warning("stdin 读取异常: %s", e)
        return {}
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning("stdin JSON 解析失败: %s | raw=%s", e, raw[:200])
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
    logger.info("信号已写入: %s event=%s msg=%s", signal_file.name, event, message[:80])


def ensure_app_running() -> None:
    """如果托盘应用未运行，则后台启动它（非阻塞）。

    通过锁文件中的 PID 判断是否已有实例。启动后立即返回，不等待结果。
    """
    try:
        if LOCK_FILE.exists():
            pid = int(LOCK_FILE.read_text().strip())
            if is_process_running(pid):
                logger.debug("托盘应用已在运行, PID=%d", pid)
                return
    except (ValueError, OSError):
        pass

    logger.info("托盘应用未运行，正在启动...")
    try:
        subprocess.Popen(
            [sys.executable, str(APP_SCRIPT)],
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
        )
    except OSError as e:
        logger.error("启动托盘应用失败: %s", e)


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
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True, choices=["notification", "stop", "tool_use", "permission"])
    args = parser.parse_args()

    logger.debug("hook 启动, event=%s, args=%s", args.event, sys.argv)

    # 读取 stdin（Claude Code 传入的 hook 上下文）
    stdin_context = _read_stdin()
    logger.debug("stdin 解析结果: keys=%s", list(stdin_context.keys()))

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
    elif args.event == "permission":
        tool_name = stdin_context.get("tool_name", "")
        # 只对写操作工具通知。Bash 不在白名单中，因为 PreToolUse hook 在权限决定前触发，
        # auto-approve 模式下 Bash 命令不会真正需要确认，但 hook 仍然会触发。
        _PERMISSION_TOOLS = {"Write", "Edit", "NotebookEdit"}
        if tool_name not in _PERMISSION_TOOLS:
            logger.debug("跳过工具: %s (permission_mode=%s)", tool_name, stdin_context.get("permission_mode"))
            print("{}")
            return
        tool_input = stdin_context.get("tool_input", {})
        if tool_name in ("Write", "Edit"):
            path = tool_input.get("file_path", "")
            message = f"需要确认写入: {path}" if path else f"需要确认 {tool_name} 操作"
        else:
            message = f"需要确认: {tool_name}" if tool_name else "Claude Code 需要工具权限"
    else:
        message = "Claude Code 任务已完成"

    # 写信号文件
    write_signal(args.event, message)

    # 确保托盘应用在运行（非阻塞）
    ensure_app_running()

    # 输出空 JSON（不拦截操作）
    print("{}")
    logger.debug("hook 完成")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("未捕获异常: %s", e)
        print("{}")

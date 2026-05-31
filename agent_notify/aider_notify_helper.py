"""Aider 通知辅助脚本 — 配合 Aider 的 --notify-cmd 使用.

用法:
    aider --notify-cmd 'python "D:/1/agent_notify/aider_notify_helper.py"'

当 Aider 等待用户输入时,会执行此脚本写入信号文件,
AgentNotify 的 AiderAdapter 会检测到该信号并弹出通知.
"""

import json
import time
from pathlib import Path

SIGNAL_DIR = Path.home() / '.agent-notify'
SIGNAL_DIR.mkdir(parents=True, exist_ok=True)

data = {
    'event': 'waiting',
    'message': 'Aider 等待你的输入',
    'timestamp': int(time.time() * 1000),
    'source': 'aider',
}

signal_file = SIGNAL_DIR / f'aider_{int(time.time() * 1000)}.json'
signal_file.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')

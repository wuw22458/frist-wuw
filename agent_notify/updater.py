"""自动更新检查 — 后台查询 GitHub Releases API。"""

import json
import shutil
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from constants import SIGNAL_DIR, __version__
from log import get_logger

logger = get_logger("updater")

GITHUB_API = "https://api.github.com/repos/wuw22458/agent_notify/releases/latest"
REQUEST_TIMEOUT = 8

# 更新检查间隔（秒）
CHECK_INTERVAL = 3600 * 6  # 6 小时
# 上次检查时间戳文件
_LAST_CHECK_FILE = SIGNAL_DIR / ".last_update_check"


@dataclass
class UpdateInfo:
    available: bool
    latest_version: str = ""
    download_url: str = ""
    html_url: str = ""
    body: str = ""


def _parse_version(v: str) -> tuple[int, int, int]:
    """将 '1.2.0' 解析为 (1, 2, 0)，忽略前缀 'v' 和预发布后缀。"""
    v = v.lstrip("v").strip()
    parts = []
    for p in v.split("."):
        # 去除预发布后缀，如 "0-beta1" → "0"
        num = ""
        for ch in p:
            if ch.isdigit():
                num += ch
            else:
                break
        if num:
            parts.append(int(num))
        else:
            break
    # 规范化为 3 段
    while len(parts) < 3:
        parts.append(0)
    return (parts[0], parts[1], parts[2])


def check_update() -> UpdateInfo:
    """同步检查是否有新版本（阻塞，应在后台线程调用）。"""
    try:
        req = urllib.request.Request(
            GITHUB_API,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "agent-notify",
            },
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        logger.debug("更新检查失败: %s", e)
        return UpdateInfo(available=False)

    tag = data.get("tag_name", "")
    current = _parse_version(__version__)
    latest = _parse_version(tag)

    if latest > current:
        assets = data.get("assets", [])
        download = ""
        for a in assets:
            if a.get("name", "").endswith(".exe"):
                download = a.get("browser_download_url", "")
                break
        if not download:
            download = data.get("html_url", "")

        logger.info("发现新版本: %s → %s", __version__, tag)
        return UpdateInfo(
            available=True,
            latest_version=tag,
            download_url=download,
            html_url=data.get("html_url", ""),
            body=data.get("body", ""),
        )

    logger.debug("当前已是最新版本: %s", __version__)
    return UpdateInfo(available=False)


def should_check() -> bool:
    """判断是否应该检查更新（距上次检查超过 CHECK_INTERVAL）。"""
    if not _LAST_CHECK_FILE.exists():
        return True
    try:
        last = float(_LAST_CHECK_FILE.read_text().strip())
        return (time.time() - last) > CHECK_INTERVAL
    except (ValueError, OSError):
        return True


def mark_checked() -> None:
    """记录本次检查时间。"""
    SIGNAL_DIR.mkdir(parents=True, exist_ok=True)
    _LAST_CHECK_FILE.write_text(str(time.time()))


def download_and_replace(download_url: str) -> bool:
    """下载新版本并替换当前可执行文件。

    策略：
      1. 下载到临时文件
      2. 将当前 exe 重命名为 .old
      3. 移动新文件到原位置
      4. 提示用户重启

    Returns:
        True 如果下载成功，False 如果失败。
    """
    import sys

    current_exe = Path(sys.executable if getattr(sys, "frozen", False) else sys.argv[0])
    if not current_exe.exists():
        logger.error("无法定位当前可执行文件: %s", current_exe)
        return False

    try:
        logger.info("正在下载更新: %s", download_url)
        req = urllib.request.Request(
            download_url,
            headers={"User-Agent": "AgentNotify-Updater/1.0"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()

        tmp_dir = Path(tempfile.gettempdir())
        tmp_file = tmp_dir / f"agent-notify-{__version__}-update.exe"
        tmp_file.write_bytes(data)
        logger.info("下载完成: %s (%d bytes)", tmp_file, len(data))

        old_file = current_exe.with_suffix(".exe.old")
        if old_file.exists():
            old_file.unlink()
        shutil.move(str(current_exe), str(old_file))
        shutil.move(str(tmp_file), str(current_exe))

        logger.info("更新完成，旧文件备份: %s", old_file)
        return True

    except (urllib.error.URLError, OSError) as e:
        logger.error("更新失败: %s", e)
        return False


class UpdateChecker(QThread):
    """后台线程执行更新检查，完成后发射 result 信号。"""

    result = Signal(object)  # UpdateInfo

    def run(self):
        info = check_update()
        self.result.emit(info)

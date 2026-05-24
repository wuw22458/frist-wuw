"""Windows Toast 通知 + 多媒体声音播放。

Toast 通知通过 PowerShell 调用 Windows Runtime API。
声音播放使用 PySide6 QMediaPlayer，支持 WAV / MP3 等格式。
"""

import subprocess
import sys
from pathlib import Path

from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl

from log import get_logger

logger = get_logger("notification")

if getattr(sys, "frozen", False):
    _BASE_DIR = Path(sys._MEIPASS)
else:
    _BASE_DIR = Path(__file__).parent

RESOURCES_DIR = _BASE_DIR / "resources"

# 自动查找 resources 目录下第一个支持的音频文件作为默认提示音
_SUPPORTED = (".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac")


def _default_sound() -> Path | None:
    """查找 resources 目录下第一个受支持的音频文件。"""
    if RESOURCES_DIR.is_dir():
        for f in sorted(RESOURCES_DIR.iterdir()):
            if f.suffix.lower() in _SUPPORTED:
                return f
    return None

# 全局播放器（复用避免重复创建）
_player: QMediaPlayer | None = None
_audio: QAudioOutput | None = None


def _get_player() -> QMediaPlayer | None:
    """获取全局 QMediaPlayer 单例。错误状态自动重建。"""
    global _player, _audio
    if _player is not None:
        # 检测错误状态，自动重建
        if _player.error() != QMediaPlayer.Error.NoError:
            logger.warning("QMediaPlayer 错误状态 (%s)，重建播放器", _player.error())
            try:
                _player.setSource(QUrl())
                _player.deleteLater()
            except Exception:
                pass
            _player = None
            _audio = None
    if _player is None:
        try:
            _player = QMediaPlayer()
            _audio = QAudioOutput()
            _player.setAudioOutput(_audio)
            _audio.setVolume(0.8)
        except Exception as e:
            logger.error("QMediaPlayer 创建失败: %s", e)
            _player = None
            _audio = None
            return None
    return _player


def play_sound(sound_path: str = "") -> None:
    """播放提示音。支持 WAV / MP3 / FLAC 等格式。

    优先使用自定义路径，其次默认 notify.wav，文件不存在则静默跳过。

    Args:
        sound_path: 自定义音频文件路径，为空时使用默认 notify.wav。
    """
    path = sound_path if (sound_path and Path(sound_path).is_file()) else None

    if path is None:
        default = _default_sound()
        if default is not None:
            path = str(default)

    if path is None:
        logger.debug("无可用音频文件，跳过播放")
        return

    player = _get_player()
    if player is None:
        return

    try:
        player.setSource(QUrl.fromLocalFile(path))
        player.play()
        logger.debug("播放提示音: %s", path)
    except Exception as e:
        logger.error("播放提示音失败 (%s): %s", path, e)


def show_toast(title: str, message: str, source: str = "") -> None:
    """弹出 Windows 原生 toast 通知（非阻塞）。

    Args:
        title: 通知标题。
        message: 通知正文。
        source: 来源归属文字（可为空）。
    """
    source_line = f"<text placement='attribution'>{_escape_xml(source)}</text>" if source else ""
    ps_script = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$template = @"
<toast duration="short" scenario="reminder">
    <visual>
        <binding template="ToastGeneric">
            <text>{_escape_xml(title)}</text>
            <text>{_escape_xml(message)}</text>
            {source_line}
        </binding>
    </visual>
    <audio src="ms-winsoundevent:Notification.Looping.Alarm" silent="true"/>
</toast>
"@

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Agent Notify").Show($toast)
'''
    try:
        subprocess.Popen(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        logger.debug("Toast 通知已发送: %s — %s", title, message[:60])
    except FileNotFoundError:
        logger.error("PowerShell 不可用，无法发送 Toast 通知")
    except OSError as e:
        logger.error("Toast 通知发送失败: %s", e)


def _escape_xml(text: str) -> str:
    """转义 XML 特殊字符。"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def notify(title: str, message: str, sound: bool = True, source: str = "", sound_path: str = "") -> None:
    """发送通知（可选声音）。

    Args:
        title: 通知标题。
        message: 通知正文。
        sound: 是否播放提示音，默认 True。
        source: 来源归属文字。
        sound_path: 自定义音频文件路径。
    """
    logger.info("通知: [%s] %s (sound=%s, source=%s)", title, message[:80], sound, source)
    if sound:
        play_sound(sound_path)
    show_toast(title, message, source)

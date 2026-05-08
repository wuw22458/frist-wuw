import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

from storage import init_db, cleanup_expired
from clipboard_monitor import ClipboardMonitor
from ui.main_window import MainPanel


def create_tray_icon():
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#4A90D9"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(2, 2, 28, 28, 6, 6)
    painter.setPen(QColor("#FFFFFF"))
    painter.drawLine(10, 14, 22, 14)
    painter.drawLine(10, 18, 18, 18)
    painter.drawLine(10, 22, 20, 22)
    painter.end()
    return QIcon(pixmap)


def enable_autostart():
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "ClipboardHistory"
        if getattr(sys, "frozen", False):
            cmd = f'"{sys.executable}"'
        else:
            pythonw_path = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
            if not os.path.exists(pythonw_path):
                pythonw_path = sys.executable.replace("python.exe", "pythonw.exe")
            if not os.path.exists(pythonw_path):
                return
            cmd = f'"{pythonw_path}" "{os.path.abspath(__file__)}"'
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
    except Exception:
        pass


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ClipboardHistory")
    app.setQuitOnLastWindowClosed(False)

    font = QFont("Microsoft YaHei", 10)
    font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    app.setFont(font)

    init_db()
    cleanup_expired()

    panel = MainPanel()

    # 先创建 monitor，避免 lambda 引用未定义的变量
    monitor = ClipboardMonitor()
    monitor.start()

    tray = QSystemTrayIcon()
    tray.setIcon(create_tray_icon())
    tray.setToolTip("剪贴板历史")

    menu = QMenu()
    menu.addAction("显示面板").triggered.connect(lambda: panel.show_at_cursor())
    menu.addSeparator()
    menu.addAction("设置").triggered.connect(panel._open_settings)
    menu.addSeparator()
    menu.addAction("退出").triggered.connect(lambda: _quit_app(app, tray, monitor))
    tray.setContextMenu(menu)
    tray.activated.connect(lambda reason: _tray_activated(reason, panel))
    tray.show()

    enable_autostart()
    sys.exit(app.exec())


def _tray_activated(reason, panel):
    if reason == QSystemTrayIcon.ActivationReason.Trigger:
        if panel.isVisible():
            panel.hide()
        else:
            panel.show_at_cursor()


def _quit_app(app, tray, monitor):
    monitor.stop()
    tray.hide()
    app.quit()


if __name__ == "__main__":
    main()

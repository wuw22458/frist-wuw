"""共享 fixtures — QApplication 单例和信号目录隔离。"""

import sys
import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def qapp():
    """创建 QApplication 单例（session 级别，所有测试共享）。"""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture()
def signal_dir(tmp_path, monkeypatch):
    """将 SIGNAL_DIR 指向临时目录，隔离测试环境。"""
    import constants
    monkeypatch.setattr(constants, "SIGNAL_DIR", tmp_path)
    # 同时更新所有依赖 SIGNAL_DIR 的模块级变量
    import adapters.signal_file
    monkeypatch.setattr(adapters.signal_file, "SIGNAL_DIR", tmp_path)
    import adapters.custom
    monkeypatch.setattr(adapters.custom, "CUSTOM_AGENTS_FILE", tmp_path / "custom_agents.yaml")
    return tmp_path

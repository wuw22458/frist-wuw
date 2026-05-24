# -*- mode: python ; coding: utf-8 -*-
"""Agent Notify PyInstaller 打包配置"""

import os

base_dir = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    [os.path.join(base_dir, 'main.py')],
    pathex=[base_dir],
    binaries=[],
    datas=[
        (os.path.join(base_dir, 'resources'), 'resources'),
        (os.path.join(base_dir, 'hooks', 'claude_hook.py'), 'hooks'),
        (os.path.join(base_dir, 'adapters'), 'adapters'),
        (os.path.join(base_dir, 'aider_notify_helper.py'), '.'),
    ],
    hiddenimports=[
        'PySide6.QtWidgets',
        'PySide6.QtGui',
        'PySide6.QtCore',
        'PySide6.QtSvg',
        'PySide6.QtMultimedia',
        'events',
        'event_bus',
        'adapters',
        'adapters.base',
        'adapters.registry',
        'adapters.signal_file',
        'adapters.claude_code',
        'adapters.cursor',
        'adapters.aider',
        'adapters.custom',
        'adapters.windsurf',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AgentNotify',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(base_dir, 'resources', 'icon.ico') if os.path.exists(os.path.join(base_dir, 'resources', 'icon.ico')) else None,
)

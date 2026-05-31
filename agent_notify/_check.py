import py_compile, sys

files = [
    'ui/style.py', 'ui/settings.py', 'ui/widgets.py', 'ui/splash.py',
    'ui/tray.py', 'notification.py', 'notification_engine.py', 'main.py',
    'events.py', 'settings.py', 'crash_reporter.py', 'signal_file.py',
    'log.py', 'adapters/claude_hook.py'
]
ok = True
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f'OK: {f}')
    except py_compile.PyCompileError as e:
        print(f'ERR: {f}: {e}')
        ok = False
print(f'\n{"All OK" if ok else "ERRORS found"}')

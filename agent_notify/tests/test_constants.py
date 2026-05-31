"""constants.py 迁移逻辑单元测试."""

import json

import pytest


@pytest.fixture()
def migration_env(tmp_path, monkeypatch):
    """设置迁移测试环境:隔离 old_path 和 new_path."""
    import constants

    old_dir = tmp_path / 'old' / '.claude' / 'agent-notify'
    new_dir = tmp_path / 'new' / '.agent-notify'
    monkeypatch.setattr(constants, '_OLD_SIGNAL_DIR', old_dir)
    monkeypatch.setattr(constants, 'SIGNAL_DIR', new_dir)
    monkeypatch.setattr(constants, 'CONFIG_FILE', new_dir / 'config.json')
    monkeypatch.setattr(constants, 'LOCK_FILE', new_dir / '.lock')
    return old_dir, new_dir


class TestMigrateFromOldPath:
    def test_no_old_dir(self, migration_env):
        from constants import migrate_from_old_path

        old_dir, new_dir = migration_env
        migrate_from_old_path()
        assert not new_dir.exists()

    def test_new_dir_already_exists(self, migration_env):
        from constants import migrate_from_old_path

        old_dir, new_dir = migration_env
        old_dir.mkdir(parents=True)
        (old_dir / 'config.json').write_text('{"old": true}')
        new_dir.mkdir(parents=True)
        (new_dir / 'config.json').write_text('{"new": true}')
        migrate_from_old_path()
        # 新目录不被覆盖
        assert json.loads((new_dir / 'config.json').read_text()) == {'new': True}

    def test_migrates_config_and_hooks(self, migration_env):
        from constants import migrate_from_old_path

        old_dir, new_dir = migration_env
        old_dir.mkdir(parents=True)
        (old_dir / 'config.json').write_text('{"sound_enabled": false}')
        hooks_dir = old_dir / 'hooks'
        hooks_dir.mkdir()
        (hooks_dir / 'test.py').write_text("print('hi')")
        migrate_from_old_path()
        assert (new_dir / 'config.json').exists()
        assert (new_dir / 'hooks' / 'test.py').exists()

    def test_does_not_migrate_lock_or_signals(self, migration_env):
        from constants import migrate_from_old_path

        old_dir, new_dir = migration_env
        old_dir.mkdir(parents=True)
        (old_dir / '.lock').write_text('12345')
        (old_dir / 'signal_001.json').write_text('{}')
        migrate_from_old_path()
        assert not (new_dir / '.lock').exists()
        assert not (new_dir / 'signal_001.json').exists()

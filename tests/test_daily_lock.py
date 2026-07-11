import fcntl
from datetime import date

import pytest

from ai_daily_update.cli import run_daily_pipeline
from ai_daily_update.config import Settings
from ai_daily_update.utils.lock import LockBusyError, exclusive_file_lock


def test_exclusive_file_lock_blocks_concurrent_holder(tmp_path) -> None:
    lock_path = tmp_path / "data" / ".daily.lock"
    with exclusive_file_lock(lock_path):
        with pytest.raises(LockBusyError):
            with exclusive_file_lock(lock_path):
                pass


def test_exclusive_file_lock_releases_after_context_exit(tmp_path) -> None:
    lock_path = tmp_path / "data" / ".daily.lock"
    with exclusive_file_lock(lock_path):
        pass
    with exclusive_file_lock(lock_path):
        pass


def test_run_daily_pipeline_raises_when_lock_already_held(tmp_path) -> None:
    settings = Settings(
        root=tmp_path,
        app={"storage": {"markdown_root": "notes", "sqlite_path": "data/kb.sqlite"}},
        topics={},
        sources={},
        scoring={},
        prompts={},
    )
    lock_path = settings.root / "data" / ".daily.lock"
    lock_path.parent.mkdir(parents=True)
    handle = lock_path.open("a+")
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        with pytest.raises(LockBusyError):
            run_daily_pipeline(settings, run_day=date(2026, 7, 8))
    finally:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()

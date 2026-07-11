from __future__ import annotations

import fcntl
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class LockBusyError(RuntimeError):
    """Raised when a file lock is already held by another process/thread."""


@contextmanager
def exclusive_file_lock(lock_path: Path, blocking: bool = False) -> Iterator[None]:
    """Acquire a cross-process exclusive lock backed by a file.

    By default (blocking=False), raises LockBusyError immediately if another
    process (or another call in this process) already holds the lock. This
    guards operations that must not run concurrently across independent
    processes and where we want to skip rather than wait, such as the daily
    pipeline being triggered by the CLI, cron, and the web server's
    background scheduler at the same time.

    With blocking=True, waits for the lock instead of raising. Use this for
    short read-modify-write critical sections (e.g. editing one Markdown
    card's metadata) where a competing writer should be serialized rather
    than rejected.
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+")
    try:
        try:
            flags = fcntl.LOCK_EX if blocking else fcntl.LOCK_EX | fcntl.LOCK_NB
            fcntl.flock(handle.fileno(), flags)
        except OSError as exc:
            raise LockBusyError(f"Lock already held: {lock_path}") from exc
        yield
    finally:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()

"""Shared helpers for import scripts (logging, batching, session naming)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterator, List, Sequence, TypeVar

T = TypeVar('T')


def _now() -> str:
    """Return a short UTC timestamp for log lines."""
    return datetime.utcnow().strftime("%H:%M:%S")


def log_header(title: str) -> None:
    """Print a standardized header block for console output."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def log_step(message: str) -> None:
    """Print a single timestamped log line."""
    print(f"[{_now()}] {message}")


def chunked(items: Sequence[T], size: int) -> Iterator[List[T]]:
    """Yield successive fixed-size chunks from a sequence."""
    if size <= 0:
        raise ValueError("chunk size must be positive")
    for idx in range(0, len(items), size):
        yield list(items[idx:idx + size])


def derive_session_name_from_path(path: Path) -> str:
    """Extract a human-readable session name from a folder path."""
    name = path.name
    return name.split('_')[0] if '_' in name else name

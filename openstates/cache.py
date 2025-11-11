"""Caching utilities for API responses."""

from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Callable, Optional


CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)


def get_cached_or_fetch(
    cache_key: str,
    fetch_func: Callable[[], Any],
    ttl_hours: int = 24,
    cache_subdir: str = ""
) -> Any:
    """
    Get data from cache or fetch if expired/missing.

    Args:
        cache_key: Unique identifier for this cached data
        fetch_func: Function to call if cache miss
        ttl_hours: Time-to-live in hours
        cache_subdir: Optional subdirectory within .cache/

    Returns:
        Cached or freshly fetched data
    """
    # Set up cache directory
    if cache_subdir:
        cache_path = CACHE_DIR / cache_subdir
        cache_path.mkdir(exist_ok=True)
    else:
        cache_path = CACHE_DIR

    cache_file = cache_path / f"{cache_key}.json"

    # Check if cache exists and is valid
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
                cache_time = datetime.fromisoformat(cached_data["timestamp"])

                # Check if cache is still valid
                if datetime.now() - cache_time < timedelta(hours=ttl_hours):
                    return cached_data["data"]
        except (json.JSONDecodeError, KeyError, ValueError):
            # Invalid cache file, will re-fetch
            pass

    # Cache miss or expired - fetch fresh data
    data = fetch_func()

    # Save to cache
    try:
        with open(cache_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "data": data
            }, f, indent=2)
    except Exception as e:
        # Cache write failed, but return data anyway
        print(f"Warning: Failed to write cache: {e}")

    return data


def clear_cache(cache_subdir: Optional[str] = None):
    """Clear all cache files or specific subdirectory."""
    if cache_subdir:
        cache_path = CACHE_DIR / cache_subdir
    else:
        cache_path = CACHE_DIR

    if cache_path.exists():
        for cache_file in cache_path.glob("*.json"):
            cache_file.unlink()

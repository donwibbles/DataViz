from __future__ import annotations

from pathlib import Path

import pytest

from import_utils import chunked, derive_session_name_from_path


def test_chunked_splits_sequence_evenly():
    data = list(range(7))
    chunks = list(chunked(data, 3))
    assert chunks == [[0, 1, 2], [3, 4, 5], [6]]


def test_chunked_raises_for_non_positive_size():
    with pytest.raises(ValueError):
        list(chunked([1, 2, 3], 0))


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (Path("2025-2026_Regular_Session"), "2025-2026"),
        (Path("2019-2020"), "2019-2020"),
        (Path("/tmp/2021-2022_Special/csv"), "csv"),
    ],
)
def test_derive_session_name_from_path_handles_various_inputs(path: Path, expected: str):
    assert derive_session_name_from_path(path) == expected

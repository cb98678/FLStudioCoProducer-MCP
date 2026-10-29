from __future__ import annotations

from coproducer.result import Result, fail, ok


def split_frames(data: list[int], max_len: int) -> Result:
    """Split a byte list into consecutive chunks of at most max_len items.

    Errors: E_ARG when data is not a list or max_len is below 1.
    """
    if not isinstance(data, list) or type(max_len) is not int or max_len < 1:
        return fail("E_ARG", "data must be a list and max_len an integer of at least 1")
    return ok([data[i:i + max_len] for i in range(0, len(data), max_len)])

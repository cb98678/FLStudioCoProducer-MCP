from __future__ import annotations

from coproducer.result import Result, fail, ok


def join_frames(frames: list[list[int]]) -> Result:
    """Concatenate ordered chunks back into one byte list.

    Errors: E_ARG when frames is not a list of lists.
    """
    if not isinstance(frames, list) or any(not isinstance(f, list) for f in frames):
        return fail("E_ARG", "frames must be a list of lists")
    return ok([b for f in frames for b in f])

from __future__ import annotations

from coproducer.result import Result, fail, ok

_PREFIX = [0xF0, 0x7D, 0x43, 0x50]


def parse_frame(frame: list[int]) -> Result:
    """Validate a SysEx frame and return its fields.

    Errors: E_ARG with detail not_ours when the prefix differs, or bad_checksum when the checksum fails.
    """
    if not isinstance(frame, list) or any(type(b) is not int or b < 0 or b > 255 for b in frame):
        return fail("E_ARG", "frame must be a list of bytes")
    if len(frame) < 14 or frame[:4] != _PREFIX or frame[-1] != 0xF7:
        return fail("E_ARG", "not a coproducer frame", not_ours=True)
    if any(b > 127 for b in frame[1:-1]):
        return fail("E_ARG", "frame contains a byte above 127", not_ours=True)
    body = frame[4:-2]
    if (sum(body) & 0x7F) != frame[-2]:
        return fail("E_ARG", "bad checksum", bad_checksum=True)
    return ok({"version": body[0], "type": body[1], "req_id": (body[2] << 7) | body[3],
               "seq": (body[4] << 7) | body[5], "total": (body[6] << 7) | body[7], "payload": body[8:]})

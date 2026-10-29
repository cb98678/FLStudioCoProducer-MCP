from __future__ import annotations

from coproducer.result import Result, fail, ok

_PREFIX = [0xF0, 0x7D, 0x43, 0x50]


def build_frame(version: int, msg_type: int, req_id: int, seq: int, total: int, payload: list[int]) -> Result:
    """Build one SysEx frame: prefix, version, type, 14-bit request id, sequence, total, payload, checksum, F7.

    The checksum is the sum of every byte from version through the payload, masked to 7 bits.
    Errors: E_ARG for out-of-range fields or a payload byte above 127.
    """
    small = (version, msg_type)
    wide = (req_id, seq, total)
    if any(type(x) is not int or x < 0 or x > 127 for x in small):
        return fail("E_ARG", "version and msg_type must be 0 to 127")
    if any(type(x) is not int or x < 0 or x > 16383 for x in wide) or total < 1 or seq >= total:
        return fail("E_ARG", "req_id, seq, total must be 0 to 16383 with total >= 1 and seq < total")
    if not isinstance(payload, list) or any(type(b) is not int or b < 0 or b > 127 for b in payload):
        return fail("E_ARG", "payload must be a list of 7-bit integers")
    body = [version, msg_type, req_id >> 7, req_id & 0x7F, seq >> 7, seq & 0x7F, total >> 7, total & 0x7F] + payload
    return ok(_PREFIX + body + [sum(body) & 0x7F, 0xF7])

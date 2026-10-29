from __future__ import annotations

from coproducer.result import Result, fail, ok


def decode_sysex(data: list[int]) -> Result:
    """Unpack 7-bit SysEx data (groups of up to 8) back into bytes.

    Errors: E_ARG when a value is above 127 or the final group has a header but no data.
    """
    if not isinstance(data, list) or any(type(b) is not int or b < 0 or b > 127 for b in data):
        return fail("E_ARG", "data must be a list of integers from 0 to 127")
    out = []
    for i in range(0, len(data), 8):
        group = data[i:i + 8]
        if len(group) < 2:
            return fail("E_ARG", "truncated group: header byte without data")
        head = group[0]
        for j, b in enumerate(group[1:]):
            out.append(b | (((head >> j) & 1) << 7))
    return ok(out)

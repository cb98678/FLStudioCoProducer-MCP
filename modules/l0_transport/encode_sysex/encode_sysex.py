from __future__ import annotations

from coproducer.result import Result, fail, ok


def encode_sysex(data: list[int]) -> Result:
    """Pack bytes into 7-bit form: each group of up to 7 bytes becomes a header byte plus the low 7 bits.

    Header bit i holds the top bit of byte i of the group.
    Errors: E_ARG when data is not a list of integers from 0 to 255.
    """
    if not isinstance(data, list) or any(type(b) is not int or b < 0 or b > 255 for b in data):
        return fail("E_ARG", "data must be a list of integers from 0 to 255")
    out = []
    for i in range(0, len(data), 7):
        group = data[i:i + 7]
        head = 0
        for j, b in enumerate(group):
            head |= (b >> 7) << j
        out.append(head)
        out.extend(b & 0x7F for b in group)
    return ok(out)

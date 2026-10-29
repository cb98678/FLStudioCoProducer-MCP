from __future__ import annotations

import json

from coproducer.result import Result, fail, ok


def decode_body(body: list[int]) -> Result:
    """Split message bytes into an operation name and its JSON dict.

    Errors: E_ARG when the bytes are not UTF-8, lack the separator, or the JSON is not an object.
    """
    try:
        text = bytes(body).decode("utf-8")
        name, sep, rest = text.partition("\x1f")
        data = json.loads(rest) if sep else None
    except (TypeError, ValueError) as e:
        return fail("E_ARG", f"undecodable body: {e}")
    if not sep or not name or not isinstance(data, dict):
        return fail("E_ARG", "body must be name, 0x1F, then a JSON object")
    return ok({"name": name, "data": data})

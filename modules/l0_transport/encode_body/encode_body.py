from __future__ import annotations

import json

from coproducer.result import Result, fail, ok


def encode_body(name: str, data: dict) -> Result:
    """Turn an operation name and a JSON-friendly dict into message bytes: name, a 0x1F separator, compact JSON.

    Errors: E_ARG when name is empty or contains the separator, or data cannot be written as JSON.
    """
    if not isinstance(name, str) or not name or "\x1f" in name or not isinstance(data, dict):
        return fail("E_ARG", "name must be a non-empty string without 0x1F and data a dict")
    try:
        text = name + "\x1f" + json.dumps(data, separators=(",", ":"), ensure_ascii=True)
    except (TypeError, ValueError) as e:
        return fail("E_ARG", f"data is not JSON friendly: {e}")
    return ok(list(text.encode("utf-8")))

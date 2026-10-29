"""Thin JSON Schema validation used by the registry for module inputs."""
from __future__ import annotations

import json
import math

from jsonschema import Draft202012Validator

from .result import Result, fail, ok


def parse_schema(text: str) -> dict:
    return json.loads(text) if isinstance(text, str) else dict(text)


def _bad_text(value, depth: int = 0) -> bool:
    """True when the arguments hold a NaN or infinity, or a string with a NUL character or one that cannot be written as UTF-8 (a lone surrogate).

    No module can use either: they break every file call and every JSON hand-off."""
    if isinstance(value, float) and not math.isfinite(value):
        return True
    if isinstance(value, str):
        if "\x00" in value:
            return True
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            return True
        return False
    if depth > 50:
        return False
    if isinstance(value, dict):
        return any(_bad_text(k, depth + 1) or _bad_text(v, depth + 1) for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return any(_bad_text(v, depth + 1) for v in value)
    return False


RESERVED = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$", *("COM%d" % i for i in range(1, 10)), *("LPT%d" % i for i in range(1, 10)),
            *(p + d for p in ("COM", "LPT") for d in "\u00b9\u00b2\u00b3")}
PATH_NAMES = ("path", "dir", "project", "file", "filename", "sandbox_root")


def is_path_name(name: str) -> bool:
    n = name.lower()
    return n in PATH_NAMES or "path" in n or n.endswith("_dir") or n.endswith("_file")


def unsafe_path(text: str) -> str:
    """Why a path argument must be refused on any machine, or ''.

    Windows treats the names CON, NUL, AUX, PRN, COM1 and LPT1 (with or without an extension) as devices: opening CON waits for the keyboard
    forever (see https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file, measured here 2026-10-21, it froze every later call in the process). A path that starts with two slashes names a network share or a
    device namespace, and merely touching it can block for minutes on a name lookup. A colon anywhere but a drive letter names an alternate
    data stream or a device."""
    if text.startswith(("\\\\", "//")):
        return "network and device paths (starting with two slashes) are not allowed"
    body = text[2:] if len(text) > 1 and text[1] == ":" and text[0].isalpha() else text
    if ":" in body:
        return "a colon is only allowed in a drive letter"
    for part in text.replace("\\", "/").split("/"):
        stem = part.strip().split(".")[0].strip().upper()
        if stem in RESERVED:
            return "%s is a Windows device name" % part
    return ""


def _path_problem(schema: dict, args: dict) -> str:
    props = schema.get("properties") or {}
    for k, v in args.items():
        if isinstance(v, str) and (is_path_name(k) or props.get(k, {}).get("x-path") is True):   # "x-path": true marks a text argument that becomes a file name
            why = unsafe_path(v)
            if why:
                return "%s: %s" % (k, why)
    return ""


def validate_args(schema: dict, args: dict) -> Result:
    bad = _path_problem(schema, args)
    if bad:
        return fail("E_ARG", bad)
    if _bad_text(args):
        return fail("E_ARG", "(arguments): a value is NaN or infinite, or text holds a NUL character or an unpaired surrogate")
    v = Draft202012Validator(schema)
    errs = sorted(v.iter_errors(args), key=lambda e: list(e.path))
    if not errs:
        return ok()
    e = errs[0]
    where = ".".join(str(p) for p in e.path) or "(arguments)"
    return fail("E_ARG", f"{where}: {e.message}", schema_errors=len(errs))


def normalize_args(schema: dict, args: dict) -> dict:
    """Turn 3.0 into 3 where the schema says integer (JSON Schema accepts a whole float as an integer; range() and indexing do not)."""
    props = schema.get("properties") or {}
    out = dict(args)
    for k, v in args.items():
        kinds = props.get(k, {}).get("type")
        kinds = [kinds] if isinstance(kinds, str) else (kinds or [])
        if type(v) is float and v.is_integer() and "integer" in kinds and "number" not in kinds:
            out[k] = int(v)
    return out

from __future__ import annotations

import json

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service

_DASHES = (chr(0x2014), chr(0x2013))


def write_report_file(path: str, content: dict | str, fmt: str = "json") -> Result:
    """Write a report (JSON object or markdown text) inside the sandbox folder. Dashes are replaced with plain hyphens.

    Errors: E_SANDBOX_VIOLATION when outside the sandbox, E_ARG when fmt and content disagree.
    """
    root = get_service("sandbox_root")
    if root is None:
        return fail("E_SANDBOX_VIOLATION", "no sandbox folder is configured")
    chk = call("check_sandbox_path", path=path, sandbox_root=str(root))
    if not chk.ok:
        return chk
    if fmt == "json" and not isinstance(content, dict):
        return fail("E_ARG", "json reports need an object")
    if fmt == "markdown" and not isinstance(content, str):
        return fail("E_ARG", "markdown reports need text")
    text = json.dumps(content, indent=2, sort_keys=True, ensure_ascii=False) if fmt == "json" else content
    for d in _DASHES:
        text = text.replace(d, "-")
    target = chk.value["resolved"]
    try:
        with open(target, "w", encoding="utf-8", newline="\n") as f:
            f.write(text + "\n")
    except OSError as e:
        return fail("E_IO", "cannot write report: %s" % e)
    return ok({"path": target, "bytes": len(text.encode("utf-8")) + 1})

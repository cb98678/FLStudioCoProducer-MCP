"""The runner loop: read one JSON request per line, write one JSON reply per line. Standard library only."""
from __future__ import annotations

import json
import os
import sys


class RunnerError(Exception):
    def __init__(self, code: str, message: str, **detail) -> None:
        super().__init__(message)
        self.code, self.detail = code, detail


def error_code(exc: BaseException) -> str:
    """Map a library exception to a project error code."""
    if isinstance(exc, RunnerError):
        return exc.code
    if "OutOfMemory" in type(exc).__name__ or "out of memory" in str(exc).lower():
        return "E_GPU_BUDGET"
    return "E_MODEL"


def serve(handlers: dict) -> None:
    """Run until stdin closes or a shutdown request arrives. Library prints go to stderr so the protocol stays clean."""
    out = os.fdopen(os.dup(1), "w", encoding="utf-8", newline="\n")
    sys.stdout = sys.stderr
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
        except ValueError:
            continue
        op, rid = req.get("op"), req.get("id")
        fn = handlers.get(op)
        if op == "shutdown":
            out.write(json.dumps({"id": rid, "ok": True, "value": True}) + "\n")
            out.flush()
            return
        out.write(json.dumps(run_one(fn, op, rid, req.get("args") or {})) + "\n")
        out.flush()


def run_one(fn, op: str, rid, args: dict) -> dict:
    if fn is None:
        return {"id": rid, "ok": False, "error": {"code": "E_NOT_FOUND", "message": "unknown op %s" % op}}
    try:
        return {"id": rid, "ok": True, "value": fn(args)}
    except BaseException as e:  # noqa: BLE001 - a runner must always answer, even to SystemExit from a CLI
        detail = getattr(e, "detail", {}) or {}
        return {"id": rid, "ok": False, "error": {"code": error_code(e), "message": "%s: %s" % (type(e).__name__, e), "detail": detail}}

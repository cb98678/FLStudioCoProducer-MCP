"""Result and Error: the only way a module reports an outcome.

This file is also inlined into the generated FL-side dispatcher, so it MUST stay
compatible with the Python that FL Studio embeds (about 3.9) and MUST NOT import
anything outside the standard library.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

ERROR_CODES = (
    "E_ARG", "E_NOT_FOUND", "E_UNSUPPORTED_API", "E_TIMEOUT", "E_NOT_VERIFIED",
    "E_SANDBOX_VIOLATION", "E_GPU_BUDGET", "E_MODEL", "E_GUI_MISMATCH",
    "E_BLOCKED_BY_DIALOG", "E_IO", "E_HALTED", "E_AUTONOMY", "E_INTERNAL", "E_PENDING_HUMAN",
)


@dataclass(frozen=True)
class Error:
    code: str
    message: str
    retryable: bool = False
    detail: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Result:
    ok: bool
    value: Any = None
    error: Error | None = None
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        err = None
        if self.error is not None:
            err = {"code": self.error.code, "message": self.error.message,
                   "retryable": self.error.retryable, "detail": dict(self.error.detail)}
        return {"ok": self.ok, "value": self.value, "error": err, "meta": dict(self.meta)}

    @staticmethod
    def from_dict(d: dict) -> "Result":
        e = d.get("error")
        err = None
        if e:
            err = Error(e.get("code", "E_INTERNAL"), e.get("message", ""),
                        bool(e.get("retryable", False)), dict(e.get("detail") or {}))
        return Result(bool(d.get("ok")), d.get("value"), err, dict(d.get("meta") or {}))


def ok(value: Any = None, **meta: Any) -> Result:
    return Result(True, value, None, dict(meta))


def fail(code: str, message: str, retryable: bool = False,
         meta: dict | None = None, **detail: Any) -> Result:
    return Result(False, None, Error(code, message, retryable, dict(detail)), dict(meta or {}))


def first_error(*results: Result) -> Result | None:
    """Return the first failed Result in `results`, or None when all succeeded."""
    for r in results:
        if not r.ok:
            return r
    return None

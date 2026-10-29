from __future__ import annotations

from pathlib import Path

from coproducer.result import Result, fail, ok


def check_sandbox_path(path: str, sandbox_root: str) -> Result:
    """Confirm that path resolves to a location inside sandbox_root (symlinks and .. are resolved).

    Errors: E_ARG for empty input, E_SANDBOX_VIOLATION when the path is outside.
    """
    if not path or not sandbox_root:
        return fail("E_ARG", "path and sandbox_root are required")
    target = Path(path).resolve(strict=False)
    root = Path(sandbox_root).resolve(strict=False)
    if target == root or root in target.parents:
        return ok({"resolved": str(target)})
    return fail("E_SANDBOX_VIOLATION", f"{target} is outside the sandbox {root}")

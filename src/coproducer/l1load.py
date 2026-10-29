"""Load a generated L1 op for tests: exec its source with the FL-side prelude names in scope."""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Callable

from . import fl_prelude

ROOT = Path(__file__).resolve().parents[2] / "modules" / "l1_fl_ops"


def load_l1(name: str, root: Path | None = None) -> Callable[..., Any]:
    path = (root or ROOT) / name / f"{name}.py"
    src = path.read_text(encoding="utf-8")
    ast.parse(src)
    ns: dict[str, Any] = {k: getattr(fl_prelude, k) for k in ("_bad", "_check_args", "_run", "_raw", "_RAW_ALLOW")}
    ns["__name__"] = name
    exec(compile(src, str(path), "exec"), ns)  # noqa: S102 - generated, linted source
    return ns[name]

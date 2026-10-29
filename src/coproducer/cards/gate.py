"""The gate for one built module: lint, the module's own tests, and the size check, run in a scratch copy of the modules tree."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

from ..lint import lint_tree
from .parse import LAYER_DIRS


def layer_of(manifest_text: str) -> str | None:
    try:
        return tomllib.loads(manifest_text)["module"]["layer"]
    except (tomllib.TOMLDecodeError, KeyError, TypeError):
        return None


def run_gate(name: str, files: dict, modules_root: Path, timeout_s: int = 120, runner=subprocess.run) -> dict:
    """Write the three files into a scratch copy of modules/, then lint and test. Returns {passed, stage, report}."""
    need = (name + ".py", "module.toml", "test_%s.py" % name)
    gone = [f for f in need if f not in files]
    if gone:
        return {"passed": False, "stage": "files", "report": "missing files: " + ", ".join(gone)}
    layer = layer_of(files["module.toml"])
    if layer not in LAYER_DIRS:
        return {"passed": False, "stage": "manifest", "report": "module.toml has no valid [module] layer"}
    scratch = Path(tempfile.mkdtemp(prefix="gate_"))
    try:
        tree = scratch / "modules"
        shutil.copytree(modules_root, tree, ignore=shutil.ignore_patterns("__pycache__"))
        target = tree / LAYER_DIRS[layer] / name
        target.mkdir(parents=True, exist_ok=True)
        for f in need:
            (target / f).write_text(files[f], encoding="utf-8", newline="\n")
        problems = lint_tree(tree).get(name, [])
        if problems:
            return {"passed": False, "stage": "lint", "report": "\n".join(str(p) for p in problems)}
        env = dict(os.environ, COPRODUCER_MODULES=str(tree))
        done = runner([sys.executable, "-m", "pytest", str(target), "-q", "-x", "-p", "no:cacheprovider"], cwd=scratch, env=env,
                      capture_output=True, text=True, timeout=timeout_s)
        tail = (done.stdout + done.stderr)[-3000:]
        return {"passed": done.returncode == 0, "stage": "tests", "report": tail}
    except subprocess.TimeoutExpired:
        return {"passed": False, "stage": "tests", "report": "tests did not finish in %d seconds" % timeout_s}
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

"""Build workers from the registry spec and config: which Python, which runner script, where the log goes."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Callable

from .spec import ModelSpec
from .worker import Worker

RUNNERS = Path(__file__).resolve().parents[1] / "runners"


def runner_path(spec: ModelSpec) -> Path:
    return RUNNERS / (spec.runner or (spec.stack + "_runner.py"))


def python_for(spec: ModelSpec, config: dict) -> str | None:
    """The interpreter of the stack's isolated environment; the 'test' stack uses the current interpreter."""
    if spec.stack == "test":
        return sys.executable
    return config.get("envs", {}).get(spec.stack) or None


def make_worker_factory(config: dict, log_dir: Path | str | None = None) -> Callable[[ModelSpec], Worker]:
    def make(spec: ModelSpec) -> Worker:
        py = python_for(spec, config)
        if not py:
            return _Missing("no environment is configured for the %r stack; run coproducer setup" % spec.stack)
        env = dict(os.environ, PYTHONUNBUFFERED="1", HF_HUB_OFFLINE=os.environ.get("HF_HUB_OFFLINE", "1"))
        if spec.stack == "acestep" and "ACESTEP_HOME" not in env:
            # The runner reads <root>/checkpoints. Without this the root was the server's current folder: on rtxclub ACE-Step put its
            # 10 GB of checkpoints in C:\coproducer\checkpoints (found 2026-10-26). The clone is the folder that holds .venv.
            env["ACESTEP_HOME"] = str(Path(py).resolve().parents[2])
        log = Path(log_dir) / (spec.stack + ".log") if log_dir else None
        if log:
            log.parent.mkdir(parents=True, exist_ok=True)
        return Worker([py, str(runner_path(spec))], log_path=log, env=env)
    return make


class _Missing:
    """A worker stand-in that reports a clear error instead of crashing the scheduler."""

    def __init__(self, why: str) -> None:
        self.why = why

    def start(self):
        from ..result import fail
        return fail("E_MODEL", self.why)

    def alive(self) -> bool:
        return False

    def call(self, op, args=None, timeout_s=0.0):
        return self.start()

    def stop(self) -> None:
        pass

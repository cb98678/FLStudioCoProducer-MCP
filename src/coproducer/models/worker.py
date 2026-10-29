"""A model worker: a runner process inside an isolated environment, spoken to with line-delimited JSON."""
from __future__ import annotations

import json
import queue
import subprocess
import threading
from pathlib import Path
from typing import Sequence

from ..result import Result, fail, ok


class Worker:
    def __init__(self, cmd: Sequence[str], log_path: Path | str | None = None, env: dict | None = None) -> None:
        self.cmd, self.env = list(cmd), env
        self.log_path = Path(log_path) if log_path else None
        self.proc: subprocess.Popen | None = None
        self._replies: "queue.Queue[dict]" = queue.Queue()
        self._next = 0
        self._lock = threading.Lock()

    def start(self) -> Result:
        if self.alive():
            return ok(True)
        err = open(self.log_path, "ab") if self.log_path else subprocess.DEVNULL
        try:
            self.proc = subprocess.Popen(self.cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err,
                                         text=True, encoding="utf-8", bufsize=1, env=self.env)
        except OSError as e:
            return fail("E_MODEL", "cannot start the model runner: %s" % e)
        threading.Thread(target=self._pump, args=(self.proc,), daemon=True).start()
        return ok(True)

    def _pump(self, proc: subprocess.Popen) -> None:
        for line in proc.stdout:                       # type: ignore[union-attr]
            try:
                self._replies.put(json.loads(line))
            except ValueError:
                continue                               # stray library output is ignored, never trusted

    def alive(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def call(self, op: str, args: dict | None = None, timeout_s: float = 600.0) -> Result:
        """Send one request and wait for its reply. A timeout kills the runner, since its state is unknown."""
        with self._lock:
            started = self.start()
            if not started.ok:
                return started
            self._next += 1
            rid = self._next
            try:
                self.proc.stdin.write(json.dumps({"id": rid, "op": op, "args": args or {}}) + "\n")  # type: ignore[union-attr]
                self.proc.stdin.flush()                                                              # type: ignore[union-attr]
            except OSError as e:
                return fail("E_MODEL", "the model runner closed its input: %s" % e)
            return self._await(rid, op, timeout_s)

    def _await(self, rid: int, op: str, timeout_s: float) -> Result:
        while True:
            try:
                rep = self._replies.get(timeout=timeout_s)
            except queue.Empty:
                self.stop()
                return fail("E_TIMEOUT", "no reply to %s within %.0f s; the runner was stopped" % (op, timeout_s), retryable=True)
            if rep.get("id") != rid:
                continue
            if rep.get("ok"):
                return ok(rep.get("value"))
            e = rep.get("error") or {}
            return fail(e.get("code", "E_MODEL"), e.get("message", "the model runner failed"), **(e.get("detail") or {}))

    def stop(self) -> None:
        if self.proc is None:
            return
        try:
            if self.proc.poll() is None:
                self.proc.kill()
            self.proc.wait(timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            pass
        self.proc = None

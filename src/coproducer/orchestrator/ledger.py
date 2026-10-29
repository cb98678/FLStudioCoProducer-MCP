"""Append-only JSON-lines run log. Every entry is flushed to disk before append returns."""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any

TYPES = ("run_start", "phase_enter", "step_start", "step_result", "verify", "snapshot", "rollback", "ask",
         "answer", "model_load", "model_unload", "external_release", "decision", "halt", "run_end", "plan_set", "note", "promotion", "waiting_for_fl", "resume_after_wait")
MAX_VALUE_BYTES = 65536


def jsonable(value: Any) -> tuple[Any, bool]:
    """Return (a JSON-safe copy, complete). Values over MAX_VALUE_BYTES are replaced by a marker and complete is False."""
    try:
        text = json.dumps(value, default=str)
    except (TypeError, ValueError):
        text = json.dumps(str(value))
    if len(text) > MAX_VALUE_BYTES:
        return {"_truncated": True, "bytes": len(text), "preview": text[:200]}, False
    return json.loads(text), True


class Ledger:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.seq = len(self.entries())

    def append(self, type_: str, **fields: Any) -> dict:
        if type_ not in TYPES:
            raise ValueError("unknown ledger type %r" % type_)
        with self._lock:
            self.seq += 1
            entry = {"seq": self.seq, "ts": round(time.time(), 3), "type": type_}
            for k, v in fields.items():
                entry[k], whole = jsonable(v)
                if not whole:
                    entry[k + "_complete"] = False
            with open(self.path, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(entry, sort_keys=True) + "\n")
                f.flush()
                os.fsync(f.fileno())
        return entry

    def entries(self) -> list[dict]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue          # a torn last line after a crash is ignored
        return out

    def tail(self, n: int = 10) -> list[dict]:
        return self.entries()[-n:]

    def done_steps(self) -> dict[str, dict]:
        """Steps whose result was ok and whose verification passed, keyed by step id (for resume)."""
        results: dict[str, dict] = {}
        done: dict[str, dict] = {}
        for e in self.entries():
            if e["type"] == "step_result":
                results[e["step_id"]] = e
            elif e["type"] == "verify" and e.get("passed") and e["step_id"] in results:
                r = results[e["step_id"]]
                if r.get("ok") and r.get("value_complete", True):
                    done[e["step_id"]] = r
        return done

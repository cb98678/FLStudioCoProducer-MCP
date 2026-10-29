"""coproducer new-project and promote. promote is the only way a result leaves the sandbox, and only a human runs it."""
from __future__ import annotations

import datetime
import hashlib
import shutil
from pathlib import Path

from ..orchestrator.ledger import Ledger
from ..orchestrator.spec_sheet import write_spec


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def new_project(home: Path, name: str, mode: str, source: str | None) -> dict:
    """Create specs/<name>.md with the header filled from what is known now."""
    header = {"project": name, "mode": mode, "source": source or "", "original_hash": sha256(Path(source)) if source and Path(source).is_file() else "",
              "targets": "", "iteration_cap": 3}
    got = write_spec(home / "specs" / (name + ".md"), header)
    return {"ok": got.ok, "message": got.error.message if not got.ok else got.value["path"]}


def promote(home: Path, run_id: str, result: Path, destination: Path, confirm: str, now=datetime.datetime.now) -> dict:
    """Copy a sandbox file over a real project path. The old file is kept as a timestamped backup. The caller must pass the exact word 'promote'."""
    sandbox = (home / "sandbox").resolve()
    result, destination = result.resolve(), destination.resolve()
    if confirm != "promote":
        return {"ok": False, "message": "not confirmed; nothing was copied"}
    if sandbox not in result.parents or not result.is_file():
        return {"ok": False, "message": "the result must be a file inside the sandbox folder"}
    if sandbox in destination.parents:
        return {"ok": False, "message": "the destination must be outside the sandbox"}
    backup = None
    if destination.exists():
        backup = destination.with_name(destination.name + ".bak-" + now().strftime("%Y%m%d-%H%M%S"))
        shutil.copy2(destination, backup)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(result, destination)
    if sha256(destination) != sha256(result):
        return {"ok": False, "message": "the copy does not match the source; the backup is %s" % backup}
    Ledger(home / "runs" / run_id / "ledger.jsonl").append("promotion", result=str(result), destination=str(destination), backup=str(backup) if backup else None)
    return {"ok": True, "message": "copied to %s" % destination, "backup": str(backup) if backup else None}

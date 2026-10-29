from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return "sha256:" + h.hexdigest()


def copy_project_to_sandbox(source: str, project: str, include_folder: bool = False, max_mb: int = 2048) -> Result:
    """Copy a project file (and optionally its folder) into sandbox/<project>/. The original is only read, never written.

    Errors: E_NOT_FOUND no source, E_SANDBOX_VIOLATION when source is already inside the sandbox, E_NOT_VERIFIED if the copy differs.
    """
    root, src = get_service("sandbox_root"), Path(source)
    if root is None or not src.is_file():
        return fail("E_NOT_FOUND", "need a sandbox folder and an existing project file")
    dest = Path(root) / project / src.name
    chk = call("check_sandbox_path", path=str(dest), sandbox_root=str(root))
    if not chk.ok or Path(root).resolve() in src.resolve().parents:
        return fail("E_SANDBOX_VIOLATION", "the source must be outside the sandbox and the target inside it")
    if include_folder and sum(f.stat().st_size for f in src.parent.rglob("*") if f.is_file()) > max_mb * 2**20:
        return fail("E_ARG", "the project folder is larger than %d MB" % max_mb)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src.parent, dest.parent, dirs_exist_ok=True) if include_folder else shutil.copy2(src, dest)
    before, after = _sha(src), _sha(dest)
    if before != after:
        return fail("E_NOT_VERIFIED", "the copy does not match the original")
    return ok({"path": str(dest), "original_hash": before, "copy_hash": after}, verified=True)

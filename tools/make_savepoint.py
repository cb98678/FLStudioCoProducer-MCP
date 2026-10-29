"""Zip a save point: the repository (no venv, no caches) plus the small sandbox files needed to rebuild or continue a remix.

    python tools/make_savepoint.py NAME [--extra sandbox/techhouse/FILE ...] [--with-render PATH]

Writes sandbox/savepoints/NAME.zip and a MANIFEST.txt inside it (size and sha256 of every file). Large stems and renders stay out unless named
with --with-render. The default extras are the v12 remix inputs; pass --extra to add more (paths relative to the repo, files or folders, small files only).
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The repository is what a release packs (tools/make_release.py, INCLUDE_TOP): everything else on the host (model weights in models/ and
# checkpoints/, logs, .venv, .hypothesis, sandbox, old zips) is data, not source, and is left out. The first run without such a list swept up
# 10+ GB of model files, and so did the first release build (2026-10-26), which is why both now use the one list.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_release import files as release_files  # noqa: E402

MAX_FILE = 5_000_000  # bytes: a repo file larger than this is not source; it is listed in the manifest as skipped
DEFAULT_EXTRAS = [
    "sandbox/techhouse/FriendsInLowPlaces_TechHouse_v12.flp",
    "sandbox/techhouse/FriendsInLowPlaces_TechHouse_v3e_userfix.flp",
    "sandbox/techhouse/cuts_v12.json",
    "sandbox/techhouse/audio_v12/techhouse_audio.json",
]
SMALL = 3_000_000  # bytes: files in an extra folder above this size are skipped


def repo_files() -> list[Path]:
    return [ROOT / f for f in release_files(ROOT)]


def extra_files(spec: str) -> list[Path]:
    p = ROOT / spec
    if p.is_file():
        return [p]
    if p.is_dir():
        return [q for q in sorted(p.rglob("*")) if q.is_file() and q.stat().st_size <= SMALL]
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name")
    ap.add_argument("--extra", nargs="*", default=None)
    ap.add_argument("--with-render", default=None)
    a = ap.parse_args()
    files = [f for f in repo_files() if f.stat().st_size <= MAX_FILE]
    missing = []
    for spec in (DEFAULT_EXTRAS if a.extra is None else a.extra):
        got = extra_files(spec)
        files += got
        if not got:
            missing.append(spec)
    if a.with_render:
        files.append(Path(a.with_render) if os.path.isabs(a.with_render) else ROOT / a.with_render)
    out_dir = ROOT / "sandbox" / "savepoints"          # under the sandbox like every other output (top-level savepoints/ until 2026-10-26)
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / (a.name + ".zip")
    lines = []
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            rel = f.relative_to(ROOT).as_posix() if f.is_relative_to(ROOT) else f.name
            data = f.read_bytes()
            z.writestr(a.name + "/" + rel, data)
            lines.append("%10d  %s  %s" % (len(data), hashlib.sha256(data).hexdigest()[:16], rel))
        head = ["Save point %s" % a.name, "Start with docs/HANDOFF.md, then docs/FILE_MAP.md.", "Files: %d" % len(lines)]
        if missing:
            head.append("Not found (skipped): " + ", ".join(missing))
        z.writestr(a.name + "/MANIFEST.txt", "\n".join(head + [""] + lines) + "\n")
    print("wrote", dest, dest.stat().st_size, "bytes,", len(lines), "files")
    for m in missing:
        print("not found:", m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

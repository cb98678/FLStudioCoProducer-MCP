"""Build the release zip a new machine installs from: dist/coproducer-<version>.zip, with install.cmd at its root.

    python tools/make_release.py                 # dist/coproducer-<version>.zip
    python tools/make_release.py --list          # print the files it would pack, and their total size

What goes in is the program, its data and the installer, named one top-level entry at a time (INCLUDE_TOP): a working machine collects
other things at the top of its folder (rtxclub had a 14 GB savepoint zip and 10 GB of ACE-Step checkpoints there), and a list of what to
leave out would never be complete. Inside those entries, what belongs to one machine or is rebuilt by the installer stays out: the
environments and weights under models/, caches, backups. config.toml, the sandbox, runs, logs and the installer's runtime folder are never
in the list. A zip made from a working install is therefore safe to hand on.
"""
from __future__ import annotations

import argparse
import os
import sys
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# The top-level files and folders of the program. Anything else at the top of the folder is left out.
INCLUDE_TOP = {"README.md", "LICENSE", "install.ps1", "install.cmd", "pyproject.toml", "requirements.lock", "mcp.example.json",
               "assets", "cards", "docs", "fl_side", "genre_profiles", "models", "modules", "plans", "plugins", "probes", "recipes", "skills", "specs",
               "src", "styles", "targets", "tests", "tools"}
# Paths (relative to the root, with forward slashes) never packed, even inside an included folder.
EXCLUDE_PATHS = {"models/envs", "models/weights", "models/acestep", "models/checkpoints"}
# Folder names never packed wherever they are.
EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", ".hypothesis", ".venv", ".git", "node_modules"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".bak", ".part", ".tmp", ".log"}
# What a release cannot work without; build() refuses to write a zip that misses one.
REQUIRED = ["install.cmd", "install.ps1", "pyproject.toml", "requirements.lock", "src/coproducer/cli/__init__.py",
            "src/coproducer/data/deps.lock.json", "fl_side/device_coproducer.py", "models/registry.toml",
            "assets/templates/base_project.flp", "assets/templates/sytrus_patches.flp", "assets/templates/serum_carrier.flp",
            "tools/remix_song.py", "docs/INSTALL.md"]


def version(root: Path = ROOT) -> str:
    with open(root / "pyproject.toml", "rb") as f:
        return tomllib.load(f)["project"]["version"]


def excluded(rel: str) -> bool:
    parts = rel.split("/")
    if parts[0] not in INCLUDE_TOP:
        return True
    if any(rel == p or rel.startswith(p + "/") for p in EXCLUDE_PATHS):
        return True
    if any(p in EXCLUDE_DIRS for p in parts[:-1]):
        return True
    return Path(rel).suffix.lower() in EXCLUDE_SUFFIXES or ".coproducer-" in parts[-1]


def files(root: Path = ROOT) -> list[str]:
    """Every file to pack, as sorted paths relative to root with forward slashes. Excluded folders are not even walked (the sandbox of a
    working machine holds tens of thousands of files)."""
    out = []
    for d, dirs, names in os.walk(root):
        base = Path(d).relative_to(root).as_posix()
        base = "" if base == "." else base + "/"
        dirs[:] = sorted(x for x in dirs if x not in EXCLUDE_DIRS and not excluded(base + x + "/_"))
        out += [base + n for n in names if not excluded(base + n)]
    return sorted(out)


def build(root: Path = ROOT, dest: Path | None = None) -> Path:
    names = files(root)
    missing = [r for r in REQUIRED if r not in names]
    if missing:
        raise SystemExit("not a complete release, missing: " + ", ".join(missing))
    dest = dest or root / "dist" / ("coproducer-%s.zip" % version(root))
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for rel in names:
            z.write(root / rel, rel)
    tmp.replace(dest)
    return dest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--list", action="store_true", help="print the files and their total size, write nothing")
    ap.add_argument("--out", default=None, help="zip to write (default dist/coproducer-<version>.zip)")
    a = ap.parse_args(argv)
    if a.list:
        names = files()
        for n in names:
            print(n)
        print("%d files, %.1f MB" % (len(names), sum((ROOT / n).stat().st_size for n in names) / 1e6))
        return 0
    out = build(ROOT, Path(a.out) if a.out else None)
    print("%s  %.1f MB" % (out, out.stat().st_size / 1e6))
    return 0


if __name__ == "__main__":
    sys.exit(main())

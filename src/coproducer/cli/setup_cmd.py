"""coproducer setup: folders, config.toml, FL-side script, and the two instruction blocks. Never overwrites an existing config."""
from __future__ import annotations

import shutil
from pathlib import Path

from ..config import load_config, render_config
from . import detect, texts


def ensure_dirs(home: Path, cfg: dict) -> list:
    made = []
    for d in (cfg["paths"]["sandbox"], cfg["paths"]["models"], cfg["paths"]["runs"], cfg["paths"]["weights"], "logs", "specs"):
        p = home / d
        if not p.exists():
            p.mkdir(parents=True)
            made.append(str(p))
    return made


def write_config(home: Path, fl_exe: str, data_dir: str) -> str:
    """Create config.toml with what was detected. Returns 'created' or 'kept'."""
    f = home / "config.toml"
    if f.exists():
        return "kept"
    cfg = load_config(home)
    cfg["fl"]["exe"], cfg["fl"]["data_dir"] = fl_exe, data_dir
    f.write_text(render_config(cfg), encoding="utf-8", newline="\n")
    return "created"


def apply_settings(home: Path, torch_index: str | None = None, models_dir: str | None = None) -> list:
    """Set the values the installer detects in config.toml, created or kept. Returns 'table.key = value' for each one that changed."""
    from ..config import load_config as _load
    cfg, changed = _load(home), []
    want = []
    if torch_index is not None:
        want.append(("gpu", "torch_index", torch_index))
    if models_dir:          # written with forward slashes, as config.toml keeps every path (render_config), so a second run sees no change
        m = Path(models_dir)
        want += [("paths", "models", m.as_posix()), ("paths", "weights", (m / "weights").as_posix())]
    for table, key, value in want:
        if cfg[table].get(key) != value:
            cfg[table][key] = value
            changed.append("%s.%s = %s" % (table, key, value))
    if changed:
        (home / "config.toml").write_text(render_config(cfg), encoding="utf-8", newline="\n")
    return changed


def install_fl_side(home: Path, data_dir: Path | str | None = None) -> str:
    """Copy the generated FL-side script into FL's Hardware folder. An empty data_dir means FL's own user data folder (detect.fl_data_dir), never
    the current folder: an empty config value once put the script under C:\\coproducer\\Settings, where FL never looks (2026-10-25)."""
    src = home / "fl_side" / "device_coproducer.py"
    if not src.is_file():
        return "missing: run coproducer gen first"
    if data_dir in (None, "") or str(data_dir) in ("", "."):
        data_dir = detect.fl_data_dir()
    data_dir = Path(data_dir)
    dst = detect.hardware_dir(data_dir) / "device_coproducer.py"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return str(dst)


# The template projects a fresh install needs (assets/templates), copied into the sandbox once: the FL-saved stem project whose channels a remix
# build replaces, Sytrus fallback patches, and one Serum 2 channel (the serum-mcp sound "CP - Deep Sub") that generated sounds ride on.
TEMPLATES = ("base_project.flp", "sytrus_patches.flp", "serum_carrier.flp")


def install_templates(home: Path, cfg: dict) -> list:
    """Copy each template into sandbox/templates unless it is there already. Returns the files copied."""
    src, dst = home / "assets" / "templates", home / cfg["paths"]["sandbox"] / "templates"
    made = []
    for name in TEMPLATES:
        if (src / name).is_file() and not (dst / name).is_file():
            dst.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src / name, dst / name)
            made.append(str(dst / name))
    return made


def run_setup(home: Path, fl_exe: str | None = None, data_dir: str | None = None) -> dict:
    found = detect.newest_fl_exe()
    exe = fl_exe or (str(found) if found else "")
    data = data_dir or str(detect.fl_data_dir())
    cfg = load_config(home)
    state = write_config(home, exe, data)
    cfg = load_config(home)
    report = {"config": state, "folders_made": ensure_dirs(home, cfg), "fl_exe": cfg["fl"]["exe"] or "(not found, set [fl] exe)",
              "fl_side": install_fl_side(home, Path(cfg["fl"]["data_dir"] or data)), "templates": install_templates(home, cfg)}
    return report


def render_report(r: dict) -> str:
    return "\n".join(["config.toml: %s" % r["config"], "FL executable: %s" % r["fl_exe"], "FL-side script: %s" % r["fl_side"],
                      "folders created: %s" % (", ".join(r["folders_made"]) or "none"),
                      "templates copied: %s" % (", ".join(Path(x).name for x in r.get("templates", [])) or "none needed"), "",
                      "STEP A. Virtual MIDI ports", texts.LOOPMIDI, "", "STEP B. Select the script in FL Studio", texts.MIDI_SETTINGS, "",
                      "STEP C. Check everything:  coproducer doctor   (then  coproducer deps  to compare with the pinned versions)", "STEP D. Install model environments:  coproducer install-models --dry-run", "         Rebuild the host venv from pinned versions:  coproducer install-host --dry-run", "STEP E. Claude Desktop (optional):  coproducer install-desktop --dry-run   (setup also offers it)"])

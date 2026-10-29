"""Look at this machine: FL Studio install, FL data folder, GPU, MIDI ports, tools on PATH. Every function returns plain data."""
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path


def fl_exe_candidates(env: dict | None = None) -> list:
    """FL Studio executables under Program Files. The exe name differs between builds, so both names are tried."""
    env = env if env is not None else os.environ
    roots = [Path(env[k]) / "Image-Line" for k in ("ProgramFiles", "ProgramFiles(x86)") if env.get(k)]
    found = []
    for root in roots:
        for exe in ("FL64.exe", "FL.exe"):
            found += sorted(root.glob("FL Studio*/" + exe))
    return found


def fl_rank(path: Path) -> tuple:
    """Sort key for an FL install folder: its year (20, 21 mean 2020, 2021), with beta builds ranked below releases."""
    m = re.search(r"(\d{2,4})", path.parent.name)
    year = int(m.group(1)) if m else 0
    return (year + 2000 if year < 100 else year, "beta" not in path.parent.name.lower(), path.name)


def newest_fl_exe(found: list | None = None) -> Path | None:
    """The executable in the newest release folder. Plain name order is wrong here: 'FL Studio 21BETA' sorts after 'FL Studio 2026'."""
    found = fl_exe_candidates() if found is None else found
    return max(found, key=fl_rank) if found else None


def documents_dir(home: Path | None = None) -> Path:
    """The user's Documents folder. On Windows it can be moved (OneDrive backup puts it under OneDrive), so the shell's own setting is read
    first: HKCU\\...\\Explorer\\User Shell Folders, value Personal. A given home (tests) or any other system means home/Documents."""
    if home is None and os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as k:
                p = Path(os.path.expandvars(winreg.QueryValueEx(k, "Personal")[0]))
            if p.is_dir():
                return p
        except OSError:
            pass
    return (home or Path.home()) / "Documents"


def fl_data_dir(home: Path | None = None) -> Path:
    """Default user data folder, Documents/Image-Line/FL Studio. The user can override it in config.toml."""
    return documents_dir(home) / "Image-Line" / "FL Studio"


def hardware_dir(data_dir: Path) -> Path:
    return Path(data_dir) / "Settings" / "Hardware" / "coproducer"


def midi_ports() -> dict:
    """Port names mido can see, or an error string when no MIDI backend is installed."""
    try:
        import mido
        return {"out": list(mido.get_output_names()), "in": list(mido.get_input_names())}
    except Exception as e:  # noqa: BLE001 - any backend failure means no ports
        return {"out": [], "in": [], "error": str(e)}


def tool_path(name: str) -> str | None:
    return shutil.which(name)


def free_disk_gb(path: Path) -> float:
    return round(shutil.disk_usage(path).free / 1e9, 1)

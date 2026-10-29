"""Install the runtime services the L5 and L6 modules read: halt flag, desktop, scheduler, LLM endpoint, FL executable."""
from __future__ import annotations

import sys
from pathlib import Path

from .cli import detect
from .config import load_config
from .services import set_service

DATA = Path(__file__).resolve().parent / "data"


class FileHalt:
    """A halt flag shared by every server process of a run: the HALT file in the run folder, or the global one beside the run folders."""

    def __init__(self, run_dir: Path) -> None:
        self.file = Path(run_dir) / "HALT"
        self.global_file = Path(run_dir).parent / "HALT"   # runs/HALT, written by the halt key and `coproducer halt`

    def is_set(self) -> bool:
        return self.file.exists() or self.global_file.exists()

    def set(self) -> None:
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text("halted by an input primitive", encoding="utf-8")


def _anchors(table: dict) -> dict:
    """Anchors are saved as "x,y" window pixels by coproducer calibrate."""
    out = {}
    for k, v in table.items():
        try:
            x, y = (int(t) for t in str(v).split(","))
            out[k] = [x, y]
        except ValueError:
            continue
    return out


def _desktop(cfg: dict):
    """The real Windows backend, or None elsewhere. L6 tools then report E_UNSUPPORTED_API."""
    if sys.platform != "win32":
        return None
    from .desktop_win import WinDesktop
    return WinDesktop()


def _scheduler(home: Path, cfg: dict, ledger):
    from .models.factory import make_worker_factory
    from .models.scheduler import Scheduler
    from .models.spec import load_registry
    from .models.vram import query_vram
    reg_file = home / "models" / "registry.toml"
    if not reg_file.is_file():
        return None
    from . import ollama
    budget = cfg["gpu"].get("budget_mb") or None
    llm = cfg.get("llm") or {}
    release = (lambda: ollama.unload(llm.get("endpoint", ""), llm.get("model", ""))) if llm.get("endpoint") else None
    return Scheduler(load_registry(reg_file), make_worker_factory(cfg, home / "logs"), query_vram, ledger=ledger, budget_mb=budget, release_external=release)


def _procs():
    """Process control for FL Studio on Windows, None elsewhere."""
    if sys.platform != "win32":
        return None
    from .procs import Procs
    return Procs()


_fl_rank = detect.fl_rank


def _newest_fl_exe() -> str | None:
    """The FL Studio executable under Program Files with the newest release folder, or None when there is none."""
    found = detect.newest_fl_exe()
    return str(found) if found else None


def install_services(home: Path, run_dir: Path, ledger=None) -> dict:
    """Read config.toml under home and set every service. Returns the config so callers can reuse it."""
    cfg = load_config(home)
    sandbox = home / cfg["paths"]["sandbox"]
    sandbox.mkdir(parents=True, exist_ok=True)
    set_service("sandbox_root", str(sandbox))
    set_service("recipes_dir", str(home / "gui_recipes") if (home / "gui_recipes").is_dir() else str(DATA / "gui_recipes"))
    set_service("templates_dir", str(home / "gui_templates") if (home / "gui_templates").is_dir() else str(DATA / "gui_templates"))
    set_service("halt", FileHalt(run_dir))
    d = cfg["desktop"]
    set_service("desktop_config", {"display_scale": d.get("display_scale", 0.0), "action_budget": d.get("action_budget", 200),
                                   "allow_unverified": bool(d.get("allow_unverified", False)),
                                   "timeout_scale": float(d.get("timeout_scale", 1.0)), "anchors": _anchors(cfg["anchors"])})
    set_service("desktop", _desktop(cfg))
    data = Path(cfg["fl"].get("data_dir") or detect.fl_data_dir())
    set_service("piano_roll_scripts_dir", str(data / "Settings" / "Piano roll scripts"))
    set_service("fl_exe", cfg["fl"].get("exe") or _newest_fl_exe())
    set_service("fl_not_owned", [str(x) for x in cfg["fl"].get("not_owned", [])])  # plugins this FL edition has only as a trial (they stall renders)
    set_service("procs", _procs())
    set_service("llm", cfg["llm"] if cfg["llm"].get("endpoint") else None)
    set_service("scheduler", _scheduler(home, cfg, ledger))
    set_service("model_files", model_files(home, cfg))
    return cfg


def model_files(home: Path, cfg: dict) -> dict:
    """{key: {"path", "sha256"}} for every pinned weight file of the model stacks (cli/stacks.py), so runners read local, hashed files."""
    from .cli.stacks import STACKS, separator_model, weight_file
    out = {}
    for stack, d in STACKS.items():
        for key in d.get("files") or {}:
            path, sha = weight_file(stack, key, home, cfg)
            out[key] = {"path": path, "sha256": sha, "stack": stack}
    out["roformer_vocals"] = separator_model(home, cfg)
    out["mulan_snapshots"] = dict(STACKS["mir"].get("hf_snapshots", {}))
    return out

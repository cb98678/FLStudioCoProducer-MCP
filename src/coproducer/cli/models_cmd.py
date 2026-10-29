"""coproducer install-models: create each stack's environment and record its interpreter in config.toml."""
from __future__ import annotations

import subprocess
from pathlib import Path

from ..config import load_config, render_config
from .stacks import STACKS, install_plan, snapshots_command, weights_command


def record_env(home: Path, stack: str, python: str) -> None:
    cfg = load_config(home)
    cfg["envs"][stack] = python
    (home / "config.toml").write_text(render_config(cfg), encoding="utf-8", newline="\n")


def record_lock(home: Path, stack: str, python: str, runner=subprocess.run) -> bool:
    """Save the exact installed versions to models/locks/<stack>.txt so the environment can be rebuilt. Never fails an install."""
    try:
        done = runner(["uv", "pip", "freeze", "--python", python], capture_output=True, text=True)
    except OSError:
        return False
    out = getattr(done, "stdout", "") or ""
    if getattr(done, "returncode", 1) != 0 or not out.strip():
        return False
    lock = home / "models" / "locks" / (stack + ".txt")
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(out, encoding="utf-8", newline="\n")
    return True


def run_commands(plan: dict, runner=subprocess.run) -> int:
    for argv, cwd in plan["commands"]:
        done = runner(argv, cwd=cwd)
        if done.returncode != 0:
            return done.returncode
    return 0


def install(home: Path, names: list, dry_run: bool, runner=subprocess.run, weights_only: bool = False, with_optional: bool = False) -> dict:
    """Plan (and unless dry_run, run) the install of each named stack. Returns {stack: {status, commands, notes}}.

    weights_only runs just the downloads (pinned snapshots and weights) of stacks that have them, leaving the environment as it is.
    with_optional also fetches the downloads only optional tools need (the Music Flamingo critic, MuQ-MuLan for reference similarity)."""
    cfg, out = load_config(home), {}
    for stack in names or list(STACKS):
        plan = install_plan(stack, home, cfg)
        if not with_optional and plan.get("optional"):
            skip = set(plan["optional"])
            plan = {**plan, "commands": [c for i, c in enumerate(plan["commands"]) if i not in skip]}
        if weights_only:
            w, sn = weights_command(stack, home, cfg), snapshots_command(stack, home, cfg)
            d = STACKS.get(stack, {})
            keep = [x for x, opt in ((sn, d.get("snapshots_optional")), (w, d.get("weights_optional"))) if x and (with_optional or not opt)]
            plan = {**plan, "commands": [(x, None) for x in keep]}
        row = {"commands": [" ".join(a) + ("   (in %s)" % c if c else "") for a, c in plan["commands"]], "notes": plan["notes"], "python": plan["python"]}
        if dry_run or not plan["commands"]:
            row["status"] = "planned"
        else:
            code = run_commands(plan, runner)
            row["status"] = "installed" if code == 0 else "failed (exit %d)" % code
            if code == 0 and not weights_only:
                record_env(home, stack, plan["python"])
                row["lock"] = record_lock(home, stack, plan["python"], runner)
        out[stack] = row
    return out


def render(rows: dict) -> str:
    lines = []
    for stack, r in rows.items():
        lines += ["[%s] %s" % (stack, r["status"])] + ["    " + c for c in r["commands"]] + ["    note: " + n for n in r["notes"]]
    return "\n".join(lines)

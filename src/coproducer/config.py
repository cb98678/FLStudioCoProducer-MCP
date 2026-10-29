"""config.toml: where things live on this machine. Defaults are safe; setup writes the real values."""
from __future__ import annotations

from pathlib import Path

import tomllib

DEFAULTS: dict = {
    "paths": {"sandbox": "sandbox", "models": "models", "runs": "runs", "weights": "models/weights"},
    "envs": {},
    "midi": {"out": "coproducer-in", "in": "coproducer-out"},
    "bridge": {"max_payload": 200},
    "gpu": {"budget_mb": 0},
    "llm": {"endpoint": "http://127.0.0.1:11434/v1", "model": "gemma4:12b", "timeout_s": 300},
    "fl": {"exe": "", "data_dir": "", "not_owned": []},
    "desktop": {"display_scale": 0.0, "action_budget": 200, "allow_unverified": False, "timeout_scale": 1.0},
    "anchors": {},
}


def merge(base: dict, over: dict) -> dict:
    out = {k: (dict(v) if isinstance(v, dict) else v) for k, v in base.items()}
    for k, v in over.items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def load_config(home: Path | str) -> dict:
    """Defaults merged with <home>/config.toml when it exists."""
    f = Path(home) / "config.toml"
    if not f.exists():
        return merge(DEFAULTS, {})
    with open(f, "rb") as fh:
        return merge(DEFAULTS, tomllib.load(fh))


def render_config(cfg: dict) -> str:
    """Write a config dict as TOML (one level of tables, scalars only)."""
    lines = []
    for table, values in cfg.items():
        lines.append("[%s]" % table)
        for k, v in values.items():
            lines.append("%s = %s" % (k, _toml_value(v)))
        lines.append("")
    return "\n".join(lines)


def _toml_value(v) -> str:
    if isinstance(v, (list, tuple)):
        return "[%s]" % ", ".join(_toml_value(x) for x in v)
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    return '"%s"' % str(v).replace("\\", "/").replace('"', "'")

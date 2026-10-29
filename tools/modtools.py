"""Shared helpers for module generators: write a module folder (source, manifest, test) from parts."""
from __future__ import annotations

import json
from pathlib import Path

from unbundle import expand_manifest  # noqa: E402  (tools/ is on sys.path when generators run)

MODULES = Path(__file__).resolve().parent.parent / "modules"


def write_module(layer_dir: str, name: str, source: str, test: str, meta: dict) -> None:
    """meta holds the key=value pairs that unbundle.expand_manifest understands (layer, summary, side, ...)."""
    lines = [f"{k}={v}" for k, v in meta.items()]
    rel, content = expand_manifest(f"{layer_dir}/{name}", lines)
    d = MODULES / layer_dir / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "module.toml").write_text(content, encoding="utf-8")
    (d / f"{name}.py").write_text(source, encoding="utf-8")
    (d / f"test_{name}.py").write_text(test, encoding="utf-8")


def schema(props: dict, required: list[str]) -> str:
    return json.dumps({"type": "object", "required": required, "properties": props,
                       "additionalProperties": False}, separators=(",", ":"))

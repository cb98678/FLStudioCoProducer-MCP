"""Model registry: data about each local model, read from models/registry.toml."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import tomllib

ROLES = ("generate", "separate", "transcribe", "critique", "ground_gui", "brain", "analyze", "test")


@dataclass(frozen=True)
class ModelSpec:
    name: str
    role: str
    stack: str
    vram_typical_mb: int = 0
    vram_min_mb: int = 0
    variants: tuple = ()
    default_variant: str = ""
    optional: bool = False
    fallback: str = ""
    license: str = ""
    runner: str = ""
    smoke: str = ""
    extra: dict = field(default_factory=dict)


def _spec(name: str, d: dict) -> ModelSpec:
    vram = d.get("vram_gb", {})
    known = {"role", "stack", "vram_gb", "variants", "default_variant", "optional", "fallback", "license", "runner", "smoke"}
    return ModelSpec(name=name, role=d["role"], stack=d["stack"], vram_typical_mb=int(vram.get("typical", 0) * 1024),
                     vram_min_mb=int(vram.get("min", 0) * 1024), variants=tuple(d.get("variants", ())),
                     default_variant=d.get("default_variant", ""), optional=bool(d.get("optional", False)),
                     fallback=d.get("fallback", ""), license=d.get("license", ""), runner=d.get("runner", ""),
                     smoke=d.get("smoke", ""), extra={k: v for k, v in d.items() if k not in known})


def load_registry(path: Path | str) -> dict[str, ModelSpec]:
    """Read the registry file; raises ValueError with a plain message when a model entry is malformed."""
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    out = {}
    for name, d in raw.get("models", {}).items():
        if d.get("role") not in ROLES or "stack" not in d:
            raise ValueError("model %r needs a stack and a role from %s" % (name, ", ".join(ROLES)))
        out[name] = _spec(name, d)
    return out

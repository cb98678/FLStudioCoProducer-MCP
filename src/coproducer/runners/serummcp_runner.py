"""serum-mcp's own preset writer (https://github.com/Celian-mrc/serum-mcp, MIT), run inside its environment (the clone's .venv), so the
co-producer can generate a preset without going through a chat: the same code its MCP tool generate_preset runs.

The folders come with each request (presets_dir, tables_dir, samples_dir) and are set as the variables serum-mcp reads
(SERUM_PRESETS_PATH and the rest); the caller keeps every preset in a subfolder named sandbox.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner_common import RunnerError, serve  # noqa: E402

ENV = {"presets_dir": "SERUM_PRESETS_PATH", "tables_dir": "SERUM_TABLES_PATH", "samples_dir": "SERUM_SAMPLES_PATH"}


def _folders(a: dict) -> None:
    for k, var in ENV.items():
        if a.get(k):
            os.environ[var] = a[k]


def preset(a: dict) -> dict:
    """spec: a serum-mcp PresetSpec as a dict; subfolder under the presets folder. Returns the written path and the files it depends on."""
    from pydantic import ValidationError
    from serum_mcp.generation.spec import PresetSpec
    from serum_mcp.tools.generate_preset import generate_preset
    _folders(a)
    try:
        spec = PresetSpec.model_validate(a["spec"])
    except ValidationError as e:
        raise RunnerError("E_ARG", "the preset spec does not validate: %s" % e) from e
    out = generate_preset(spec, subfolder=a.get("subfolder") or None)
    lines = [x for x in str(out).splitlines() if x.strip()]
    deps = [x.strip()[2:] for x in lines[1:] if x.strip().startswith("- ")]
    return {"path": lines[0].strip(), "depends_on": deps}


def describe(a: dict) -> dict:
    from serum_mcp.tools.describe_preset import describe_preset
    _folders(a)
    return {"text": str(describe_preset(a["path"]))}


if __name__ == "__main__":
    serve({"load": lambda a: {"loaded": "serum-mcp"}, "unload": lambda a: True, "ping": lambda a: "pong", "preset": preset, "describe": describe})

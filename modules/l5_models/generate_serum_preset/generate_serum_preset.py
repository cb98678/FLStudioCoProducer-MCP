from __future__ import annotations

from pathlib import Path

from coproducer import call, serumstate
from coproducer.result import Result, fail, ok

USER_PRESETS = Path("Documents") / "Xfer" / "Serum 2 Presets" / "Presets" / "User"


def generate_serum_preset(spec: dict, subfolder: str, presets_dir: str = "") -> Result:
    """Write spec (serum-mcp's PresetSpec: name, description, oscillators, envelopes, filters, mod routes, effects) as a .SerumPreset
    with serum-mcp's generator (the serummcp model), under presets_dir/subfolder. presets_dir is Serum 2's user preset folder (default
    Documents\\\\Xfer\\\\Serum 2 Presets\\\\Presets\\\\User); subfolder starts with sandbox, so the person's own presets are never touched.

    Errors: E_ARG (a subfolder outside sandbox, or a spec serum-mcp refuses), E_NOT_FOUND (no preset folder), E_MODEL, E_NOT_VERIFIED.
    """
    parts = subfolder.replace("\\\\", "/").split("/")
    if parts[0] != "sandbox" or ".." in parts:
        return fail("E_ARG", "the preset subfolder must start with sandbox and stay inside it")
    base = Path(presets_dir) if presets_dir else Path.home() / USER_PRESETS
    if not base.is_dir():
        return fail("E_NOT_FOUND", "no Serum 2 user preset folder at %s" % base)
    root = base.parent.parent
    got = call("run_model_op", model="serummcp", op="preset", timeout_s=180,
               args={"spec": spec, "subfolder": "/".join(parts), "presets_dir": str(base),
                     **{k: str(root / d) for k, d in (("tables_dir", "Tables"), ("samples_dir", "Samples")) if (root / d).is_dir()}})
    if not got.ok:
        return got
    path = Path(got.value["path"])
    inside = path.resolve().is_relative_to((base / Path(*parts)).resolve())
    try:
        name = serumstate.read_container(path.read_bytes())[0].get("presetName") if path.is_file() else None
    except (serumstate.SerumStateError, ValueError):
        name = None
    if not inside or name != spec["name"]:
        return fail("E_NOT_VERIFIED", "the preset was not written where expected, or reads back with another name", path=str(path), name=name)
    return ok({"path": str(path), "depends_on": got.value.get("depends_on", []), "name": name}, verified=True)

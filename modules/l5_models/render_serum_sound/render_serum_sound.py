from __future__ import annotations

from pathlib import Path

from coproducer import call, flpfile, serumstate
from coproducer.result import Result, fail, ok
from coproducer.services import get_service

TAIL_S = 1.5


def _request_state(preset_path: str, state_path: str, template_project: str) -> tuple[bytes | None, str]:
    """(the channel state to play, why not): a saved one as it is, or a preset put on a Serum 2 channel of the template project."""
    if state_path:
        return Path(state_path).read_bytes(), ""
    f = flpfile.Flp.load(template_project)
    carrier = next((b for b in (f.plugin_state(c) for c in f.channel_ids()) if b and serumstate.is_serum2(b)), None)
    if carrier is None:
        return None, "no Serum 2 channel in %s to carry the preset" % Path(template_project).name
    return serumstate.inject_preset(carrier, Path(preset_path).read_bytes(), str(Path(preset_path).resolve())), ""


def render_serum_sound(notes: list, out_path: str, preset_path: str = "", state_path: str = "", bpm: float = 120.0,
                       template_project: str = "") -> Result:
    """Play notes (beats at bpm) on a .SerumPreset or a saved channel state through the serum model (Serum 2 under pedalboard, no FL).
    Writes out_path (a WAV in the sandbox) and out_path.serumstate, the state Serum saved after loading it (build_remix_project's
    serum_states). template_project holds a Serum 2 channel to carry a preset (default sandbox\\serum\\serum_sounds.flp).

    Errors: E_ARG, E_NOT_FOUND, E_SANDBOX_VIOLATION, E_MODEL (install it: coproducer install-models serum).
    """
    if bool(preset_path) == bool(state_path):
        return fail("E_ARG", "give preset_path or state_path, one of them")
    root = str(get_service("sandbox_root"))
    chk = call("check_sandbox_path", path=out_path, sandbox_root=root)
    if not chk.ok:
        return chk
    src = preset_path or state_path
    template = template_project or str(Path(root) / "serum" / "serum_sounds.flp")
    for p in (src,) + (() if state_path else (template,)):
        if not Path(p).is_file():
            return fail("E_NOT_FOUND", "no file at %s" % p)
    try:
        blob, why = _request_state(preset_path, state_path, template)
    except (serumstate.SerumStateError, flpfile.FlpError, ValueError) as e:
        blob, why = None, str(e)
    if blob is None or not serumstate.is_serum2(blob):
        return fail("E_ARG", why or "%s is not a Serum 2 channel state" % Path(src).name)
    out = Path(out_path)
    req = out.with_suffix(".request.serumstate")
    req.parent.mkdir(parents=True, exist_ok=True)
    req.write_bytes(blob)
    beat = 60.0 / bpm
    rows = [[n["start"] * beat, n["duration"] * beat, n["pitch"], n.get("velocity", 100)] for n in notes]
    end = max(r[0] + r[1] for r in rows) + TAIL_S
    got = call("run_model_op", model="serum", op="render", timeout_s=300,
               args={"state_in": str(req), "notes": rows, "seconds": end, "out_wav": str(out), "state_out": str(out.with_suffix(".serumstate"))})
    if not got.ok:
        return got
    v = got.value
    return ok({"wav": v["out_wav"], "state": v["state_out"], "rms_db": v["rms_db"], "peak": v["peak"], "preset": serumstate.preset_name(blob)},
              verified=v["rms_db"] > -60.0)

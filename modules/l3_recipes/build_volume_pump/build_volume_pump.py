from __future__ import annotations

from coproducer import call, flpfile, partmix, pump
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def _kick(f: flpfile.Flp) -> int | None:
    """The first channel whose name says kick and that has notes (a Layer channel counts: the notes are on it)."""
    used = {n[1] for ns in f.pattern_notes().values() for n in ns}
    return next((c for c in f.channel_ids() if c in used and partmix.role_of(f.channel_info(c)["name"] or "") == "kick"), None)


def build_volume_pump(project: str, out_project: str, targets: list, kick_channel: int = -1, row: int = 0) -> Result:
    """Make inserts pump on the kick without a compressor sidechain: a neutral Fruity Balance in a free slot (the last) of each target, and a clip on
    its volume that dips on every kick note, holds a tenth of a beat and is back by 0.3 beat (the reference's measured pump). targets: [{"insert",
    "depth": "full" (-24 dB, sub), "deep" (-16 dB, music) or "medium" (-8 dB, FX), or "depth_db", "slot"}]. row: playlist row for the clips
    (default below every used row). Writes a sandbox copy of an FL-saved project; check a render with measure_pump_depth against the unpumped part.
    Errors: E_SANDBOX_VIOLATION, E_ARG, E_IO."""
    chk = call("check_sandbox_path", path=out_project, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    if not targets:
        return fail("E_ARG", "give at least one target insert")
    try:
        f = flpfile.Flp.load(project)
        kick = kick_channel if kick_channel >= 0 else _kick(f)
        if kick is None:
            return fail("E_ARG", "no kick channel with notes found; pass kick_channel")
        rep = pump.build_pump(f, kick, targets, row or pump.first_free_row(f))
        f.save(out_project)
        back = flpfile.Flp.load(out_project)
    except flpfile.FlpError as e:
        return fail("E_ARG", str(e))
    except OSError as e:
        return fail("E_IO", str(e))
    placed = all(pump.fxlib.slot_plugin(back, t["insert"], t["slot"]) == "Fruity Balance" and t["clip"] in back.channel_ids() for t in rep["targets"])
    return ok(dict(rep, kick=kick, out_project=out_project), verified=placed)

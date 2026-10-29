from __future__ import annotations

from coproducer import call, flpfile, layers
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def build_layer_channel(project: str, out_project: str, name: str, children: list, stack: list | None = None, take_notes_from: str = "") -> Result:
    """Add a Layer channel that plays several channels from one set of notes, as the Future House reference builds its kick (three samples on one
    insert) and bass (a sub and a mid bass), to a sandbox copy. children: channel ids or names; stack: [{"sample", "name", "like", "pitch_cents",
    "volume", "band": full, top or body, "pan": -100..100}] new samplers copied from `like` with another file, added to the layer; take_notes_from: the channel
    whose notes the layer takes over (default the first child), so nothing plays twice. Errors: E_SANDBOX_VIOLATION, E_ARG, E_IO."""
    chk = call("check_sandbox_path", path=out_project, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    try:
        f = flpfile.Flp.load(project)
        kids = [layers.find_channel(f, c) for c in children]
        added = [layers.stack_sample(f, layers.find_channel(f, s.get("like", kids[0] if kids else 0)), s["sample"], s.get("name") or s["sample"].replace("\\", "/").rsplit("/", 1)[-1].rsplit(".", 1)[0],
                                     int(s.get("pitch_cents", 0)), s.get("volume"), s.get("band", "full"), float(s.get("pan", 0)) / 100.0) for s in (stack or [])]
        rep = layers.add_layer(f, name, kids + added, take_notes_from or None)
        f.save(out_project)
        back = flpfile.Flp.load(out_project).layer_children(rep["layer"])
    except (flpfile.FlpError, KeyError, IndexError) as e:
        return fail("E_ARG", str(e))
    except OSError as e:
        return fail("E_IO", str(e))
    return ok(dict(rep, out_project=out_project, stacked=added), verified=back == rep["children"])

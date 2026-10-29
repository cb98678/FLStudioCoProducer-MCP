from __future__ import annotations

from coproducer import call, flpfile, fxsynth, pump
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def add_transition_synths(project: str, out_project: str, synths: list, key: str = "A", row: int = 0) -> Result:
    """Add editable risers and transition synths around section changes, 3x Osc patches from the Future House reference: noise_riser (ends on
    the moment), noise_downlifter (starts on it) and impact_synth (a one-beat chord in the key on it). synths: [{"kind", "at": marker name or bar,
    "bars", "insert", "volume"}]; each gets its own channel, pattern and clip on `row` (default the first free row) and plays through the FX insert unless
    `insert` is given. Writes a sandbox copy. Errors: E_SANDBOX_VIOLATION, E_ARG, E_IO."""
    chk = call("check_sandbox_path", path=out_project, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    if not synths:
        return fail("E_ARG", "give at least one transition synth")
    try:
        f = flpfile.Flp.load(project)
        lane = row or pump.first_free_row(f)
        done = [fxsynth.add_fx_synth(f, s["kind"], s["at"], lane, int(s.get("insert", -1)), float(s.get("bars", 0)), key, s.get("volume")) for s in synths]
        f.save(out_project)
        g = flpfile.Flp.load(out_project)
        back = all(d["channel"] in g.channel_ids() and d["pattern"] in g.pattern_ids() for d in done)
    except (flpfile.FlpError, KeyError) as e:
        return fail("E_ARG", str(e))
    except OSError as e:
        return fail("E_IO", str(e))
    return ok({"out_project": out_project, "row": lane, "placed": done}, verified=back)

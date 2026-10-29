from __future__ import annotations

from coproducer import call, flpfile, pump, transitions
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def add_transition_automation(project: str, out_project: str, transitions_list: list, row: int = 0) -> Result:
    """Add transition automation around section changes, as the Future House reference does: filter_sweep (high-pass rises into the moment, on
    the music bus), reverb_throw (wet swells, dry dips, cut on it), pitch_rise (`semitones` up into it), fade_in, gap, lowpass_open (a part's
    low-pass opens into it), lowpass_dip, filter_wobble (cutoff swings every `period` beats from it for `bars`), fx_swell (drum-bus flanger in), and Gross Beat fills on
    the last bar: stutter_fill, reverse_fill, tape_stop.
    transitions_list: [{"recipe", "at": marker or bar, "insert" or "channel", "bars", "beats", "semitones", "period", "low"}]. Plugins come from
    the effect library, one named instance per job. Writes a sandbox copy of an FL-saved project. Errors: E_SANDBOX_VIOLATION, E_ARG, E_IO."""
    chk = call("check_sandbox_path", path=out_project, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    if not transitions_list:
        return fail("E_ARG", "give at least one transition")
    try:
        f = flpfile.Flp.load(project)
        lane = row or pump.first_free_row(f)
        done = [transitions.add_transition(f, t["recipe"], t["at"], lane, int(t.get("insert", -1)), int(t.get("channel", -1)), float(t.get("bars", 4)),
                                           float(t.get("beats", 2)), int(t.get("semitones", 12)), float(t.get("period", 1)),
                                           float(t.get("low", 0.4))) for t in transitions_list]
        f.save(out_project)
        back = flpfile.Flp.load(out_project).channel_ids()
    except flpfile.FlpError as e:
        return fail("E_ARG", str(e))
    except OSError as e:
        return fail("E_IO", str(e))
    return ok({"out_project": out_project, "row": lane, "placed": done}, verified=all(d["clip"] in back for d in done))

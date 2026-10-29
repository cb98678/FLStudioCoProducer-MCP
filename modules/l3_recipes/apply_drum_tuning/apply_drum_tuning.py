from __future__ import annotations

from coproducer import call, drumtune, flpfile, layers
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def apply_drum_tuning(project: str, out_project: str, key: str, channels: list | None = None, tune_to: str = "root_fifth", dry_run: bool = False) -> Result:
    """Tune drum samples to the song's key with each channel's pitch knob, as the Future House reference does, in a sandbox copy. Reads each
    sample's pitch from its file, adds the note its pattern plays and the knob, and moves it to the nearest root or fifth (tune_to root_fifth, at
    most 3.5 semitones) or root. channels: ids or names (default kicks, toms and 808s); samples with no clear pitch are left alone and listed.
    dry_run reports without writing. Errors: E_SANDBOX_VIOLATION, E_ARG, E_IO."""
    chk = call("check_sandbox_path", path=out_project, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    try:
        f = flpfile.Flp.load(project)
        ids = [layers.find_channel(f, c) for c in channels] if channels else drumtune.default_channels(f)
        rows = drumtune.plan(f, ids, key, tune_to, get_service("fl_exe"))
        if dry_run:
            return ok({"tuned": [], "plan": rows}, verified=None)
        drumtune.apply(f, rows)
        f.save(out_project)
        g = flpfile.Flp.load(out_project)
        done = [r for r in rows if r.get("cents") is not None]
        back = all(g.channel_pitch(r["channel"])[0] == r["cents"] for r in done)
    except (flpfile.FlpError, KeyError) as e:
        return fail("E_ARG", str(e))
    except (OSError, RuntimeError) as e:
        return fail("E_IO", str(e))
    return ok({"out_project": out_project, "tuned": [r["channel"] for r in done], "plan": rows}, verified=back)

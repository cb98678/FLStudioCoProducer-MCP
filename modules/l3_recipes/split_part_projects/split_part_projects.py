from __future__ import annotations

from coproducer import call, flpfile, partmix
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def split_part_projects(project: str, out_dir: str, bypass_master: bool = False) -> Result:
    """Write one solo project per mixer track (every other track's channels disabled) plus manifest.json into a sandbox folder. Render the folder with
    render_folder_via_cli, then measure_part_levels. A Layer channel that triggers the part, controller channels (an Envelope Controller pump, MIDI
    Out) and automation clips stay on so the part sounds as in the mix. bypass_master switches the master's effects off in every solo, so a master
    limiter does not shape the part levels; keep it the same for a profile and the builds compared with it. The source project is only read."""
    chk = call("check_sandbox_path", path=out_dir, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    try:
        man = partmix.split_to_dir(project, out_dir, bypass_master)
    except (OSError, flpfile.FlpError) as e:
        return fail("E_IO", str(e))
    return ok({"projects": len(man["tracks"]), "tracks": man["tracks"], "out_dir": out_dir}, verified=len(man["tracks"]) > 0)

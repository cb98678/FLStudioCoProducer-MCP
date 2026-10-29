"""Set part levels from solo renders against a profile taken from a mix the person approved.

    python tools/part_levels.py split PROJECT.flp SOLO_DIR [--bypass-master]  one solo project per mixer track + manifest.json
    (render the folder: render_folder_via_cli folder=SOLO_DIR out_dir=RENDER_DIR)
    python tools/part_levels.py measure SOLO_DIR RENDER_DIR [--save-profile profile.json]
    python tools/part_levels.py plan PROJECT.flp SOLO_DIR RENDER_DIR PROFILE.json OUT.flp

`measure` prints each part's solo loudness and level relative to the kick, and can save that as a profile (the approved mix). `plan` compares a new
project's measured levels with a profile and writes OUT.flp with the fader changes applied (capped at 12 dB a pass; run split, render, plan again to confirm).
Paths must sit under a folder named sandbox. Roles come from channel names (partmix.ROLE_WORDS).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from coproducer import flpfile, partmix  # noqa: E402


def _need_sandbox(p: str) -> None:
    if "sandbox" not in [x.lower() for x in os.path.abspath(p).split(os.sep)]:
        sys.exit("refusing %s: must be under a folder named sandbox" % p)


def _measured(solo_dir: str, render_dir: str):
    man, levels, roles, missing = partmix.measure_dir(solo_dir, render_dir)
    for name in missing:
        print("no render for", name)
    return man, levels, roles


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=("split", "measure", "plan"))
    ap.add_argument("args", nargs="+")
    ap.add_argument("--save-profile", default="")
    ap.add_argument("--bypass-master", action="store_true", help="split: switch the master's effects off in every solo")
    a = ap.parse_args()
    if a.mode == "split":
        project, out = a.args
        _need_sandbox(out)
        man = partmix.split_to_dir(project, out, a.bypass_master)
        tracks = man["tracks"]
        print("wrote %d solo projects to %s" % (len(tracks), out))
        return 0
    if a.mode == "measure":
        solo_dir, render_dir = a.args
        man, levels, roles = _measured(solo_dir, render_dir)
        prof = partmix.profile_from(levels, roles)
        for t in sorted(levels):
            print("track %2d %-6s %6.1f LUFS  peak %6.1f dBFS  rel kick %s" % (t, roles[t], levels[t]["lufs"], levels[t]["peak_db"], prof["relative_db"].get(roles[t])))
        print("relative to kick (dB):", prof["relative_db"])
        if a.save_profile:
            _need_sandbox(a.save_profile)
            Path(a.save_profile).write_text(partmix.dump(prof), encoding="utf-8")
            print("saved", a.save_profile)
        return 0
    project, solo_dir, render_dir, profile, out = a.args
    _need_sandbox(out)
    f = flpfile.Flp.load(project)
    man, levels, roles = _measured(solo_dir, render_dir)
    prof = json.loads(Path(profile).read_text(encoding="utf-8"))
    changes = partmix.plan_changes(levels, roles, partmix.faders_db(f, list(levels)), prof)
    for c in changes:
        print("track %2d %-6s %6.1f LUFS -> fader %+.1f dB to %.1f dB" % (c["track"], c["role"], c["measured_lufs"], c["role_delta_db"], c["new_db"]))
    if not changes:
        print("every part is within %.1f dB of the profile" % partmix.TOLERANCE_DB)
    partmix.apply_changes(f, changes)
    f.save(out)
    print("wrote", out, "with", len(changes), "fader changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

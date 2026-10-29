from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def restore_track_values(snapshot: dict) -> Result:
    """Put mixer track settings back to the values in a snapshot, using verified writes.

    Only values that differ are written. Fails with E_NOT_VERIFIED, listing each failure, if any write does not stick.
    """
    saved = snapshot.get("tracks", {})
    setters = {
        "volume": lambda i, v: call("set_track_volume_verified", index=i, volume=v),
        "pan": lambda i, v: call("set_track_pan_verified", index=i, pan=v),
        "stereo": lambda i, v: call("set_track_stereo_sep_verified", index=i, separation=v),
        "mute": lambda i, v: call("mute_track_verified", index=i, muted=v),
        "solo": lambda i, v: call("solo_track_verified", index=i, solo=v),
        "name": lambda i, v: call("set_track_name_verified", index=i, name=v),
    }
    cur = call("snapshot_tracks", track_limit=len(saved))
    diff = call("diff_state_snapshots", before=cur.value if cur.ok else {}, after=saved) if cur.ok else cur
    if not diff.ok:
        return diff
    applied, failed = 0, []
    for c in diff.value:
        idx, key = c["path"].split(".", 1)
        r = setters[key](int(idx), c["after"])
        applied, failed = applied + r.ok, failed + ([] if r.ok else [{"path": c["path"], "error": r.error.code}])
    if failed:
        return fail("E_NOT_VERIFIED", "%d track values did not restore" % len(failed), failed=failed, applied=applied)
    return ok({"applied": applied}, verified=True)

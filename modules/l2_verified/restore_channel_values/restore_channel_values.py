from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def restore_channel_values(snapshot: dict) -> Result:
    """Put channel volume, pan, mute and target track back to the values in a snapshot, using verified writes.

    Fails with E_NOT_VERIFIED, listing each failure, if any write does not stick.
    """
    saved = snapshot.get("channels", {})
    setters = {
        "volume": lambda i, v: call("set_channel_volume_verified", index=i, volume=v),
        "pan": lambda i, v: call("set_channel_pan_verified", index=i, pan=v),
        "mute": lambda i, v: call("mute_channel_verified", index=i, muted=v),
        "target": lambda i, v: call("route_channel_to_track_verified", channel_index=i, track_index=v),
    }
    cur = call("snapshot_channels")
    diff = call("diff_state_snapshots", before=cur.value, after=saved) if cur.ok else cur
    if not diff.ok:
        return diff
    applied, failed = 0, []
    for c in diff.value:
        idx, key = c["path"].split(".", 1)
        r = setters[key](int(idx), c["after"]) if key in setters else None
        if r is None:
            continue
        applied, failed = applied + r.ok, failed + ([] if r.ok else [{"path": c["path"], "error": r.error.code}])
    if failed:
        return fail("E_NOT_VERIFIED", "%d channel values did not restore" % len(failed), failed=failed, applied=applied)
    return ok({"applied": applied}, verified=True)

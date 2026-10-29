from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, first_error, ok


def rollback_to(snapshot: dict) -> Result:
    """Restore mixer tracks, channels and tempo to a snapshot, then re-read everything to prove it matches.

    Errors: E_NOT_VERIFIED with the leftover differences. If FL cannot get back to the snapshot, reopen the saved copy.
    """
    restored = call("restore_state_values", snapshot=snapshot)
    now = call("snapshot_state", track_limit=len(snapshot.get("tracks", {})), include_channels="channels" in snapshot)
    bad = first_error(restored, now)
    if bad:
        return bad
    left = call("diff_state_snapshots", before=snapshot, after=now.value)
    if left.ok and left.value:
        return fail("E_NOT_VERIFIED", "%d values still differ after rollback" % len(left.value), left=left.value[:20])
    return ok({"applied": restored.value["applied"]}, verified=True)

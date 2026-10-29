from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, first_error, ok


def undo_last_verified(track_limit: int = 0) -> Result:
    """Undo one step in FL and confirm that some mixer track value changed back.

    The check compares track snapshots before and after, so it only sees mixer changes.
    Errors: E_NOT_VERIFIED when nothing changed.
    """
    before = call("snapshot_tracks", track_limit=track_limit)
    w = call("op_general_undo")
    after = call("snapshot_tracks", track_limit=track_limit)
    bad = first_error(before, w, after)
    if bad:
        return bad
    diff = call("diff_state_snapshots", before=before.value, after=after.value)
    if not diff.ok:
        return diff
    if not diff.value:
        return fail("E_NOT_VERIFIED", "undo ran but no mixer track value changed", undo_result=w.value)
    return ok(diff.value, verified=True)

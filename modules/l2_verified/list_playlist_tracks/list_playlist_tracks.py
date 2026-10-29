from __future__ import annotations

from coproducer import call
from coproducer.result import Result, first_error, ok


def list_playlist_tracks(only_named: bool = True, limit: int = 500) -> Result:
    """List playlist tracks (numbered from 1) with name and mute state.

    FL has hundreds of playlist tracks, so only_named skips those still called 'Track N'.
    """
    n = call("op_playlist_track_count")
    if not n.ok:
        return n
    rows = []
    for i in range(1, min(n.value, limit) + 1):
        name = call("op_playlist_get_track_name", index=i)
        muted = call("op_playlist_is_track_muted", index=i)
        bad = first_error(name, muted)
        if bad:
            return bad
        if not (only_named and name.value == "Track %d" % i):
            rows.append({"index": i, "name": name.value, "muted": muted.value})
    return ok(rows, total=n.value)

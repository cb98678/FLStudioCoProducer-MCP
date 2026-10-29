from __future__ import annotations

from coproducer import call
from coproducer.result import Result, first_error, ok


def list_tracks_summary(start: int = 0, count: int = 0, only_named: bool = False) -> Result:
    """List mixer tracks with name, volume (raw and dB), pan, mute and solo. count 0 means all from start.

    only_named skips tracks that still have FL's default name.
    """
    n = call("op_mixer_track_count")
    if not n.ok:
        return n
    stop = n.value if count == 0 else min(n.value, start + count)
    rows = []
    for i in range(start, stop):
        got = [call("op_mixer_get_track_name", index=i), call("op_mixer_get_track_volume", index=i),
               call("op_mixer_get_track_volume", index=i, mode=1), call("op_mixer_get_track_pan", index=i),
               call("op_mixer_is_track_muted", index=i), call("op_mixer_is_track_solo", index=i)]
        bad = first_error(*got)
        if bad:
            return bad
        if only_named and got[0].value in ("Master", "Insert %d" % i):
            continue
        rows.append({"index": i, "name": got[0].value, "volume": got[1].value, "volume_db": got[2].value,
                     "pan": got[3].value, "muted": got[4].value, "solo": got[5].value})
    return ok(rows, total=n.value)

from __future__ import annotations

from coproducer import call
from coproducer.result import Result, first_error, ok


def snapshot_tracks(track_limit: int = 0) -> Result:
    """Capture name, volume, pan, stereo separation, mute and solo of mixer tracks 0 up to track_limit.

    track_limit 0 means every track. Keys are track indexes as text, so the result is JSON friendly.
    """
    n = call("op_mixer_track_count")
    if not n.ok:
        return n
    out = {}
    for i in range(n.value if track_limit == 0 else min(track_limit, n.value)):
        got = [call("op_mixer_get_track_name", index=i), call("op_mixer_get_track_volume", index=i),
               call("op_mixer_get_track_pan", index=i), call("op_mixer_get_track_stereo_sep", index=i),
               call("op_mixer_is_track_muted", index=i), call("op_mixer_is_track_solo", index=i)]
        bad = first_error(*got)
        if bad:
            return bad
        out[str(i)] = dict(zip(("name", "volume", "pan", "stereo", "mute", "solo"), (g.value for g in got)))
    return ok(out)

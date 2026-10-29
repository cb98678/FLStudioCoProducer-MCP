from __future__ import annotations

from coproducer import call
from coproducer.result import Result, first_error, ok


def snapshot_channels() -> Result:
    """Capture name, volume, pan, mute and target mixer track of every channel into a dictionary.

    Keys are channel indexes as text.
    """
    n = call("op_channels_channel_count")
    if not n.ok:
        return n
    out = {}
    for i in range(n.value):
        got = [call("op_channels_get_channel_name", index=i), call("op_channels_get_channel_volume", index=i),
               call("op_channels_get_channel_pan", index=i), call("op_channels_is_channel_muted", index=i),
               call("op_channels_get_target_fx_track", index=i)]
        bad = first_error(*got)
        if bad:
            return bad
        out[str(i)] = dict(zip(("name", "volume", "pan", "mute", "target"), (g.value for g in got)))
    return ok(out)

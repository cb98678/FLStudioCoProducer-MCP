from __future__ import annotations

from coproducer import call
from coproducer.result import Result, first_error, ok


def list_channels_summary() -> Result:
    """List channels with name, type, volume, pan, mute state and the mixer track they feed.

    Errors: any read error.
    """
    n = call("op_channels_channel_count")
    if not n.ok:
        return n
    rows = []
    for i in range(n.value):
        got = [call("op_channels_get_channel_name", index=i), call("op_channels_get_channel_type", index=i),
               call("op_channels_get_channel_volume", index=i), call("op_channels_get_channel_pan", index=i),
               call("op_channels_is_channel_muted", index=i), call("op_channels_get_target_fx_track", index=i)]
        bad = first_error(*got)
        if bad:
            return bad
        rows.append(dict(zip(("name", "type", "volume", "pan", "muted", "target_track"), (g.value for g in got)), index=i))
    return ok(rows)

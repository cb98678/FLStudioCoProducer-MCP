from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def route_channel_to_track_verified(channel_index: int, track_index: int) -> Result:
    """Route a channel to a mixer track and confirm by reading the target back.

    Errors: E_ARG for bad input or an FL-side failure, E_NOT_VERIFIED when the readback differs.
    """
    w = call("op_channels_set_target_fx_track", channelIndex=channel_index, mixerIndex=track_index)
    if not w.ok:
        return w
    r = call("op_channels_get_target_fx_track", index=channel_index)
    if not r.ok:
        return r
    if r.value != track_index:
        return fail("E_NOT_VERIFIED", "wrote %r but read back %r" % (track_index, r.value), wrote=track_index, read=r.value)
    return ok(r.value, verified=True)

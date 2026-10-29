from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def set_channel_volume_verified(index: int, volume: float) -> Result:
    """Set a channel's volume from 0.0 to 1.0 and confirm by reading it back.

    Errors: E_ARG for bad input or an FL-side failure, E_NOT_VERIFIED when the readback differs.
    """
    w = call("op_channels_set_channel_volume", index=index, volume=volume)
    if not w.ok:
        return w
    r = call("op_channels_get_channel_volume", index=index)
    if not r.ok:
        return r
    if abs(r.value - volume) > 0.002:
        return fail("E_NOT_VERIFIED", "wrote %r but read back %r" % (volume, r.value), wrote=volume, read=r.value)
    return ok(r.value, verified=True)

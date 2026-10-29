from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def mute_channel_verified(index: int, muted: bool) -> Result:
    """Set a channel's mute state to an explicit value and confirm it.

    Errors: E_ARG for bad input or an FL-side failure, E_NOT_VERIFIED when the readback differs.
    """
    w = call("op_channels_mute_channel", index=index, value=1 if muted else 0)
    if not w.ok:
        return w
    r = call("op_channels_is_channel_muted", index=index)
    if not r.ok:
        return r
    if r.value != muted:
        return fail("E_NOT_VERIFIED", "wrote %r but read back %r" % (muted, r.value), wrote=muted, read=r.value)
    return ok(r.value, verified=True)

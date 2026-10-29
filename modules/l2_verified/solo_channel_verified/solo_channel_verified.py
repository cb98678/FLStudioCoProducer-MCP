from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def solo_channel_verified(index: int, solo: bool) -> Result:
    """Set a channel's solo state to an explicit value and confirm.

    FL only offers a toggle for channel solo, so the state is read first.
    """
    cur = call("op_channels_is_channel_solo", index=index)
    if not cur.ok or cur.value == solo:
        return cur if not cur.ok else ok(solo, verified=True, changed=False)
    w = call("op_channels_solo_channel", index=index)
    if not w.ok:
        return w
    r = call("op_channels_is_channel_solo", index=index)
    if not r.ok:
        return r
    if r.value != solo:
        return fail("E_NOT_VERIFIED", "solo is %r, wanted %r" % (r.value, solo), read=r.value)
    return ok(r.value, verified=True, changed=True)

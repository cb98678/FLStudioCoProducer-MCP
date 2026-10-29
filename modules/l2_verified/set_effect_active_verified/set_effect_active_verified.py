from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def set_effect_active_verified(index: int, slot_index: int, active: bool) -> Result:
    """Turn one mixer effect slot on (processing) or off (bypassed) and confirm it by reading the state back.

    Errors: E_ARG for a bad track or slot, E_NOT_VERIFIED when the readback differs.
    """
    w = call("op_mixer_set_plugin_mute_state", index=index, slotIndex=slot_index, value=1 if active else 0)
    if not w.ok:
        return w
    r = call("op_mixer_get_plugin_mute_state", index=index, slotIndex=slot_index)
    if not r.ok:
        return r
    if bool(r.value) != active:
        return fail("E_NOT_VERIFIED", "wrote active=%r but read back %r" % (active, r.value), wrote=active, read=r.value)
    return ok(bool(r.value), verified=True)

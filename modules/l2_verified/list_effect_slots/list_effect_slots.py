from __future__ import annotations

from coproducer import call
from coproducer.result import Result, ok


def list_effect_slots(index: int, slots: int = 10) -> Result:
    """List the effect slots on a mixer track: plugin name, active flag and mix level for every filled slot.

    FL's "mute state" is 1 when the plugin is processing and 0 when it is bypassed (measured on 26.1.7).
    """
    out = []
    for slot in range(slots):
        name = call("op_plugins_get_plugin_name", index=index, slotIndex=slot, userName=False)
        if not name.ok or not name.value:
            continue
        mute = call("op_mixer_get_plugin_mute_state", index=index, slotIndex=slot)
        mix = call("op_mixer_get_plugin_mix_level", index=index, slotIndex=slot)
        out.append({"slot": slot, "plugin": name.value, "active": bool(mute.value) if mute.ok else None, "mix": mix.value if mix.ok else None})
    return ok({"track": index, "slots": out})

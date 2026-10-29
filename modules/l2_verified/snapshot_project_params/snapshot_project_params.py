from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def _v(r):
    return r.value if r.ok else None


def _params(index: int, slot: int, limit: int, glob: bool) -> dict:
    kw = {"index": index, "slotIndex": slot, "useGlobalIndex": glob}
    n = int(_v(call("op_plugins_get_param_count", **kw)) or 0)
    out = {}
    for p in range(min(n, limit)):
        name = _v(call("op_plugins_get_param_name", paramIndex=p, **kw))
        if name:
            raw = _v(call("op_plugins_get_param_value", paramIndex=p, **kw))
            out[str(p)] = {"name": name, "text": _v(call("op_plugins_get_param_value_string", paramIndex=p, **kw)),
                           "raw": round(raw, 5) if isinstance(raw, float) else raw}
    return {"count": n, "params": out}


def _insert(t: int, used: list, limit: int) -> dict:
    row = {"index": t, "name": _v(call("op_mixer_get_track_name", index=t)), "color": _v(call("op_mixer_get_track_color", index=t)),
           "volume": _v(call("op_mixer_get_track_volume", index=t)), "volume_db": _v(call("op_mixer_get_track_volume", index=t, mode=1)),
           "pan": _v(call("op_mixer_get_track_pan", index=t)), "stereo_sep": _v(call("op_mixer_get_track_stereo_sep", index=t)), "routes": {}, "slots": []}
    for d in sorted(set(used) | {0}):
        if d != t and _v(call("op_mixer_get_route_send_active", index=t, destIndex=d)):
            row["routes"][str(d)] = _v(call("op_mixer_get_route_to_level", index=t, destIndex=d))
    for slot in range(10):
        if _v(call("op_plugins_is_valid", index=t, slotIndex=slot)):
            s = {"slot": slot, "plugin": _v(call("op_plugins_get_plugin_name", index=t, slotIndex=slot)),
                 "user_name": _v(call("op_plugins_get_plugin_name", index=t, slotIndex=slot, userName=True)),
                 "mix": _v(call("op_mixer_get_plugin_mix_level", index=t, slotIndex=slot)), "on": _v(call("op_mixer_get_plugin_mute_state", index=t, slotIndex=slot))}
            s.update(_params(t, slot, limit, False))
            row["slots"].append(s)
    return row


def _channel(c: int, limit: int, with_params: bool) -> dict:
    kw = {"index": c, "useGlobalIndex": True}
    row = {"index": c, "name": _v(call("op_channels_get_channel_name", **kw)), "type": _v(call("op_channels_get_channel_type", **kw)),
           "volume_db": _v(call("op_channels_get_channel_volume", mode=True, **kw)), "pan": _v(call("op_channels_get_channel_pan", **kw)),
           "target": _v(call("op_channels_get_target_fx_track", **kw))}
    if with_params and _v(call("op_plugins_is_valid", index=c, slotIndex=-1, useGlobalIndex=True)):
        row["plugin"] = _v(call("op_plugins_get_plugin_name", index=c, slotIndex=-1, useGlobalIndex=True))
        row.update(_params(c, -1, limit, True))
    return row


def snapshot_project_params(inserts: list, max_params: int = 400, include_channels: bool = True, channel_params: bool = True) -> Result:
    """Read every effect slot on the given mixer inserts (plugin, name the person gave, slot mix, on state, every parameter's name, display text and
    raw value), each insert's level, pan, width and routes, and optionally every channel with its generator's parameters. Read only; slow (about
    80 ms a call, a 22-insert project takes about 16 minutes), so pass only the inserts you need.
    Errors: E_ARG for an empty insert list; E_NO_FL when FL does not answer."""
    if not inserts:
        return fail("E_ARG", "give at least one insert index")
    ping = call("op_mixer_track_count")
    if not ping.ok:
        return ping
    used = sorted({int(t) for t in inserts})
    data = {"tempo": _v(call("op_mixer_get_current_tempo")), "inserts": [_insert(t, used, max_params) for t in used], "channels": []}
    if include_channels:
        n = int(_v(call("op_channels_channel_count", globalCount=True)) or 0)
        data["channels"] = [_channel(c, max_params, channel_params) for c in range(n)]
    return ok(data)

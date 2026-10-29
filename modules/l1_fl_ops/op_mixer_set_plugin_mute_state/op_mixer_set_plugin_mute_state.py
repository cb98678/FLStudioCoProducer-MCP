import mixer


def op_mixer_set_plugin_mute_state(index: int, slotIndex: int, value: int) -> dict:
    """Run mixer.setPluginMuteState inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "slotIndex": slotIndex, "value": value}, {"index": "i", "slotIndex": "i", "value": "i"})
    if bad:
        return bad
    return _run(mixer.setPluginMuteState, index, slotIndex, value)

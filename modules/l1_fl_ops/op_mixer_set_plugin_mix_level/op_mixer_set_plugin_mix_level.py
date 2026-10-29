import mixer


def op_mixer_set_plugin_mix_level(index: int, slotIndex: int, value: float) -> dict:
    """Run mixer.setPluginMixLevel inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "slotIndex": slotIndex, "value": value}, {"index": "i", "slotIndex": "i", "value": "n"})
    if bad:
        return bad
    return _run(mixer.setPluginMixLevel, index, slotIndex, value)

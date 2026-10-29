import mixer


def op_mixer_get_plugin_mix_level(index: int, slotIndex: int) -> dict:
    """Run mixer.getPluginMixLevel inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "slotIndex": slotIndex}, {"index": "i", "slotIndex": "i"})
    if bad:
        return bad
    return _run(mixer.getPluginMixLevel, index, slotIndex)

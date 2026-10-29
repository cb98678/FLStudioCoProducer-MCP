import mixer


def op_mixer_get_active_effect_index() -> dict:
    """Run mixer.getActiveEffectIndex inside FL Studio and return the outcome as a result dict."""
    return _run(mixer.getActiveEffectIndex)

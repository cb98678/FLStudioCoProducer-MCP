import general


def op_general_get_use_metronome() -> dict:
    """Run general.getUseMetronome inside FL Studio and return the outcome as a result dict."""
    return _run(general.getUseMetronome)

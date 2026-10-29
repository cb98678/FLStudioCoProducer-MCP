import general


def op_general_clear_log() -> dict:
    """Run general.clearLog inside FL Studio and return the outcome as a result dict."""
    return _run(general.clearLog)

import general


def op_general_get_changed_flag() -> dict:
    """Run general.getChangedFlag inside FL Studio and return the outcome as a result dict."""
    return _run(general.getChangedFlag)

import general


def op_general_undo() -> dict:
    """Run general.undo inside FL Studio and return the outcome as a result dict."""
    return _run(general.undo)

import general


def op_general_get_precount() -> dict:
    """Run general.getPrecount inside FL Studio and return the outcome as a result dict."""
    return _run(general.getPrecount)

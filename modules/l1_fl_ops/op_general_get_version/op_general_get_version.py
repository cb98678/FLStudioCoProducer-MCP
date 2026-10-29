import general


def op_general_get_version() -> dict:
    """Run general.getVersion inside FL Studio and return the outcome as a result dict."""
    return _run(general.getVersion)

import general


def op_general_safe_to_edit() -> dict:
    """Run general.safeToEdit inside FL Studio and return the outcome as a result dict."""
    return _run(general.safeToEdit)

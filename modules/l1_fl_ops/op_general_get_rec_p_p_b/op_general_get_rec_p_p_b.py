import general


def op_general_get_rec_p_p_b() -> dict:
    """Run general.getRecPPB inside FL Studio and return the outcome as a result dict."""
    return _run(general.getRecPPB)

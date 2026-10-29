import transport


def op_transport_get_h_w_beat_l_e_d_state() -> dict:
    """Run transport.getHWBeatLEDState inside FL Studio and return the outcome as a result dict."""
    return _run(transport.getHWBeatLEDState)

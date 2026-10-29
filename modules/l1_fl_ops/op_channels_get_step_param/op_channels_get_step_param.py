import channels


def op_channels_get_step_param(step: int, param: int, offset: int, startPos: int, padsStride: int = 16, useGlobalIndex: bool = False) -> dict:
    """Run channels.getStepParam inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"step": step, "param": param, "offset": offset, "startPos": startPos, "padsStride": padsStride, "useGlobalIndex": useGlobalIndex}, {"step": "i", "param": "i", "offset": "i", "startPos": "i", "padsStride": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.getStepParam, step, param, offset, startPos, padsStride, useGlobalIndex)

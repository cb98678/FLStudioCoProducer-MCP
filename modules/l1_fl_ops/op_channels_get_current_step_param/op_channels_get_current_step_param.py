import channels


def op_channels_get_current_step_param(index: int, step: int, param: int, useGlobalIndex: bool = False) -> dict:
    """Run channels.getCurrentStepParam inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "step": step, "param": param, "useGlobalIndex": useGlobalIndex}, {"index": "i", "step": "i", "param": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.getCurrentStepParam, index, step, param, useGlobalIndex)

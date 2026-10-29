import channels


def op_channels_set_step_parameter_by_index(index: int, patNum: int, step: int, param: int, value: int, useGlobalIndex: bool = False) -> dict:
    """Run channels.setStepParameterByIndex inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "patNum": patNum, "step": step, "param": param, "value": value, "useGlobalIndex": useGlobalIndex}, {"index": "i", "patNum": "i", "step": "i", "param": "i", "value": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.setStepParameterByIndex, index, patNum, step, param, value, useGlobalIndex)

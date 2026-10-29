import device


def op_device_is_double_click(index: int) -> dict:
    """Run device.isDoubleClick inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(device.isDoubleClick, index)

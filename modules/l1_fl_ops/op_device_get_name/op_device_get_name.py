import device


def op_device_get_name() -> dict:
    """Run device.getName inside FL Studio and return the outcome as a result dict."""
    return _run(device.getName)

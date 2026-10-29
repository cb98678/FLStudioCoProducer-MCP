import device


def op_device_get_device_i_d() -> dict:
    """Run device.getDeviceID inside FL Studio and return the outcome as a result dict."""
    return _run(device.getDeviceID)

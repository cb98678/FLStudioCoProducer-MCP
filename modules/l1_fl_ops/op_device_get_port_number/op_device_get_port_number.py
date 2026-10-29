import device


def op_device_get_port_number() -> dict:
    """Run device.getPortNumber inside FL Studio and return the outcome as a result dict."""
    return _run(device.getPortNumber)

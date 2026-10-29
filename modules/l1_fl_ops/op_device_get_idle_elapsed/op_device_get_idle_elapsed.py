import device


def op_device_get_idle_elapsed() -> dict:
    """Run device.getIdleElapsed inside FL Studio and return the outcome as a result dict."""
    return _run(device.getIdleElapsed)

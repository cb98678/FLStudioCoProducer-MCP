import device


def op_device_get_master_sync() -> dict:
    """Run device.getMasterSync inside FL Studio and return the outcome as a result dict."""
    return _run(device.getMasterSync)

import ui


def op_ui_get_version(mode: int = 4) -> dict:
    """Run ui.getVersion inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"mode": mode}, {"mode": "i"})
    if bad:
        return bad
    return _run(ui.getVersion, mode)

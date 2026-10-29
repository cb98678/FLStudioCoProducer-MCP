import ui


def op_ui_set_hint_msg(msg: str) -> dict:
    """Run ui.setHintMsg inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"msg": msg}, {"msg": "s"})
    if bad:
        return bad
    return _run(ui.setHintMsg, msg)

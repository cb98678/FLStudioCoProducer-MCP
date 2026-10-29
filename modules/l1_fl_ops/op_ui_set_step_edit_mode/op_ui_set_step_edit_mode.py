import ui


def op_ui_set_step_edit_mode(newValue: bool) -> dict:
    """Run ui.setStepEditMode inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"newValue": newValue}, {"newValue": "b"})
    if bad:
        return bad
    return _run(ui.setStepEditMode, newValue)

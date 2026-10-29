import mixer


def op_mixer_focus_editor(index: int, plugIndex: int) -> dict:
    """Run mixer.focusEditor inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "plugIndex": plugIndex}, {"index": "i", "plugIndex": "i"})
    if bad:
        return bad
    return _run(mixer.focusEditor, index, plugIndex)

import ui


def op_ui_launch_audio_editor(reuse: int, filename: str, index: int, preset: str, presetGUID: str) -> dict:
    """Run ui.launchAudioEditor inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"reuse": reuse, "filename": filename, "index": index, "preset": preset, "presetGUID": presetGUID}, {"reuse": "i", "filename": "s", "index": "i", "preset": "s", "presetGUID": "s"})
    if bad:
        return bad
    return _run(ui.launchAudioEditor, reuse, filename, index, preset, presetGUID)

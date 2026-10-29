import ui


def op_ui_is_metronome_enabled() -> dict:
    """Run ui.isMetronomeEnabled inside FL Studio and return the outcome as a result dict."""
    return _run(ui.isMetronomeEnabled)

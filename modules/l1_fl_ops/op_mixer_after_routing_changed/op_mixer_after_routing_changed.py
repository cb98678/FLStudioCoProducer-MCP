import mixer


def op_mixer_after_routing_changed() -> dict:
    """Run mixer.afterRoutingChanged inside FL Studio and return the outcome as a result dict."""
    return _run(mixer.afterRoutingChanged)

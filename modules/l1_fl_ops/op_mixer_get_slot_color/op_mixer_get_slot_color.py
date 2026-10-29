import mixer


def op_mixer_get_slot_color(index: int, slot: int) -> dict:
    """Run mixer.getSlotColor inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "slot": slot}, {"index": "i", "slot": "i"})
    if bad:
        return bad
    return _run(mixer.getSlotColor, index, slot)

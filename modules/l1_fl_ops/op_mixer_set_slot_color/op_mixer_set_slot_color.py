import mixer


def op_mixer_set_slot_color(index: int, slot: int, color: int) -> dict:
    """Run mixer.setSlotColor inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "slot": slot, "color": color}, {"index": "i", "slot": "i", "color": "i"})
    if bad:
        return bad
    return _run(mixer.setSlotColor, index, slot, color)

from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def set_track_color_verified(index: int, rgb: list[int], like_index: int, like_rgb: list[int]) -> Result:
    """Colour a mixer track and confirm by reading it back. The colour integer's byte order (BGR or RGB) is taken from the track `like_index`, whose colour in
    FL is known to be `like_rgb`, so no order is assumed. Errors: E_NOT_VERIFIED when the readback differs or the reference matches neither order."""
    ref = call("op_mixer_get_track_color", index=like_index)
    if not ref.ok:
        return ref
    seen = ref.value & 0xFFFFFF  # FL reports a signed 32-bit integer with an alpha byte on top
    r, g, b = like_rgb
    order = "bgr" if seen == (b << 16) | (g << 8) | r else "rgb" if seen == (r << 16) | (g << 8) | b else ""
    if not order:
        return fail("E_NOT_VERIFIED", "track %d reads colour %#08x, which is neither order of %r" % (like_index, seen, like_rgb))
    r, g, b = rgb
    want = (b << 16) | (g << 8) | r if order == "bgr" else (r << 16) | (g << 8) | b
    w = call("op_mixer_set_track_color", index=index, color=want)
    if not w.ok:
        return w
    got = call("op_mixer_get_track_color", index=index)
    if not got.ok:
        return got
    if got.value & 0xFFFFFF != want:
        return fail("E_NOT_VERIFIED", "wrote %#08x but read back %#08x" % (want, got.value & 0xFFFFFF), wrote=want, read=got.value)
    return ok({"index": index, "color": want, "order": order}, verified=True)

from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service

# CENTER, VARIATION, TRANS as fractions of each knob's travel (VARIATION 0.5 and TRANS 1 are the voice as sung). Measured on the Girlish
# vocal, 2026-10-29: robotic 1.3 cents off the semitone with 61 % of frames within 10 cents of their note, middle 8.7 and 45 %, smooth
# 11.3 and 36 %, the untuned voice 18.7 and 31 %.
STYLES = {"robotic": (1.0, 0.0, 0.0), "middle": (1.0, 0.23, 0.33), "smooth": (0.83, 0.44, 0.88), "natural": (0.6, 0.5, 1.0)}


def apply_vocal_tuning_gui(path: str, out_path: str, style: str = "middle", midi_path: str = "", center: float = -1.0,
                            variation: float = -1.0, trans: float = -1.0) -> Result:
    """Auto-tune a vocal with FL's Newtone and save the tuned audio and its notes as MIDI (the voice's melody for the synths and bass).

    style picks the three knobs (robotic, middle, smooth, natural); center, variation or trans (0..1) override one. midi_path defaults to
    out_path with .mid. Runs the newtone_tune_save_gui recipe. Errors: E_ARG, E_SANDBOX_VIOLATION, E_GUI_MISMATCH, E_NOT_VERIFIED, E_HALTED.
    """
    if style not in STYLES:
        return fail("E_ARG", "style must be one of %s" % ", ".join(STYLES))
    knobs = [v if 0.0 <= v <= 1.0 else d for v, d in zip((center, variation, trans), STYLES[style])]
    root = str(get_service("sandbox_root"))
    mid = midi_path or (out_path.rsplit(".", 1)[0] + ".mid")
    checks = [call("check_sandbox_path", path=p, sandbox_root=root) for p in (path, out_path, mid)]
    bad = next((c for c in checks if not c.ok), None)
    if bad is not None:
        return bad
    src, wav, midi = (c.value["resolved"] for c in checks)
    run = call("run_gui_recipe", name="newtone_tune_save_gui", params={"path": src, "out_wav": wav, "out_mid": midi, "center": "%.3f" % knobs[0],
                                                                       "variation": "%.3f" % knobs[1], "trans": "%.3f" % knobs[2]})
    if not run.ok:
        return run
    return ok({"out_path": wav, "midi_path": midi, "style": style, "center": knobs[0], "variation": knobs[1], "trans": knobs[2]})

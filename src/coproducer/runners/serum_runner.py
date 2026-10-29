"""Serum 2 played headless through pedalboard (Spotify, GPL-3.0; https://github.com/spotify/pedalboard), to hear a generated preset
without FL: load a channel state, play notes, write the audio, and write back the state Serum itself saves after loading it.

Measured on rtxclub 2026-10-26 (pedalboard 0.9.26, Serum 2.1.5): the .vst3 bundle folder does not scan; the binary inside it does,
with plugin_name "Serum 2" (the file also holds "Serum 2 FX"). A state rebuilt from the serum-mcp preset "CP - Deep Sub" rendered
the same audio as the state Serum wrote for it in FL (difference -73 dB, correlation 1.00000), and Serum re-saved it in its own
format version (11.0), which is what goes into the project.
"""
from __future__ import annotations

import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner_common import RunnerError, serve  # noqa: E402

DEFAULT_VST = r"C:\Program Files\Common Files\VST3\Serum2.vst3\Contents\x86_64-win\Serum2.vst3"
STATE: dict = {"plugin": None, "path": None}


def _serumstate():
    """serumstate.py from the coproducer source (standard library plus cbor2 and zstandard, both in this environment)."""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "serumstate.py")
    spec = importlib.util.spec_from_file_location("serumstate", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _plugin(path: str | None = None):
    import pedalboard
    path = path or os.environ.get("SERUM2_VST3") or DEFAULT_VST
    if STATE["plugin"] is None or STATE["path"] != path:
        if not os.path.exists(path):
            raise RunnerError("E_NOT_FOUND", "no Serum 2 plugin at %s (set SERUM2_VST3)" % path)
        STATE["plugin"], STATE["path"] = pedalboard.load_plugin(path, plugin_name="Serum 2"), path
    return STATE["plugin"]


def load(a: dict) -> dict:
    p = _plugin(a.get("vst3"))
    return {"loaded": p.name, "instrument": bool(p.is_instrument)}


def render(a: dict) -> dict:
    """state_in: a Serum 2 channel state (FL plugin event data); notes: [[start_s, length_s, midi, velocity 1-127]]; seconds; out_wav;
    state_out: where Serum's own re-saved channel state goes. Returns levels of the render."""
    import numpy as np
    import soundfile as sf
    ss = _serumstate()
    blob = open(a["state_in"], "rb").read()
    proc, ctrl = ss.components(blob)
    p = _plugin(a.get("vst3"))
    p.raw_state = ss.juce_state(proc, ctrl)
    p.reset()
    msgs = []
    for t0, length, midi, vel in a["notes"]:
        msgs += [(bytes([0x90, int(midi), max(1, min(127, int(vel)))]), float(t0)), (bytes([0x80, int(midi), 0]), float(t0) + float(length))]
    rate = int(a.get("rate", 44100))
    audio = p(sorted(msgs, key=lambda m: m[1]), duration=float(a["seconds"]), sample_rate=rate, num_channels=2)
    os.makedirs(os.path.dirname(os.path.abspath(a["out_wav"])), exist_ok=True)
    sf.write(a["out_wav"], audio.T, rate, subtype="FLOAT")
    back_proc, back_ctrl = ss.parse_juce_state(bytes(p.raw_state))
    with open(a["state_out"], "wb") as fh:
        fh.write(ss.from_components(blob, back_proc, back_ctrl))
    rms = float(np.sqrt(np.mean(audio ** 2)))
    return {"out_wav": a["out_wav"], "state_out": a["state_out"], "rms_db": round(20 * np.log10(rms + 1e-12), 2),
            "peak": round(float(np.abs(audio).max()), 4), "preset": ss.preset_name(blob), "seconds": float(a["seconds"])}


if __name__ == "__main__":
    serve({"load": load, "unload": lambda a: STATE.update(plugin=None, path=None) or True, "ping": lambda a: "pong", "render": render})

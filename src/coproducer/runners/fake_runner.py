"""A stand-in model runner for tests of the worker, the scheduler and the L5 adapters. No ML libraries."""
from __future__ import annotations

import math
import os
import struct
import sys
import time
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner_common import RunnerError, serve  # noqa: E402

STATE: dict = {"loaded": None}


def _tone(path: str, hz: float, seconds: float = 0.2, rate: int = 22050) -> None:
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"".join(struct.pack("<h", int(8000 * math.sin(2 * math.pi * hz * i / rate))) for i in range(int(rate * seconds))))


def load(a: dict) -> dict:
    STATE["loaded"] = a.get("variant")
    return {"loaded": STATE["loaded"], "pid": os.getpid()}


def unload(a: dict) -> bool:
    STATE["loaded"] = None
    return True


def separate(a: dict) -> dict:
    os.makedirs(a["out_dir"], exist_ok=True)
    stems = {}
    for i, name in enumerate(("drums", "bass", "other", "vocals")):
        stems[name] = os.path.join(a["out_dir"], name + ".wav")
        _tone(stems[name], 110 * (i + 1))
    return {"stems": stems, "model": a.get("model", "fake")}


def transcribe(a: dict) -> dict:
    return {"notes": [{"start": 0.0, "end": 0.5, "pitch": 60, "velocity": 0.8}, {"start": 0.5, "end": 1.0, "pitch": 64, "velocity": 0.6}]}


def generate(a: dict) -> dict:
    os.makedirs(a["out_dir"], exist_ok=True)
    path = os.path.join(a["out_dir"], "gen_%s.wav" % a.get("seed", 0))
    _tone(path, 220, seconds=float(a.get("duration", 1.0)))
    return {"paths": [path], "seed": a.get("seed", 0)}


def critique(a: dict) -> dict:
    if os.environ.get("FAKE_CRITIQUE_REPLY"):
        return {"text": os.environ["FAKE_CRITIQUE_REPLY"]}
    if "bpm" in a.get("prompt", "").lower():
        return {"text": "key=A minor; bpm=128"}
    return {"text": "Fake critique of %s: the low end is heavy." % os.path.basename(a["path"])}


def ground(a: dict) -> dict:
    if os.environ.get("FAKE_GROUND_FAIL"):
        raise RunnerError("E_MODEL", "no GUI grounding model is configured")
    return {"x": 10, "y": 20, "confidence": float(os.environ.get("FAKE_GROUND_CONF", "0.9"))}


def vocals(a: dict) -> dict:
    os.makedirs(a["out_dir"], exist_ok=True)
    out = {}
    for i, name in enumerate(("vocals", "instrumental")):
        out[name] = os.path.join(a["out_dir"], "mix_%s.wav" % name)
        _tone(out[name], 220 * (i + 1), seconds=2.0)  # long enough for a loudness reading (the panel's separation judge)
    return out


def embed(a: dict) -> dict:
    """A unit vector per segment that depends on the file name and the segment start, so similarities differ but are repeatable."""
    out = []
    for seg in a.get("segments") or [[0, 10]]:
        h = abs(hash((os.path.basename(a["path"]), round(seg[0], 2)))) % 1000
        v = [math.sin(h + k) for k in range(8)]
        n = math.sqrt(sum(x * x for x in v))
        out.append([x / n for x in v])
    return {"embeddings": out}


def words(a: dict) -> dict:
    w = [("friends", 2.0, 2.4), ("in", 2.4, 2.5), ("low", 2.5, 2.8), ("places", 2.8, 3.3), ("friends", 6.0, 6.4), ("in", 6.4, 6.5), ("low", 6.5, 6.8), ("places", 6.8, 7.3)]
    return {"text": " ".join(x[0] for x in w), "words": [{"word": x, "start": a0, "end": a1} for x, a0, a1 in w], "model": "fake"}


def beats(a: dict) -> dict:
    """A steady 120 bpm 4/4 grid over 20 s (FAKE_BEATS_FEW gives two beats); the checkpoint argument is echoed for the tests."""
    if os.environ.get("FAKE_BEATS_FEW"):
        return {"beats": [0.5, 1.0], "downbeats": [0.5]}
    b = [round(0.25 + 0.5 * i, 4) for i in range(40)]
    return {"beats": b, "downbeats": b[::4], "checkpoint": a.get("checkpoint", "")}


def melody(a: dict) -> dict:
    """A sung A3, C#4, E4 arpeggio (0.3 s each) at 10 ms frames, with a short gap between notes."""
    f0, per, rms = [], [], []
    for hz in (220.0, 277.18, 329.63):
        f0 += [hz] * 30 + [0.0] * 5
        per += [0.9] * 30 + [0.1] * 5
        rms += [0.1] * 30 + [0.0001] * 5
    return {"hop_s": 0.01, "offset_s": float(a.get("offset_s", 0.0)), "f0": f0, "periodicity": per, "rms": rms}


def render(a: dict) -> dict:
    """Serum stand-in: a tone for the notes' length, and the state passed back unchanged."""
    os.makedirs(os.path.dirname(os.path.abspath(a["out_wav"])), exist_ok=True)
    rate = 22050
    out = [0.0] * int(rate * float(a["seconds"]))
    for t0, length, midi, _vel in a["notes"]:          # a plucked tone per note, decaying a little slower each render
        hz = 440.0 * 2 ** ((midi - 69) / 12)
        for i in range(int(rate * min(length + 0.3, 1.0))):
            j = int(t0 * rate) + i
            if j < len(out):
                out[j] += 0.5 * math.sin(2 * math.pi * hz * i / rate) * math.exp(-i / rate / 0.3)
    with wave.open(a["out_wav"], "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"".join(struct.pack("<h", int(16000 * max(-1.0, min(1.0, v)))) for v in out))
    with open(a["state_in"], "rb") as src, open(a["state_out"], "wb") as dst:
        dst.write(src.read())
    return {"out_wav": a["out_wav"], "state_out": a["state_out"], "rms_db": -15.0, "peak": 0.24, "preset": None, "seconds": float(a["seconds"])}


def preset(a: dict) -> dict:
    """serum-mcp stand-in: the test preset "CP - House Stab" written under the given name, at serum-mcp's path for it."""
    import importlib.util
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location("serumstate", os.path.join(os.path.dirname(here), "serumstate.py"))
    ss = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ss)
    if not a["spec"].get("oscillators"):
        raise RunnerError("E_ARG", "the preset spec does not validate: oscillators missing")
    src = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(here))), "tests", "data", "cp_house_stab.SerumPreset")
    meta, data = ss.read_container(open(src, "rb").read())
    meta = dict(meta, presetName=a["spec"]["name"])
    folder = os.path.join(a["presets_dir"], *[p for p in (a.get("subfolder") or "").split("/") if p])
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, a["spec"]["name"].replace(" ", "-") + ".SerumPreset")
    with open(path, "wb") as fh:
        fh.write(ss.write_container(meta, data))
    STATE["specs"] = STATE.get("specs", []) + [a["spec"]]
    return {"path": path, "depends_on": []}


def sleep(a: dict) -> bool:
    time.sleep(float(a["seconds"]))
    return True


def crash(a: dict) -> bool:
    os._exit(3)


def oom(a: dict) -> bool:
    raise RuntimeError("CUDA out of memory. Tried to allocate 2.00 GiB")


def bad(a: dict) -> bool:
    raise RunnerError("E_ARG", "bad input", field="x")


if __name__ == "__main__":
    serve({"load": load, "unload": unload, "ping": lambda a: "pong", "separate": separate, "transcribe": transcribe, "beats": beats, "melody": melody, "vocals": vocals, "words": words, "embed": embed,
           "generate": generate, "critique": critique, "sleep": sleep, "crash": crash, "oom": oom, "bad": bad,
           "cover": generate, "repaint": generate, "ground": ground, "render": render, "preset": preset})

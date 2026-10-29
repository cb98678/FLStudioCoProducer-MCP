"""Stand-alone smoke test for the FL-side script. Run it with the oldest Python FL may embed (3.9).

Usage: python3.9 tools/smoke_fl39.py     (no third-party packages needed)
Loads fakefl.py and fl_side/device_coproducer.py by path, plays one ping and one op through the real
frame protocol using the script's own helper functions, and prints OK.
"""
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def roundtrip(script, fake, msg_type, req_id, name, data):
    body = script.encode_body(name, data).value
    packed = script.encode_sysex(body).value
    chunks = script.split_frames(packed, 40).value
    for i, c in enumerate(chunks):
        frame = script.build_frame(1, msg_type, req_id, i, len(chunks), c).value
        script.OnSysEx(type("E", (), {"sysex": bytes(frame), "handled": False})())
    script.OnIdle()
    frames = [script.parse_frame(list(f)).value for f in fake.outbox]
    fake.outbox.clear()
    payload = [b for f in sorted(frames, key=lambda f: f["seq"]) for b in f["payload"]]
    return script.decode_body(script.decode_sysex(payload).value).value


def main():
    fakefl = load("fakefl_standalone", REPO / "src" / "coproducer" / "fakefl.py")
    fake = fakefl.FakeFL()
    fake.install()
    script = load("device_script", REPO / "fl_side" / "device_coproducer.py")
    pong = roundtrip(script, fake, 4, 7, "ping", {})
    assert pong["data"]["proto"] == 1, pong
    rep = roundtrip(script, fake, 1, 8, "op_mixer_get_track_name", {"index": 1})
    assert rep["data"] == {"ok": True, "value": "Insert 1", "error": None}, rep
    rep = roundtrip(script, fake, 1, 9, "bridge_echo", {"text": "café " * 40})
    assert rep["data"]["value"] == "café " * 40
    print("OK", sys.version.split()[0])


main()

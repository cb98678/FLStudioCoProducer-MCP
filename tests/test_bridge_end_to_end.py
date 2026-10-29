"""Host bridge client against the generated FL-side script and the fake FL, over the real frame protocol."""
import ast
from pathlib import Path

from coproducer.result import Result

SCRIPT = Path(__file__).resolve().parents[1] / "fl_side" / "device_coproducer.py"


def test_generated_script_is_python39_syntax():
    ast.parse(SCRIPT.read_text(encoding="utf-8"), feature_version=(3, 9))


def test_ping_reports_versions(rig):
    r = rig.client.ping()
    assert r.ok and r.value["proto"] == 1 and r.value["fl"] == "2026.1.7" and r.value["project"] == "fake_project"


def test_read_op_roundtrip(rig):
    r = rig.reg.call("op_mixer_get_track_name", index=1)
    assert r.ok and r.value == "Insert 1"


def test_write_op_roundtrip_changes_fake(rig):
    r = rig.reg.call("op_mixer_set_track_volume", index=2, volume=0.5)
    assert r.ok and abs(rig.fake.mixer[2]["volume"] - 0.5) < 1e-9


def test_float_precision_survives(rig):
    rig.reg.call("op_mixer_set_track_volume", index=2, volume=0.123456789)
    assert rig.reg.call("op_mixer_get_track_volume", index=2).value == 0.123456789


def test_unknown_op_reports_error(rig):
    r = rig.client.request("op_nope", {})
    assert not r.ok and r.error.code == "E_NOT_FOUND"


def test_fl_error_is_surfaced(rig):
    r = rig.reg.call("op_mixer_get_track_name", index=99)
    assert not r.ok and r.error.code == "E_ARG"


def test_big_payload_is_split_and_reassembled(rig):
    text = "x" * 3000
    r = rig.client.request("bridge_echo", {"text": text})
    assert r.ok and r.value == text
    assert len(rig.fake.outbox) == 0 and len(rig.transport.sent) > 10


def test_unicode_survives(rig):
    r = rig.client.request("bridge_echo", {"text": "kick é \U0001f941"})
    assert r.ok and r.value == "kick é \U0001f941"


def test_foreign_sysex_is_ignored(rig):
    rig.transport.send(bytes([0xF0, 0x41, 0x10, 0xF7]))
    assert rig.client.ping().ok
    assert rig.script._stats["ignored"] == 1


def test_read_retries_after_dropped_reply(rig):
    rig.transport.drop_replies = 1
    r = rig.client.request("op_mixer_track_count", {}, timeout_s=0.2)
    assert r.ok and r.value == 6


def test_write_is_not_retried_after_timeout(rig):
    rig.transport.drop_replies = 1
    r = rig.client.request("op_mixer_set_track_volume", {"index": 1, "volume": 0.3}, writes=True, timeout_s=0.2)
    assert not r.ok and r.error.code == "E_TIMEOUT"
    assert len(rig.fake.calls("mixer", "setTrackVolume")) == 1


def test_corrupt_reply_is_not_accepted(rig):
    rig.transport.corrupt_next = True
    r = rig.client.request("op_mixer_track_count", {}, timeout_s=0.2)
    assert r.ok  # the read is retried and the second reply is clean


def test_l1_needs_a_bridge():
    from coproducer.registry import Registry
    reg = Registry(Path(__file__).resolve().parents[1] / "modules").load(layers=("L1",))
    r = reg.call("op_mixer_track_count")
    assert not r.ok and r.error.code == "E_UNSUPPORTED_API"


def test_result_type(rig):
    assert isinstance(rig.client.ping(), Result)


def test_script_works_without_json_module(rig):
    import json as real_json
    import sys

    from coproducer.bridge import BridgeClient
    from coproducer.fakefl import FakeFL
    from coproducer.loopback import LoopbackTransport, load_device_script

    fake = FakeFL()
    sys.modules["json"] = None  # make `import json` fail while the FL-side file loads
    try:
        script = load_device_script(fake, tag="nojson")
    finally:
        sys.modules["json"] = real_json
    assert script.json.__name__ == "json" and script.json is not real_json
    client = BridgeClient(rig.reg, LoopbackTransport(fake, script))
    assert client.request("op_mixer_get_track_name", {"index": 2}).value == "Insert 2"
    assert client.request("bridge_echo", {"text": "héllo \"q\""}).value == "héllo \"q\""

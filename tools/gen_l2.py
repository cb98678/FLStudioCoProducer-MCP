"""Generate the L2 "verified setter" family: write through one L1 op, read it back, report meta.verified.

One job: turn the FAMILY table into module folders. Hand-written L2 modules live in bundles and are not touched.
Run: python tools/gen_l2.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from modtools import schema, write_module  # noqa: E402

IDX = {"type": "integer", "minimum": 0}
UNIT = {"type": "number", "minimum": 0.0, "maximum": 1.0}
SIGNED = {"type": "number", "minimum": -1.0, "maximum": 1.0}

# name, summary, params(py), props(json schema), kind, write(op, args), read(op, args), value param,
#   golden sample kwargs, expected value, state probe on fake, bad-FL-arg kwargs
FAMILY = [
    dict(name="set_track_volume_verified", summary="Set a mixer track's volume from 0.0 to 1.0 (FL default 0.8) and confirm by reading it back.",
         sig="index: int, volume: float", props={"index": IDX, "volume": UNIT}, kind="float", v="volume",
         write=("op_mixer_set_track_volume", "index=index, volume=volume"), read=("op_mixer_get_track_volume", "index=index"),
         sample="index=1, volume=0.5", want="0.5", state="rig.fake.mixer[1]['volume']", badfl="index=99, volume=0.5"),
    dict(name="set_track_pan_verified", summary="Set a mixer track's pan from -1.0 (left) to 1.0 (right) and confirm by reading it back.",
         sig="index: int, pan: float", props={"index": IDX, "pan": SIGNED}, kind="float", v="pan",
         write=("op_mixer_set_track_pan", "index=index, pan=pan"), read=("op_mixer_get_track_pan", "index=index"),
         sample="index=1, pan=-0.25", want="-0.25", state="rig.fake.mixer[1]['pan']", badfl="index=99, pan=0.1"),
    dict(name="set_track_stereo_sep_verified", summary="Set a mixer track's stereo separation from -1.0 to 1.0 and confirm by reading it back.",
         sig="index: int, separation: float", props={"index": IDX, "separation": SIGNED}, kind="float", v="separation",
         write=("op_mixer_set_track_stereo_sep", "index=index, pan=separation"), read=("op_mixer_get_track_stereo_sep", "index=index"),
         sample="index=1, separation=0.5", want="0.5", state="rig.fake.mixer[1]['stereo']", badfl="index=99, separation=0.1"),
    dict(name="set_track_name_verified", summary="Rename a mixer track and confirm by reading the name back.",
         sig="index: int, name: str", props={"index": IDX, "name": {"type": "string", "minLength": 1, "maxLength": 64}}, kind="eq", v="name",
         write=("op_mixer_set_track_name", "index=index, name=name"), read=("op_mixer_get_track_name", "index=index"),
         sample="index=1, name='Kick'", want="'Kick'", state="rig.fake.mixer[1]['name']", badfl="index=99, name='x'"),
    dict(name="mute_track_verified", summary="Set a mixer track's mute state to an explicit value and confirm it.",
         sig="index: int, muted: bool", props={"index": IDX, "muted": {"type": "boolean"}}, kind="eq", v="muted",
         write=("op_mixer_mute_track", "index=index, value=1 if muted else 0"), read=("op_mixer_is_track_muted", "index=index"),
         sample="index=1, muted=True", want="True", state="rig.fake.mixer[1]['mute']", badfl="index=99, muted=True"),
    dict(name="solo_track_verified", summary="Set a mixer track's solo state to an explicit value and confirm it.",
         sig="index: int, solo: bool", props={"index": IDX, "solo": {"type": "boolean"}}, kind="eq", v="solo",
         write=("op_mixer_solo_track", "index=index, value=1 if solo else 0"), read=("op_mixer_is_track_solo", "index=index"),
         sample="index=1, solo=True", want="True", state="rig.fake.mixer[1]['solo']", badfl="index=99, solo=True"),
    dict(name="set_route_level_verified", summary="Set the send level from one mixer track to another (0.0 to 1.0) and confirm it.",
         sig="index: int, dest_index: int, level: float", props={"index": IDX, "dest_index": IDX, "level": UNIT}, kind="float", v="level",
         write=("op_mixer_set_route_to_level", "index=index, destIndex=dest_index, level=level"),
         read=("op_mixer_get_route_to_level", "index=index, destIndex=dest_index"),
         sample="index=1, dest_index=0, level=0.4", want="0.4", state="rig.fake.mixer[1]['routes'][0]", badfl="index=1, dest_index=5, level=0.4"),
    dict(name="set_eq_gain_verified", summary="Set one mixer EQ band's gain (0.0 to 1.0, 0.5 is flat) and confirm it.",
         sig="index: int, band: int, value: float", props={"index": IDX, "band": {"type": "integer", "minimum": 0, "maximum": 2}, "value": UNIT},
         kind="float", v="value", write=("op_mixer_set_eq_gain", "index=index, band=band, value=value"),
         read=("op_mixer_get_eq_gain", "index=index, band=band"),
         sample="index=1, band=0, value=0.7", want="0.7", state="rig.fake.mixer[1]['eq'][0]['gain']", badfl="index=99, band=0, value=0.7"),
    dict(name="set_eq_frequency_verified", summary="Set one mixer EQ band's frequency (0.0 to 1.0, normalized) and confirm it.",
         sig="index: int, band: int, value: float", props={"index": IDX, "band": {"type": "integer", "minimum": 0, "maximum": 2}, "value": UNIT},
         kind="float", v="value", write=("op_mixer_set_eq_frequency", "index=index, band=band, value=value"),
         read=("op_mixer_get_eq_frequency", "index=index, band=band"),
         sample="index=1, band=1, value=0.3", want="0.3", state="rig.fake.mixer[1]['eq'][1]['freq']", badfl="index=99, band=0, value=0.7"),
    dict(name="set_eq_bandwidth_verified", summary="Set one mixer EQ band's bandwidth (0.0 to 1.0, normalized) and confirm it.",
         sig="index: int, band: int, value: float", props={"index": IDX, "band": {"type": "integer", "minimum": 0, "maximum": 2}, "value": UNIT},
         kind="float", v="value", write=("op_mixer_set_eq_bandwidth", "index=index, band=band, value=value"),
         read=("op_mixer_get_eq_bandwidth", "index=index, band=band"),
         sample="index=1, band=2, value=0.65", want="0.65", state="rig.fake.mixer[1]['eq'][2]['bw']", badfl="index=99, band=0, value=0.7"),
    dict(name="set_channel_volume_verified", summary="Set a channel's volume from 0.0 to 1.0 and confirm by reading it back.",
         sig="index: int, volume: float", props={"index": IDX, "volume": UNIT}, kind="float", v="volume",
         write=("op_channels_set_channel_volume", "index=index, volume=volume"), read=("op_channels_get_channel_volume", "index=index"),
         sample="index=1, volume=0.6", want="0.6", state="rig.fake.channels[1]['volume']", badfl="index=99, volume=0.6"),
    dict(name="set_channel_pan_verified", summary="Set a channel's pan from -1.0 to 1.0 and confirm by reading it back.",
         sig="index: int, pan: float", props={"index": IDX, "pan": SIGNED}, kind="float", v="pan",
         write=("op_channels_set_channel_pan", "index=index, pan=pan"), read=("op_channels_get_channel_pan", "index=index"),
         sample="index=1, pan=0.3", want="0.3", state="rig.fake.channels[1]['pan']", badfl="index=99, pan=0.3"),
    dict(name="mute_channel_verified", summary="Set a channel's mute state to an explicit value and confirm it.",
         sig="index: int, muted: bool", props={"index": IDX, "muted": {"type": "boolean"}}, kind="eq", v="muted",
         write=("op_channels_mute_channel", "index=index, value=1 if muted else 0"), read=("op_channels_is_channel_muted", "index=index"),
         sample="index=1, muted=True", want="True", state="rig.fake.channels[1]['mute']", badfl="index=99, muted=True"),
    dict(name="route_channel_to_track_verified", summary="Route a channel to a mixer track and confirm by reading the target back.",
         sig="channel_index: int, track_index: int", props={"channel_index": IDX, "track_index": IDX}, kind="eq", v="track_index",
         write=("op_channels_set_target_fx_track", "channelIndex=channel_index, mixerIndex=track_index"),
         read=("op_channels_get_target_fx_track", "index=channel_index"),
         sample="channel_index=1, track_index=3", want="3", state="rig.fake.channels[1]['target']", badfl="channel_index=1, track_index=99"),
    dict(name="mute_playlist_track_verified", summary="Set a playlist track's mute state to an explicit value and confirm it.",
         sig="index: int, muted: bool", props={"index": {"type": "integer", "minimum": 1}, "muted": {"type": "boolean"}}, kind="eq", v="muted",
         write=("op_playlist_mute_track", "index=index, value=1 if muted else 0"), read=("op_playlist_is_track_muted", "index=index"),
         sample="index=2, muted=True", want="True", state="rig.fake.playlist[1]['mute']", badfl="index=99, muted=True"),
    dict(name="set_playlist_track_name_verified", summary="Rename a playlist track and confirm by reading the name back.",
         sig="index: int, name: str", props={"index": {"type": "integer", "minimum": 1}, "name": {"type": "string", "minLength": 1, "maxLength": 64}},
         kind="eq", v="name", write=("op_playlist_set_track_name", "index=index, name=name"), read=("op_playlist_get_track_name", "index=index"),
         sample="index=2, name='Drums'", want="'Drums'", state="rig.fake.playlist[1]['name']", badfl="index=99, name='x'"),
    dict(name="select_pattern_verified", summary="Make a pattern current and confirm by reading the current pattern number.",
         sig="index: int", props={"index": {"type": "integer", "minimum": 1}}, kind="eq", v="index",
         write=("op_patterns_jump_to_pattern", "index=index"), read=("op_patterns_pattern_number", ""),
         sample="index=3", want="3", state="rig.fake.pattern_current", badfl="index=99"),
]

SRC = '''from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def {name}({sig}) -> Result:
    """{summary}

    Errors: E_ARG for bad input or an FL-side failure, E_NOT_VERIFIED when the readback differs.
    """
    w = call("{wop}", {wargs})
    if not w.ok:
        return w
    r = call("{rop}"{rargs})
    if not r.ok:
        return r
    if {mismatch}:
        return fail("E_NOT_VERIFIED", "wrote %r but read back %r" % ({v}, r.value), wrote={v}, read=r.value)
    return ok(r.value, verified=True)
'''

TEST = '''"""Tests for {name}: golden against the fake FL, and failure handling."""


def test_{golden}(rig):
    r = rig.call("{name}", {sample})
    assert r.ok and r.meta["verified"] is True
    assert {check}
    assert rig.fake.calls("{wmod}", "{wfn}")


def test_failures(rig):
    assert rig.call("{name}", {badfl}).error.code == "E_ARG"
    rig.fake.ignore_writes = True
    r = rig.call("{name}", {sample})
    assert not r.ok and r.error.code == "E_NOT_VERIFIED"
'''


def snake_to_fl(op: str) -> tuple[str, str]:
    """op_mixer_set_track_volume -> ('mixer', 'setTrackVolume') using the inventory for the right-cased name."""
    import json
    inv = json.loads((Path(__file__).resolve().parent.parent / "src/coproducer/data/api_inventory.json").read_text())
    mod = op.split("_")[1]
    tail = op[len(f"op_{mod}_"):]
    for key in inv:
        m, fn = key.split(".")
        if m == mod and "".join(c if not c.isupper() else "_" + c.lower() for c in fn) == tail:
            return m, fn
    raise SystemExit(f"cannot map {op}")


def main() -> int:
    n = 0
    for f in FAMILY:
        wop, wargs = f["write"]
        rop, rargs = f["read"]
        v = f["v"]
        mismatch = f"abs(r.value - {v}) > 0.002" if f["kind"] == "float" else f"r.value != {v}"
        src = SRC.format(name=f["name"], sig=f["sig"], summary=f["summary"], wop=wop, wargs=wargs, rop=rop,
                         rargs=(", " + f["read"][1]) if rargs else "", mismatch=mismatch, v=v)
        wmod, wfn = snake_to_fl(wop)
        want = f["want"]
        check = f"abs({f['state']} - {want}) < 1e-9" if f["kind"] == "float" else f"{f['state']} == {want}"
        test = TEST.format(name=f["name"], golden="reads_back_and_changes_fake", sample=f["sample"], badfl=f["badfl"],
                           check=check, wmod=wmod, wfn=wfn)
        test = test.replace("def test_reads_back_and_changes_fake", "def test_reads_back_and_changes_fake")
        required = [k for k in f["props"]]
        meta = dict(layer="L2", summary=f["summary"], side="writes_fl_sandbox", auto="A2", cost="instant", idem="true",
                    verifier="readback", golden="test_reads_back_and_changes_fake", failure="test_failures",
                    calls=f"{wop}, {rop}", input=schema(f["props"], required),
                    output='{"type":["number","string","boolean","integer"]}', min_api=1)
        write_module("l2_verified", f["name"], src, test, meta)
        n += 1
    print(f"generated {n} L2 verified setters")
    return 0


if __name__ == "__main__":
    sys.exit(main())

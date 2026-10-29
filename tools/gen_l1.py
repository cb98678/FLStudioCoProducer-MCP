"""Generate the L1 FL op modules (source, manifest, test) from the API inventory.

One job: turn the CURATED table into module folders under modules/l1_fl_ops and write docs/l1_missing.md.
Run: python tools/gen_l1.py   (run tools/gen_inventory.py first)
"""
from __future__ import annotations

import ast
import json
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INV = REPO / "src" / "coproducer" / "data" / "api_inventory.json"
OUT = REPO / "modules" / "l1_fl_ops"

# (module, function, kind r|w, sample args, optional setup run on the fake before the golden call)
M = "arrangement"
CURATED: list[tuple] = [
    ("transport", "start", "w", ()), ("transport", "stop", "w", ()), ("transport", "record", "w", ()),
    ("transport", "isPlaying", "r", ()), ("transport", "isRecording", "r", ()),
    ("transport", "getLoopMode", "r", ()), ("transport", "setLoopMode", "w", ()),
    ("transport", "getSongPos", "r", ()), ("transport", "setSongPos", "w", (0,)),
    ("transport", "getSongLength", "r", (0,)),
    ("mixer", "trackCount", "r", ()), ("mixer", "getTrackName", "r", (1,)),
    ("mixer", "setTrackName", "w", (1, "Kick")), ("mixer", "getTrackVolume", "r", (1,)),
    ("mixer", "setTrackVolume", "w", (1, 0.5)), ("mixer", "getTrackPan", "r", (1,)),
    ("mixer", "setTrackPan", "w", (1, 0.25)), ("mixer", "getTrackStereoSep", "r", (1,)),
    ("mixer", "setTrackStereoSep", "w", (1, 0.1)), ("mixer", "isTrackMuted", "r", (1,)),
    ("mixer", "muteTrack", "w", (1, 1)), ("mixer", "isTrackSolo", "r", (1,)),
    ("mixer", "soloTrack", "w", (1, 1)), ("mixer", "getTrackPeaks", "r", (1, 0)),
    ("mixer", "getTrackColor", "r", (1,)), ("mixer", "setTrackColor", "w", (1, 255)),
    ("mixer", "getRouteToLevel", "r", (1, 0)), ("mixer", "setRouteToLevel", "w", (1, 0, 0.5)),
    ("mixer", "setRouteTo", "w", (1, 0, True)), ("mixer", "getRouteSendActive", "r", (1, 0)),
    ("mixer", "getEqGain", "r", (1, 0)), ("mixer", "setEqGain", "w", (1, 0, 0.6)),
    ("mixer", "getEqFrequency", "r", (1, 0)), ("mixer", "setEqFrequency", "w", (1, 0, 0.6)),
    ("mixer", "getEqBandwidth", "r", (1, 0)), ("mixer", "setEqBandwidth", "w", (1, 0, 0.6)),
    ("mixer", "getPluginMuteState", "r", (1, 0)), ("mixer", "setPluginMuteState", "w", (1, 0, 1)),
    ("mixer", "getPluginMixLevel", "r", (1, 0)), ("mixer", "setPluginMixLevel", "w", (1, 0, 0.5)),
    ("mixer", "getCurrentTempo", "r", ()), ("mixer", "isTrackArmed", "r", (1,)),
    ("mixer", "setCurrentTempo", "w", (128000,)),
    ("channels", "channelCount", "r", ()), ("channels", "getChannelName", "r", (1,)),
    ("channels", "setChannelName", "w", (1, "Lead")), ("channels", "getChannelVolume", "r", (1,)),
    ("channels", "setChannelVolume", "w", (1, 0.5)), ("channels", "getChannelPan", "r", (1,)),
    ("channels", "setChannelPan", "w", (1, 0.2)), ("channels", "isChannelMuted", "r", (1,)),
    ("channels", "muteChannel", "w", (1, 1)), ("channels", "isChannelSolo", "r", (1,)),
    ("channels", "soloChannel", "w", (1,)), ("channels", "getChannelColor", "r", (1,)),
    ("channels", "setChannelColor", "w", (1, 255)), ("channels", "getTargetFxTrack", "r", (1,)),
    ("channels", "setTargetFxTrack", "w", (1, 2)), ("channels", "getChannelType", "r", (1,)),
    ("channels", "selectOneChannel", "w", (1,)), ("channels", "midiNoteOn", "w", (1, 60, 100)),
    ("patterns", "patternCount", "r", ()), ("patterns", "patternNumber", "r", ()),
    ("patterns", "getPatternName", "r", (1,)), ("patterns", "setPatternName", "w", (1, "Verse")),
    ("patterns", "getPatternLength", "r", (1,)), ("patterns", "jumpToPattern", "w", (2,)),
    ("patterns", "selectPattern", "w", (2, 1)), ("patterns", "findFirstNextEmptyPat", "w", (0,)),
    ("patterns", "isPatternSelected", "r", (1,)), ("patterns", "isPatternDefault", "r", (1,)),
    ("patterns", "setPatternLength", "w", (1, 8)), ("patterns", "incrementPatternLength", "w", (1, 1)),
    ("patterns", "clearPattern", "w", (1,)),
    ("channels", "getSwing", "r", ()), ("channels", "setSwing", "w", (0.25,)),
    ("plugins", "isValid", "r", (0, -1)), ("plugins", "getPluginName", "r", (0, -1)),
    ("plugins", "getParamCount", "r", (0, -1)), ("plugins", "getParamName", "r", (0, 0, -1)),
    ("plugins", "getParamValue", "r", (0, 0, -1)), ("plugins", "setParamValue", "w", (0.7, 0, 0, -1)),
    ("plugins", "getParamValueString", "r", (0, 0, -1)), ("plugins", "getColor", "r", (0, -1)),
    ("playlist", "trackCount", "r", ()), ("playlist", "getTrackName", "r", (1,)),
    ("playlist", "setTrackName", "w", (1, "Drums")), ("playlist", "isTrackMuted", "r", (1,)),
    ("playlist", "muteTrack", "w", (1, 1)), ("playlist", "isTrackSolo", "r", (1,)),
    ("playlist", "soloTrack", "w", (1, 1)), ("playlist", "getTrackColor", "r", (1,)),
    ("playlist", "setTrackColor", "w", (1, 255)),
    ("arrangement", "addAutoTimeMarker", "w", (0, "Drop")), ("arrangement", "jumpToMarker", "w", (1, False)),
    ("arrangement", "currentTime", "r", (0,)),
    ("arrangement", "getMarkerName", "r", (0,), "fl.modules['arrangement'].addAutoTimeMarker(0, 'M')"),
    ("general", "getVersion", "r", ()), ("general", "undo", "w", ()),
    ("general", "saveUndo", "w", ("Edit", 0)), ("general", "getChangedFlag", "r", ()),
    ("ui", "getVersion", "r", ()), ("ui", "showWindow", "w", (0,)), ("ui", "hideWindow", "w", (0,)),
    ("ui", "getProgTitle", "r", ()),
    ("device", "getName", "r", ()), ("device", "isAssigned", "r", ()),
]

# Added 2026-10-25 (docs/ROADMAP.md, "FL control"): the rest of the inventory, so every function FL offers has an op. Sample arguments come
# from the parameter types. Left out on purpose: the ui keystroke functions (cut, copy, paste, delete, insert, enter, escape, yes, no, the
# arrows, jog and strip controls), which act on whatever window has focus in the person's session and belong to guarded GUI recipes, and the
# device functions the dispatcher itself uses (MIDI out, dispatch, refresh threads, master sync).
KEYSTROKE_UI = {"cut", "copy", "paste", "delete", "insert", "enter", "escape", "yes", "no", "up", "down", "left", "right", "next", "previous",
                "jog", "jog2", "moveJog", "strip", "stripHold", "stripJog", "nextWindow", "closeActivePopupMenu", "closeAllMenu"}
DEVICE_INTERNAL = {"midiOutMsg", "midiOutNewMsg", "midiOutSysex", "dispatch", "dispatchGetReceiverPortNumber", "dispatchReceiverCount",
                   "createRefreshThread", "destroyRefreshThread", "fullRefresh", "hardwareRefreshMixerTrack", "directFeedback", "forwardMIDICC",
                   "processMIDICC", "repeatMidiEvent", "stopRepeatMidiEvent", "sendMsgGeneric", "setHasMeters", "setMasterSync", "baseTrackSelect"}
READ_PREFIX = re.compile(r"^(get|is|channelNumber|channelCount|trackNumber|selectedChannel|patternMax|currentTime|selection|liveSelection|safeToEdit"
                         r"|snapMode|findEventID|liveTimeToBlockNum|liveBlockNumToTime|remoteFindEventValue|crDisplayRect|miDisplayRect|miDisplayDockRect)")
SAMPLE_BY_TYPE = {"int": 1, "float": 0.5, "bool": False, "str": "x", "'float | int'": 0.5, "'int | float'": 0.5}


def extended_rows(inv: dict, have: set) -> list[tuple]:
    rows = []
    for key in sorted(inv):
        mod, fn = key.split(".", 1)
        if (mod, fn) in have or mod == "midi" or (mod == "ui" and fn in KEYSTROKE_UI) or (mod == "device" and fn in DEVICE_INTERNAL):
            continue
        spec = inv[key]
        if any(q["type"] not in SAMPLE_BY_TYPE for q in spec["params"]):
            continue
        kind = "r" if spec.get("returns") not in (None, "None") and READ_PREFIX.match(fn) else "w"  # anything else may change FL: a write
        sample = tuple(SAMPLE_BY_TYPE[q["type"]] for q in spec["params"] if q["default"] is None)
        rows.append((mod, fn, kind, sample))
    return rows


# Names the plan listed that the 37.0.1 stubs do not have (FL 2026 additions) or that were renamed.
PLANNED_MISSING = {
    "op_mixer_set_tempo": "built as op_mixer_set_current_tempo (milli-BPM integer, observed on build 26.1.7)",
    "op_patterns_get_swing": "swing is on channels: built as op_channels_get_swing",
    "op_patterns_set_swing": "swing is on channels: built as op_channels_set_swing",
    "op_ui_get_program_title": "renamed: the real function is ui.getProgTitle, generated as op_ui_get_prog_title",
    "op_device_midi_out_sysex": "internal to the dispatcher, not exposed as an op",
}

NOT_BUILT = {
    "setup_sidechain_route": "FL 26.1.7 has no sidechain routing function (only getRouteSendActive, getRouteToLevel, setRouteTo, setRouteToLevel); needs a recorded GUI recipe or the human",
    "import_midi_into_channel": "replaced by import_midi_gui and write_notes_via_script (score.loadScoreFromFile did nothing with a standard MIDI file)",
    "save project": "FL 26.1.7 has no save function in general; only midi.FPT_Save and FPT_SaveNew constants exist (untested), so saving goes through save_project_copy (GUI)",
}

KIND = {"int": "i", "float": "n", "bool": "b", "str": "s", "'float | int'": "n", "'int | float'": "n"}
PYTYPE = {"int": "int", "float": "float", "bool": "bool", "str": "str", "'float | int'": "float", "'int | float'": "float"}
JSONTYPE = {"int": "integer", "float": "number", "bool": "boolean", "str": "string",
            "'float | int'": "number", "'int | float'": "number"}
SETLIKE = re.compile(r"^set[A-Z]")


def snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def default_literal(text: str | None) -> str:
    if text is None:
        return ""
    try:
        ast.literal_eval(text)
        return text
    except (ValueError, SyntaxError):
        return "0"  # midi.PIM_None and similar constants are 0


def render_op(op: str, mod: str, fn: str, params: list[dict]) -> str:
    sig = ", ".join(
        f"{p['name']}: {PYTYPE[p['type']]}" + (f" = {default_literal(p['default'])}" if p["default"] is not None else "")
        for p in params)
    names = ", ".join(p["name"] for p in params)
    lines = [f"import {mod}", "", "", f"def {op}({sig}) -> dict:",
             f'    """Run {mod}.{fn} inside FL Studio and return the outcome as a result dict."""']
    if params:
        argmap = ", ".join(f'"{p["name"]}": {p["name"]}' for p in params)
        kinds = ", ".join(f'"{p["name"]}": "{"j" if p["type"] == "int" and p["default"] == "-1" else KIND[p["type"]]}"' for p in params)
        lines += [f"    bad = _check_args({{{argmap}}}, {{{kinds}}})", "    if bad:", "        return bad"]
    lines.append(f"    return _run({mod}.{fn}" + (f", {names})" if names else ")"))
    return "\n".join(lines) + "\n"


def render_manifest(op: str, mod: str, fn: str, kind: str, params: list[dict], inv: dict) -> str:
    props = {p["name"]: {"type": JSONTYPE[p["type"]]} for p in params}
    req = [p["name"] for p in params if p["default"] is None]
    schema = {"type": "object", "properties": props, "required": req, "additionalProperties": False}
    ret = inv["returns"]
    out = {"type": JSONTYPE[ret]} if ret in JSONTYPE else ({"type": "null"} if ret == "None" else {})
    write = kind == "w"
    summary = (f"Write through {mod}.{fn} in FL Studio." if write else f"Read {mod}.{fn} from FL Studio.")
    return "\n".join([
        "[module]", f'name = "{op}"', 'layer = "L1"', f'summary = "{summary}"', 'version = "1.0.0"', "",
        "[io]", f"input = '''{json.dumps(schema, separators=(',', ':'))}'''",
        f"output = '''{json.dumps(out, separators=(',', ':'))}'''", "",
        "[policy]", f'side_effect = "{"writes_fl_sandbox" if write else "reads_fl"}"',
        f'autonomy = "{"A2" if write else "A0"}"', 'cost = "instant"',
        f"idempotent = {'true' if (not write or SETLIKE.match(fn)) else 'false'}", 'verifier = "none"', "",
        "[deps]", f"min_api = {inv['since']}", "calls = []", "models = []", "binaries = []", "packages = []", "",
        "[tests]", f'golden = "test_{op}.py::test_matches_fake"', f'failure = "test_{op}.py::test_failures"', ""])


def render_test(op: str, mod: str, fn: str, kind: str, sample: tuple, pre: str, nparams: int) -> str:
    pre_line = f"    {pre}\n" if pre else ""
    if kind == "r":
        check = (f"    want = fl.modules['{mod}'].{fn}(*SAMPLE)\n"
                 "    assert r['ok'] is True\n    assert r['value'] == want\n")
    else:
        check = (f"    assert r['ok'] is True\n    assert fl.calls('{mod}', '{fn}')\n")
    bad_arg = ("    assert load_l1(OP)(*((None,) + SAMPLE[1:]))['error']['code'] == 'E_ARG'\n" if nparams else "")
    return f'''"""Tests for {op}: golden against the fake FL, and failure handling."""
import pytest

from coproducer.fakefl import FakeFL
from coproducer.l1load import load_l1

OP = "{op}"
SAMPLE = {sample!r}


@pytest.fixture
def fl():
    f = FakeFL().install()
    yield f
    f.uninstall()


def test_matches_fake(fl):
{pre_line}    r = load_l1(OP)(*SAMPLE)
{check}

def test_failures(fl):
{bad_arg}    def boom(*a, **k):
        raise RuntimeError("fl broke")

    setattr(fl.modules["{mod}"], "{fn}", boom)
    r = load_l1(OP)(*SAMPLE)
    assert r["ok"] is False and r["error"]["code"] == "E_INTERNAL"
'''


def main() -> int:
    inv = json.loads(INV.read_text(encoding="utf-8"))
    HAND_WRITTEN = {"op_raw_call_function"}
    for old in (OUT.glob("op_*") if OUT.exists() else []):
        if old.name not in HAND_WRITTEN:
            shutil.rmtree(old)
    made, problems = [], []
    have = {(r[0], r[1]) for r in CURATED}
    for row in CURATED + extended_rows(inv, have):
        mod, fn, kind, sample = row[:4]
        pre = row[4] if len(row) > 4 else ""
        spec = inv.get(f"{mod}.{fn}")
        if spec is None:
            problems.append(f"{mod}.{fn}: not in stubs")
            continue
        if any(p["type"] not in KIND for p in spec["params"]):
            problems.append(f"{mod}.{fn}: unsupported parameter type")
            continue
        op = f"op_{mod}_{snake(fn)}"
        d = OUT / op
        d.mkdir(parents=True)
        (d / f"{op}.py").write_text(render_op(op, mod, fn, spec["params"]), encoding="utf-8")
        (d / "module.toml").write_text(render_manifest(op, mod, fn, kind, spec["params"], spec), encoding="utf-8")
        (d / f"test_{op}.py").write_text(render_test(op, mod, fn, kind, sample, pre, len(spec["params"])), encoding="utf-8")
        made.append(op)
    rep = ["# L1 generation report", "", f"Generated {len(made)} ops from the FL API stubs 37.0.1 inventory plus the observed live additions.", "",
           "## Left out on purpose", "",
           "- ui keystroke functions (%s): they act on whatever has focus in the person's session; GUI recipes with guards do that work" % ", ".join(sorted(KEYSTROKE_UI)),
           "- device functions the dispatcher uses itself (%s)" % ", ".join(sorted(DEVICE_INTERNAL)),
           "- functions with parameter types the generator does not map (lists, constants objects)", "",
           "## Planned names not generated", ""]
    rep += [f"- `{k}`: {v}" for k, v in sorted(PLANNED_MISSING.items())]
    rep += ["", "## Wrapper and recipe modules not built", ""] + [f"- `{k}`: {v}" for k, v in sorted(NOT_BUILT.items())]
    if problems:
        rep += ["", "## Problems", ""] + [f"- {p}" for p in problems]
    (REPO / "docs").mkdir(exist_ok=True)
    (REPO / "docs" / "l1_missing.md").write_text("\n".join(rep) + "\n", encoding="utf-8")
    print(f"generated {len(made)} ops; problems: {problems}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

"""MCP servers: generated tool lists, phase slicing, meta tools, a real stdio round trip, and the MIDI transport."""
import json
import sys
from pathlib import Path

import anyio
import pytest
from mcp.client import Client
from mcp.client.stdio import StdioServerParameters

from coproducer.bridge import BridgeClient
from coproducer.fakefl import FakeFL
from coproducer.loopback import LoopbackTransport, load_device_script
from coproducer.midi_transport import open_midi_transport
from coproducer.servers.common import build_server, make_session
from coproducer.services import clear_services

MODULES = Path(__file__).resolve().parents[1] / "modules"


@pytest.fixture
def home(tmp_path):
    (tmp_path / "modules").symlink_to(MODULES, target_is_directory=True)
    yield tmp_path
    clear_services()


def run_client(server, fn):
    async def go():
        async with Client(server) as c:
            return await fn(c)
    return anyio.run(go)


def payload(result):
    return json.loads(result.content[0].text)


def test_studio_audio_lists_only_its_layer_with_manifest_schemas(home):
    s = make_session(home, "r1", "studio-audio")
    tools = run_client(build_server(s, "studio-audio", False), lambda c: c.list_tools())
    names = {t.name for t in tools.tools}
    assert {"measure_sample_peak", "estimate_key_dsp", "write_midi_file"} <= names
    assert "set_track_volume_db_verified" not in names and "read_audio_file" not in names and "op_mixer_get_track_name" not in names
    peak = next(t for t in tools.tools if t.name == "measure_sample_peak")
    assert peak.input_schema == s.registry.modules["measure_sample_peak"].input_schema
    assert "[A0, reads_files" in peak.description


def test_tool_call_runs_the_module_and_reports_errors(home, wav):
    from coproducer.synth import sine
    path = wav("tone", sine(1000, 0.5, amp=0.5))
    s = make_session(home, "r1", "studio-audio")

    async def go(c):
        good = await c.call_tool("measure_sample_peak", {"path": path})
        bad = await c.call_tool("measure_sample_peak", {"path": "nope.wav"})
        wrong = await c.call_tool("set_track_volume_db_verified", {"index": 1, "db": -3})
        return good, bad, wrong
    good, bad, wrong = run_client(build_server(s, "studio-audio", False), go)
    assert not good.is_error and abs(payload(good)["value"]["peak_db"] - -6.02) < 0.1
    assert bad.is_error and payload(bad)["error"]["code"] in ("E_IO", "E_NOT_FOUND")
    assert wrong.is_error and payload(wrong)["error"]["code"] == "E_NOT_FOUND"


P1_AUDIO = {"build_measure_report", "estimate_bpm_dsp", "estimate_key_dsp", "detect_sections_dsp", "detect_silence", "detect_leakage",
            "clean_midi_notes", "quantize_notes", "extract_melody_contour", "detect_chord_loop", "write_midi_file", "read_midi_file",
            "load_genre_profile", "load_invariants_file", "build_reference_profile", "find_song_clues", "measure_part_sound",
            "extract_song_loops", "find_matching_loops", "build_wavetable", "prepare_sampler_sound"}


def test_phase_slice_hides_tools_until_requested(home):
    from coproducer.orchestrator.session import save_state
    s = make_session(home, "r1", "studio-audio")
    srv = build_server(s, "studio-audio", True)

    async def names(c):
        return {t.name for t in (await c.list_tools()).tools}

    async def go(c):
        p0 = await names(c)
        s.phase = "P1"
        save_state(s)
        p1 = await names(c)
        refused = await c.call_tool("measure_sample_peak", {"path": "x.wav"})
        return p0, p1, refused
    p0, p1, refused = run_client(srv, go)
    assert p0 == {"load_targets_file", "load_genre_profile", "read_project_anatomy", "check_project_health"} and p1 == P1_AUDIO
    assert refused.is_error and "request_tool" in payload(refused)["error"]["message"]


def attach_fake(s):
    fake = FakeFL()
    BridgeClient(s.registry, LoopbackTransport(fake, load_device_script(fake))).attach(s.registry)
    return fake


def test_fl_bridge_runs_a_plan_through_meta_tools(home):
    s = make_session(home, "r1", "fl-bridge")
    fake = attach_fake(s)
    plan = {"plan_id": "e2e", "steps": [
        {"id": "s01", "phase": "P0", "module": "read_project_summary", "args": {}, "verifier": "none"},
        {"id": "s02", "phase": "P0", "module": "set_track_volume_db_verified", "args": {"index": 1, "db": -6}, "verifier": "readback"}]}

    async def go(c):
        tools = {t.name for t in (await c.list_tools()).tools}
        bad = await c.call_tool("plan_set", {"plan": {"steps": [{"id": "x", "phase": "P0", "module": "nope", "verifier": "none"}]}})
        good = await c.call_tool("plan_set", {"plan": plan})
        ran = await c.call_tool("plan_run", {})
        got = await c.call_tool("plan_get", {})
        status = await c.call_tool("run_status", {})
        tail = await c.call_tool("ledger_tail", {"n": 3})
        added = await c.call_tool("request_tool", {"name": "measure_sample_peak", "reason": "check a bounce"})
        halt = await c.call_tool("halt_run", {"reason": "test"})
        after = await c.call_tool("read_project_summary", {})
        return tools, bad, good, ran, got, status, tail, added, halt, after
    tools, bad, good, ran, got, status, tail, added, halt, after = run_client(build_server(s, "fl-bridge", False), go)
    assert {"plan_set", "plan_run", "ask_human", "phase_advance", "read_project_summary", "set_track_volume_db_verified"} <= tools
    assert bad.is_error and payload(bad)["error"]["code"] == "E_ARG"
    assert not good.is_error and not ran.is_error and payload(ran)["value"]["completed"] == ["s01", "s02"]
    assert [x["done"] for x in payload(got)["value"]["steps"]] == [True, True]
    assert payload(status)["value"]["phase"] == "P0" and len(payload(tail)["value"]) == 3
    assert payload(added)["ok"] and "measure_sample_peak" in payload(added)["value"]   # the slice is shared by all four servers
    assert payload(halt)["ok"] and payload(after)["error"]["code"] == "E_HALTED"
    assert abs(fake.db_law(fake.mixer[1]["volume"]) + 6.0) < 0.2
    fake.uninstall()


def test_ask_human_unattended_writes_the_pending_file(home):
    s = make_session(home, "r1", "fl-bridge")
    got = run_client(build_server(s, "fl-bridge", False), lambda c: c.call_tool("ask_human", {"question": "Half-time?", "options": ["yes", "no"]}))
    assert payload(got)["error"]["code"] == "E_PENDING_HUMAN"
    pending = json.loads((home / "runs" / "r1" / "pending_decisions.json").read_text())
    assert pending == [{"question": "Half-time?", "options": ["yes", "no"]}]


def test_state_is_shared_between_server_processes_through_the_run_folder(home):
    from coproducer.orchestrator.session import save_state
    a = make_session(home, "shared", "fl-bridge")
    a.phase = "P5"
    a.extra_tools.add("estimate_key_dsp")
    save_state(a)
    b = make_session(home, "shared", "studio-audio")
    assert b.phase == "P5" and "estimate_key_dsp" in b.extra_tools


def test_real_stdio_round_trip(home, wav):
    from coproducer.synth import sine
    path = wav("tone", sine(440, 0.5, amp=0.25))
    params = StdioServerParameters(command=sys.executable, args=["-m", "coproducer.servers.studio_audio", "--home", str(home), "--no-slice"])

    async def go(c):
        names = {t.name for t in (await c.list_tools()).tools}
        return names, payload(await c.call_tool("measure_sample_peak", {"path": path}))
    names, res = run_client(params, go)
    assert "measure_integrated_loudness" in names and res["ok"] and abs(res["value"]["peak_db"] - -12.04) < 0.1


class FakePort:
    def __init__(self):
        self.queue, self.closed = [], False

    def send(self, msg):
        self.queue.append(msg)

    def poll(self):
        return self.queue.pop(0) if self.queue else None

    def close(self):
        self.closed = True


class FakeMsg:
    def __init__(self, data, type_="sysex"):
        self.data, self.type = list(data), type_

    @staticmethod
    def from_bytes(data):
        return FakeMsg(data)

    def bytes(self):
        return self.data


class FakeBackend:
    Message = FakeMsg

    def __init__(self):
        self.out, self.inp = FakePort(), FakePort()

    def open_output(self, name):
        if name == "missing":
            raise OSError("no such port")
        return self.out

    def open_input(self, name):
        return self.inp


def test_midi_transport_sends_and_receives_sysex_only():
    be = FakeBackend()
    t = open_midi_transport("coproducer-in", "coproducer-out", be).value
    t.send(bytes([0xF0, 0x7D, 0x43, 0xF7]))
    assert be.out.queue[0].data == [0xF0, 0x7D, 0x43, 0xF7]
    be.inp.queue += [FakeMsg([144, 60, 90], "note_on"), FakeMsg([0xF0, 1, 2, 0xF7])]
    assert t.recv(0.05) == bytes([0xF0, 1, 2, 0xF7]) and t.recv(0.01) is None
    t.close()
    assert be.out.closed and be.inp.closed
    assert open_midi_transport("missing", "x", be).error.code == "E_IO"


class ListingBackend(FakeBackend):
    """Reports ports the way Windows does, with an index after the name."""

    def __init__(self, outs, ins):
        super().__init__()
        self.opened = []
        self._outs, self._ins = outs, ins

    def get_output_names(self):
        return self._outs

    def get_input_names(self):
        return self._ins

    def open_output(self, name):
        self.opened.append(("out", name))
        return self.out

    def open_input(self, name):
        self.opened.append(("in", name))
        return self.inp


def test_midi_names_resolve_to_windows_indexed_ports():
    be = ListingBackend(["Microsoft GS Wavetable Synth 0", "coproducer-in 1", "coproducer-out 2"], ["coproducer-in 3", "coproducer-out 4"])
    got = open_midi_transport("coproducer-in", "coproducer-out", be)
    assert got.ok and be.opened == [("out", "coproducer-in 1"), ("in", "coproducer-out 4")]


def test_midi_exact_and_case_insensitive_names_still_work():
    be = ListingBackend(["coproducer-in"], ["Coproducer-Out"])
    assert open_midi_transport("coproducer-in", "coproducer-out", be).ok and be.opened == [("out", "coproducer-in"), ("in", "Coproducer-Out")]


def test_midi_missing_port_error_lists_what_is_visible():
    be = ListingBackend(["loopMIDI Port 1"], ["loopMIDI Port 1"])
    res = open_midi_transport("coproducer-in", "coproducer-out", be)
    assert res.error.code == "E_IO" and "loopMIDI Port 1" in res.error.message and "'coproducer-in'" in res.error.message
    assert be.opened == []


def test_a_new_chat_can_read_the_skills_through_fl_bridge(home):
    """A Claude Desktop chat has no copy of the repo's skills: fl-bridge serves them read only (2026-10-26)."""
    repo = MODULES.parent
    for d in ("skills", "docs", "styles"):
        (home / d).symlink_to(repo / d, target_is_directory=True)
    s = make_session(home, "r1", "fl-bridge")

    async def go(c):
        tools = {t.name for t in (await c.list_tools()).tools}
        listed = await c.call_tool("list_skills", {})
        skill = await c.call_tool("read_skill", {"name": "remix-from-stems"})
        ref = await c.call_tool("read_skill", {"name": "remix-from-stems/references/creative-brief.md"})
        style = await c.call_tool("read_skill", {"name": "styles/house.json"})
        out = await c.call_tool("read_skill", {"name": "../pyproject.toml"})
        src = await c.call_tool("read_skill", {"name": "docs/../src/coproducer/config.py"})
        return tools, listed, skill, ref, style, out, src
    tools, listed, skill, ref, style, out, src = run_client(build_server(s, "fl-bridge", True), go)
    assert {"list_skills", "read_skill"} <= tools                                  # always listed, whatever the phase
    names = {x["folder"]: x for x in payload(listed)["value"]["skills"]}
    assert "co-producer-protocol" in names and "references/creative-brief.md" in names["remix-from-stems"]["references"]
    assert names["remix-from-stems"]["description"].startswith("Use when")
    assert payload(skill)["value"]["text"].startswith("---") and "Creative first" in payload(skill)["value"]["text"]
    assert "mood" in payload(ref)["value"]["text"] and json.loads(payload(style)["value"]["text"])["name"]
    assert payload(out)["error"]["code"] == "E_ARG" and payload(src)["error"]["code"] == "E_ARG"


def test_every_server_lists_a_tool_in_every_phase(home):
    """Claude Desktop marks a server that lists no tools as failed ("Offered no tools"): studio-ml had none in P0 (rtxclub, 2026-10-27)."""
    from coproducer.servers.tools import SERVER_LAYERS, list_tools
    from coproducer.orchestrator.session import save_state
    s = make_session(home, "r1", "studio-ml")
    for phase in ["P%d" % i for i in range(8)]:
        s.phase = phase
        save_state(s)
        for server in SERVER_LAYERS:
            assert list_tools(s, server, True), (phase, server)

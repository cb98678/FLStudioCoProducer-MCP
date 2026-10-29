"""The live stress scenarios, run against the fake FL so their own logic is tested before they touch a real machine."""
from coproducer.cli import stress_cmd


def test_raw_frame_checksum_and_shape():
    f = stress_cmd.raw_frame(1, 4, 5, 0, 1, [])
    assert f[:4] == bytes(stress_cmd.PREFIX) and f[-1] == 0xF7 and f[-2] == sum(f[4:-2]) & 0x7F
    assert stress_cmd.raw_frame(1, 4, 5, 0, 1, [], checksum_delta=1)[-2] == (f[-2] + 1) & 0x7F
    assert stress_cmd.raw_frame(1, 4, 5, 0, 1, [], terminate=False)[-1] != 0xF7


def test_every_scenario_passes_on_the_fake_fl(rig):
    rows = stress_cmd.run_all(rig.client, rig.reg, rig.transport)
    bad = [r for r in rows if not r["passed"]]
    assert not bad, stress_cmd.render(bad)
    assert len(rows) == 9


def test_the_runner_stops_when_the_bridge_goes_deaf(rig, monkeypatch):
    monkeypatch.setattr(stress_cmd, "alive", lambda *a, **k: False)
    rows = stress_cmd.run_all(rig.client, rig.reg, rig.transport, ["latency", "reads"])
    assert rows[-1]["scenario"] == "abort" and len(rows) == 2


def test_raw_send_falls_back_to_the_driver_when_the_library_refuses():
    sent = []

    class Rt:
        def send_message(self, data):
            sent.append(data)

    class Port:
        _rt = Rt()

    class Picky:
        out_port = Port()

        def send(self, data):
            raise ValueError("invalid sysex end byte")

    assert stress_cmd.send_raw(Picky(), bytes([0xF0, 1])) == "" and sent == [[0xF0, 1]]

    class Stuck:
        def send(self, data):
            raise ValueError("no")

    assert "refused" in stress_cmd.send_raw(Stuck(), b"x")


def test_desktop_scenarios_are_skipped_off_windows():
    import sys
    rows = stress_cmd.desktop_weird(lambda *a, **k: None)
    if sys.platform != "win32":
        assert rows[0]["passed"] and "skipped" in rows[0]["detail"]


def test_a_dead_transport_gives_a_clean_timeout(rig):
    rig.transport.recv = lambda timeout=0.0: None
    r = rig.client.request("op_mixer_track_count", {}, timeout_s=0.1)
    assert not r.ok and r.error.code == "E_TIMEOUT"


def test_stall_hunt_reports_on_the_fake_fl(rig):
    row = stress_cmd.stall_hunt(rig.client, seconds=0.3)
    assert row["passed"] and "pings in" in row["detail"]

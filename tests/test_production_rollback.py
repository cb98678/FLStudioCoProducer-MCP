"""A production move that fails part way leaves the project as it was before the move (2026-10-25 code review)."""
from __future__ import annotations

from coproducer import production, testflp
from coproducer.flpfile import FlpError


def test_a_failed_move_is_rolled_back_and_the_pass_goes_on():
    f = testflp.project({0: "Kick", 1: "Snare"}, {0: [0, 96]}, bars=4)
    before = f.to_bytes()
    log: list = []

    def half_then_fail(g, name):
        g.set_channel_volume_raw(0, 5000)          # a change, then the move finds no room
        raise FlpError("no room for %s" % name)

    def bug(g):
        g.events.append([199, b"x"])
        return {}["missing"]

    assert production._step(log, "half", f, half_then_fail, "chain") is None
    assert production._step(log, "bug", f, bug) is None
    assert f.to_bytes() == before
    assert log[0] == {"step": "half", "ok": False, "why": "no room for chain", "rolled_back": True}
    assert log[1]["ok"] is False and log[1]["why"].startswith("KeyError") and log[1]["rolled_back"]
    assert production._step(log, "fine", f, lambda g: g.set_channel_volume_raw(0, 4000)) is None and log[2]["ok"]
    assert f.to_bytes() != before

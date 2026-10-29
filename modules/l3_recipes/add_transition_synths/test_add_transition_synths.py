from coproducer import anatomy, flpfile, testflp


def _src(tmp_path):
    f = testflp.project({0: "Kick", 1: "FX Bed"}, {0: [0]}, bars=16)
    f.set_track(1, 7)
    f.add_time_marker(8 * 384, "Drop")
    p = tmp_path / "sandbox" / "in.flp"
    p.parent.mkdir(exist_ok=True)
    f.save(str(p))
    return p


def test_adds_each_synth(rig, desk, tmp_path):
    out = tmp_path / "sandbox" / "t.flp"
    todo = [{"kind": "noise_riser", "at": "Drop", "bars": 3}, {"kind": "noise_downlifter", "at": "Drop"}, {"kind": "impact_synth", "at": 9, "insert": 2, "volume": 10000}]
    r = rig.call("add_transition_synths", project=str(_src(tmp_path)), out_project=str(out), synths=todo, key="A", row=5)
    assert r.ok and r.meta["verified"] is True
    riser, down, hit = r.value["placed"]
    assert (riser["start_bar"], riser["bars"], riser["insert"]) == (6, 3.0, 7)  # ends on bar 9, through the FX bed's insert
    assert (down["start_bar"], down["bars"]) == (9, 4.0) and (hit["insert"], hit["notes"]) == (2, [45, 57, 64, 69, 73, 76])
    g = flpfile.Flp.load(str(out))
    chans = {c["id"]: c for c in anatomy.channels(g)}
    assert chans[riser["channel"]]["plugin"] == "3x Osc" and chans[riser["channel"]]["name"] == "Noise Riser Drop" and chans[hit["channel"]]["notes"] == 6
    assert g.channel_pitch(hit["channel"]) == (0, 2) and next(bytes(v) for e, v in g.events[g.block(hit["channel"])[0]:g.block(hit["channel"])[1]] if e == 219)[4:8] == (10000).to_bytes(4, "little")
    clips = [c for c in g.pattern_clips() if c[0] == riser["pattern"]]
    assert clips == [(riser["pattern"], 5 * 384, 3 * 384)]


def test_failures(rig, desk, tmp_path):
    src = str(_src(tmp_path))
    out = str(tmp_path / "sandbox" / "x.flp")
    assert rig.call("add_transition_synths", project=src, out_project=out, synths=[]).error.code == "E_ARG"
    assert rig.call("add_transition_synths", project=src, out_project=out, synths=[{"kind": "noise_riser", "at": "Chorus"}]).error.code == "E_ARG"
    assert rig.call("add_transition_synths", project=src, out_project=out, synths=[{"kind": "noise_riser", "at": 2, "bars": 4}]).error.code == "E_ARG"
    assert rig.call("add_transition_synths", project=src, out_project="/elsewhere/x.flp", synths=[{"kind": "impact_synth", "at": 9}]).error.code == "E_SANDBOX_VIOLATION"

from coproducer import anatomy, flpfile, testflp


def _src(tmp_path):
    f = testflp.project({0: "Kick", 1: "Clap"}, {0: [0, 96, 192, 288], 1: [96, 288]}, samples={0: "C:\\kit\\kick_a.wav", 1: "C:\\kit\\clap.wav"})
    p = tmp_path / "sandbox" / "in.flp"
    p.parent.mkdir(exist_ok=True)
    f.save(str(p))
    return p


def test_builds_a_kick_stack(rig, desk, tmp_path):
    out = tmp_path / "sandbox" / "layer.flp"
    stack = [{"sample": "C:\\kit\\kick_b.wav", "like": "Kick", "pitch_cents": -150}, {"sample": "C:\\kit\\kick_c.wav", "name": "Kick Top", "like": 0, "volume": 6000, "band": "top", "pan": -50}]
    r = rig.call("build_layer_channel", project=str(_src(tmp_path)), out_project=str(out), name="Kick Layer", children=["Kick"], stack=stack)
    assert r.ok and r.meta["verified"] is True
    assert r.value["layer"] == 4 and r.value["children"] == [0, 2, 3] and r.value["moved_notes"] == 4
    g = flpfile.Flp.load(str(out))
    chans = {c["id"]: c for c in anatomy.channels(g)}
    assert chans[4]["type"] == "layer" and chans[4]["name"] == "Kick Layer" and chans[4]["children"] == [0, 2, 3] and chans[4]["notes"] == 4
    assert chans[0]["notes"] == 0 and chans[1]["notes"] == 2  # the kick's notes moved to the layer; the clap is untouched
    assert chans[2]["sample"] == "kick_b.wav" and chans[2]["name"] == "kick_b" and g.channel_pitch(2) == (-150, 2)
    assert chans[3]["name"] == "Kick Top" and chans[3]["insert"] == chans[0]["insert"]
    lv = next(bytes(v) for e, v in g.events[g.block(3)[0] : g.block(3)[1]] if e == 219)
    assert lv[0:4] == (3200).to_bytes(4, "little") and lv[4:8] == (6000).to_bytes(4, "little") and lv[12:24] == bytes.fromhex("20000000" "00000000" "03000000")  # high-passed at 32


def test_failures(rig, desk, tmp_path):
    src = str(_src(tmp_path))
    out = str(tmp_path / "sandbox" / "x.flp")
    assert rig.call("build_layer_channel", project=src, out_project=out, name="L", children=["Kick"]).error.code == "E_ARG"  # one child is not a layer
    assert rig.call("build_layer_channel", project=src, out_project=out, name="L", children=["Kick", "Nope"]).error.code == "E_ARG"
    assert rig.call("build_layer_channel", project=src, out_project="/elsewhere/x.flp", name="L", children=[0, 1]).error.code == "E_SANDBOX_VIOLATION"

def test_a_clean_part_passes_and_a_broken_one_fails(rig):
    sung = [i % 16 < 8 for i in range(64)]                      # she sings the first half of each bar
    good = {"bass": [[b * 4.0 + o, 1.8, 38, 100 if o == 0 else 90] for b in range(4) for o in (0, 2)], "answer": [[2.5, 0.45, 74, 70], [3.0, 0.5, 76, 66]]}
    r = rig.call("check_support_parts", parts=good, sung=sung, cells={str(b): "halves" for b in range(4)})
    assert r.ok and r.value["ok"], r.value["fails"]
    bad = {"bass": good["bass"] + [[1.0, 0.5, 40, 90]], "answer": [[0.5, 0.5, 74, 70]]}
    r = rig.call("check_support_parts", parts=bad, sung=sung, cells={str(b): "halves" for b in range(4)})
    fails = " ".join(r.value["fails"])
    assert not r.value["ok"] and "notes while she sings" in fails and "outside its cells" in fails


def test_unknown_cell_is_refused(rig):
    assert rig.call("check_support_parts", parts={"bass": []}, sung=[], cells={"0": "swing"}).error.code == "E_ARG"

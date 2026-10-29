def test_scores_each_target(rig):
    report = {"loudness": {"lufs": -9.4}, "true_peak": {"dbtp": -0.3}}
    r = rig.call("compare_to_reference", report=report, target={"loudness.lufs": {"value": -9.0, "tolerance": 0.5},
                                                                  "true_peak.dbtp": {"value": -1.0, "tolerance": 0.5}})
    rows = {x["metric"]: x for x in r.value["rows"]}
    assert rows["loudness.lufs"]["within"] is True and rows["loudness.lufs"]["delta"] == -0.4
    assert rows["true_peak.dbtp"]["within"] is False and r.value["all_within"] is False


def test_missing_metrics_are_reported(rig):
    r = rig.call("compare_to_reference", report={"a": 1}, target={"b.c": {"value": 1, "tolerance": 1}})
    assert r.ok and r.value["missing"] == ["b.c"] and r.value["all_within"] is False
    assert rig.call("compare_to_reference", report={}, target={"x": {"value": 1}}).error.code == "E_ARG"

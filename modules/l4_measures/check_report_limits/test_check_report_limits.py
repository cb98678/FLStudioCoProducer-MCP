REPORT = {"loudness": {"lufs": -8.8}, "true_peak": {"true_peak_dbtp": -0.4}, "correlation": {"correlation": 0.5}}


def test_inside_and_outside(rig):
    r = rig.call("check_report_limits", report=REPORT, limits=[
        {"path": "loudness.lufs", "min": -9.5, "max": -8.5, "label": "lufs"},
        {"path": "true_peak.true_peak_dbtp", "max": -1.0, "label": "tp"},
        {"path": "correlation.correlation", "min": 0.2, "label": "corr"}])
    assert r.ok and r.value["failing"] == ["tp"] and r.value["all_within"] is False
    rows = {x["label"]: x for x in r.value["rows"]}
    assert rows["lufs"]["within"] and rows["lufs"]["delta"] == 0.0 and rows["tp"]["delta"] == 0.6


def test_missing_metric_and_empty_limits(rig):
    r = rig.call("check_report_limits", report=REPORT, limits=[{"path": "bands.sub", "min": 0}])
    assert r.value["failing"] == ["bands.sub"] and r.value["rows"][0]["measured"] is None
    assert rig.call("check_report_limits", report=REPORT, limits=[]).error.code == "E_ARG"

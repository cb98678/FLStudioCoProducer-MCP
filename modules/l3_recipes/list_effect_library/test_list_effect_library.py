def test_filters(rig):
    verbs = rig.call("list_effect_library", plugin="Reeverb").value
    assert verbs["count"] > 5 and all("Reeverb" in e["plugin"] for e in verbs["entries"])
    vocal = rig.call("list_effect_library", plugin="Reeverb", text="vocal chop", with_params=True).value
    assert vocal["count"] == 1 and vocal["entries"][0]["params"]["Decay time"] == "1.0sec"


def test_no_match(rig):
    assert rig.call("list_effect_library", plugin="No Such Plugin").value["count"] == 0

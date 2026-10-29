def test_lists_filled_slots_with_state(rig):
    rig.fake.plugins[(1, 0)]["mute"] = 0
    rig.fake.plugins[(1, 0)]["mix"] = 0.5
    r = rig.call("list_effect_slots", index=1)
    assert r.ok and r.value["slots"] == [{"slot": 0, "plugin": "Fake EQ", "active": False, "mix": 0.5}]


def test_empty_track_gives_no_slots(rig):
    r = rig.call("list_effect_slots", index=2)
    assert r.ok and r.value["slots"] == []


def test_default_slot_is_active(rig):
    assert rig.call("list_effect_slots", index=1).value["slots"][0]["active"] is True

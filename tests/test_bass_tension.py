"""Bass-led transitions (skill bass-tension, 2026-11-05): a pitch rise can target the bass part, not only the snare or tom channels, and the
tek_house pack and its production recipe validate with no noise move anywhere."""
from __future__ import annotations

from coproducer import production, stylepack, testflp

NOISE = {"noise_riser", "noise_downlifter", "impact_synth", "filter_sweep", "fx_swell"}


def test_a_pitch_rise_on_a_role_target_rides_that_parts_channel():
    f = testflp.project({0: "Rolling Bass"}, {0: [0, 48]}, bars=8)
    assert production.resolve(f, "bass") == ("insert", 3)          # the role resolves to the part's insert, as every insert move needs
    assert production._channel_on(f, 3) == 0                        # a channel move (pitch_rise) rides the first channel on that insert
    assert production._channel_on(f, 7) is None


def test_the_tek_house_pack_and_recipe_validate_with_no_noise():
    pack = stylepack.load("tek_house")
    assert stylepack.validate(pack) == [] and pack["sources"]
    assert pack["bass"]["pedal"] == ["groove"] and "break" in pack["sub"]["pedal"]    # pedal under the verses, release in the drops
    assert len(pack["bass"]["build"]) == 4 and len(pack["bass"]["build"][-1]) == 32    # the density ramp ends on a 32nd trill
    assert pack["drums"]["build"]["last"]["kick"] == "X...X..........."              # the kick leaves, the bass hangs
    assert "roll" not in pack["drums"]["build"]                                      # no snare roll: the bass is the tension
    recipe = production.load_recipe(pack["production_recipe"])
    assert production.check_recipe(recipe) == []
    moves = {m.get("recipe") or m.get("synth") for v in recipe["transitions"].values() for m in v}
    assert not moves & NOISE
    into_drop = recipe["transitions"]["build>drop"]
    assert any(m.get("recipe") == "pitch_rise" and m["on"] == "bass" for m in into_drop)
    assert any(m.get("recipe") == "lowpass_open" and m["on"] == "bass" for m in into_drop)
    assert any(m.get("recipe") == "gap" and m["on"] == "drum_bus" for m in into_drop)
    assert any(p["on"] == "bass" for p in recipe["pump"])

import copy

import pytest

from coproducer import arrange, remixplan, songplan

PLAN = "plans/friends_in_low_places.json"


@pytest.fixture
def restore():
    saved = songplan.export_current()
    yield
    songplan.apply(saved)


def test_shipped_plan_is_valid_and_matches_the_module():
    plan = songplan.load(PLAN)
    assert songplan.validate(plan) == []
    live = songplan.export_current()
    assert plan == live


def test_apply_round_trip_changes_nothing(restore):
    before = (remixplan.summary(), remixplan.chop_events(), remixplan.fx_cues())
    songplan.apply(songplan.load(PLAN))
    assert (remixplan.summary(), remixplan.chop_events(), remixplan.fx_cues()) == before


def test_arranger_reproduces_the_hand_made_table():
    assert arrange.arrange_chops(remixplan.SECTIONS, remixplan.FRIENDS_ROLES) == remixplan.chop_events()


def test_a_plan_with_roles_only_gets_an_arrangement(restore):
    plan = songplan.load(PLAN)
    plan.pop("chop_events")
    plan.pop("fx_cues")
    songplan.apply(plan)
    assert remixplan.chop_events() == arrange.arrange_chops(remixplan.SECTIONS, remixplan.FRIENDS_ROLES)
    kinds = {c["kind"] for c in remixplan.fx_cues()}
    assert {"impact", "air_sweep", "noise_riser", "tone_riser", "downlifter"} <= kinds
    assert all(c["bar"] >= 0 for c in remixplan.fx_cues())


def test_a_different_section_map_changes_the_tempo_and_length(restore):
    plan = copy.deepcopy(songplan.load(PLAN))
    plan["bpm"], plan["source_bpm"] = 128.0, 100.0
    plan["sections"] = [{"name": "intro", "start": 0, "end": 8}, {"name": "groove", "start": 8, "end": 24}, {"name": "build", "start": 24, "end": 32},
                        {"name": "drop", "start": 32, "end": 48}, {"name": "outro", "start": 48, "end": 56}]
    plan.pop("chop_events")
    plan.pop("fx_cues")
    songplan.apply(plan)
    assert remixplan.TOTAL_BARS == 56 and abs(remixplan.STRETCH - 1.28) < 1e-9
    assert max(e[0] for e in remixplan.chop_events()) < 56
    assert remixplan.summary()["bars"] == 56


@pytest.mark.parametrize("edit,word", [(lambda p: p.pop("bpm"), "missing field"), (lambda p: p["sections"][1].update(start=9), "does not continue"),
                                       (lambda p: p["echoed"].append("nope"), "not in chops"), (lambda p: p["roots8"].pop(), "roots8"),
                                       (lambda p: p.update(roles={}), "roles missing")])
def test_bad_plans_are_refused(edit, word):
    plan = copy.deepcopy(songplan.load(PLAN))
    edit(plan)
    with pytest.raises(songplan.PlanError) as e:
        songplan.apply(plan)
    assert word in str(e.value)

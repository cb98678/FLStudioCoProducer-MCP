"""The contrast loop's decisions (src/coproducer/contrast.py), checked on numbers from the first genre renders."""
from coproducer import contrast, sectiongain


def test_next_scale_aims_from_the_slope():
    assert contrast.next_scale([(0.0, 0.36)], 3.0, 5.5) == round((4.25 - 0.36) / 7.5, 3)      # dnb: first turn by the measured slope
    s = contrast.next_scale([(0.0, 0.36), (1.0, 8.11)], 3.0, 5.5)                              # the old first turn overshot to 8.1
    assert abs(s - (1.0 + (4.25 - 8.11) / 7.75)) < 1e-3
    assert contrast.next_scale([(0.0, 1.0), (0.5, 1.0)], 3.0, 5.5) == round(0.5 + 3.25 / 7.5, 3)  # no change measured: fall back on 7.5
    assert contrast.next_scale([(0.0, None)], 3.0, 5.5) == 0.0
    assert contrast.next_scale([(0.0, -20.0)], 3.0, 5.5) == 3.0                                # clamped


def test_shortfall_by_kind_against_the_loudest_drop():
    rows = [{"section": "Intro", "lufs": -29.4}, {"section": "Build 1", "lufs": -21.4}, {"section": "Drop 1", "lufs": -17.2},
            {"section": "Break", "lufs": -26.8}, {"section": "Drop 2", "lufs": -17.2}, {"section": "Outro", "lufs": -24.5}]
    need = contrast.shortfall(rows, 7.0)
    assert need == {"intro": 5.2, "break": 2.6}            # the outro is 0.3 short, within tolerance; builds belong to the contrast knob
    assert contrast.shortfall(rows, 0.0) == {} and contrast.shortfall([{"section": "Intro", "lufs": -20}], 7.0) == {}


def test_lifts_accumulate_and_cap():
    lifts = contrast.add_lifts({}, {"break": 7.2})
    lifts = contrast.add_lifts(lifts, {"break": 6.0, "intro": 1.0})
    assert lifts == {"break": 12.0, "intro": 1.0}


def test_role_map_lowers_the_rest_past_the_balance_top():
    kinds = ["intro", "groove", "break", "build", "drop", "outro"]
    m = contrast.role_map(sectiongain.DEFAULT_ROLE_GAINS, 0.0, {"intro": 1.4, "break": 7.2, "outro": 2.4}, kinds)   # house v4's lifts
    assert m["break"]["master"] == 5.5 and m["drop"]["master"] == -1.7 and m["groove"]["master"] == -1.7
    assert m["intro"]["master"] == round(1.4 - 1.7, 2) and m["outro"]["master"] == round(2.4 - 1.7, 2)
    assert all(v["master"] <= contrast.BALANCE_MAX_DB for v in m.values())
    m2 = contrast.role_map(sectiongain.DEFAULT_ROLE_GAINS, 0.5, {"break": 2.0}, kinds)          # within the top: nothing else moves
    assert m2["break"]["master"] == 2.0 and m2["build"]["master"] == -3.0 and "drop" not in m2
    assert m2["build"]["kick"] == -1.5
    assert contrast.role_map(sectiongain.DEFAULT_ROLE_GAINS, 0.0, {}, kinds) == {}


def test_drop_over_build_only_counts_drops_after_builds_and_stuck():
    rows = [{"drop": "Drop 1", "before": "Groove 1", "over_before_lu": 0.2}, {"drop": "Drop 2", "before": "Build 2", "over_before_lu": 4.1},
            {"drop": "Drop 3", "before": "Break", "over_before_lu": 9.0}]
    assert contrast.drop_over_build(rows) == 4.1
    assert contrast.drop_over_build(rows[:1]) is None                                    # hip-hop: a hook after a verse
    assert contrast.stuck([(0.0, 0.23), (0.54, 0.22)]) and not contrast.stuck([(0.0, 0.36), (0.52, 4.44)])
    assert not contrast.stuck([(0.0, 0.2)]) and not contrast.stuck([(0.5, 1.0), (0.5, 1.1)])


def test_blocked_stops_turns_the_map_cannot_use():
    """A drop already too far over a quiet build at scale 0 cannot come down by adding contrast: no render is spent on it (2026-10-28)."""
    assert contrast.blocked([(0.0, 7.42)], 3.0, 5.5)                                   # at the lowest scale and above the window
    assert contrast.blocked([(0.0, 5.8), (0.05, 6.14)], 3.0, 5.5)                      # the next scale is the clamped one just rendered
    assert not contrast.blocked([(0.0, 0.36)], 3.0, 5.5) and not contrast.blocked([(0.0, 4.0)], 3.0, 5.5)
    assert not contrast.blocked([(0.0, 0.36), (0.52, 2.0)], 3.0, 5.5)                   # still short and the map can go further
    assert contrast.blocked([(3.0, 1.0)], 3.0, 5.5) and not contrast.blocked([(0.0, None)], 3.0, 5.5)


def test_build_lift_brings_a_quiet_build_up_when_the_map_cannot():
    assert contrast.build_lift([(0.0, 11.0)], 3.0, 5.5) == round(11.0 - 4.25, 2)          # blocked at scale 0: lift to the middle
    assert contrast.build_lift([(0.0, 11.0)], 3.0, 5.5, lifted_db=10.0) == 2.0            # capped by what the builds already took
    assert contrast.build_lift([(0.0, 4.0)], 3.0, 5.5) == 0.0 and contrast.build_lift([(0.0, 1.0)], 3.0, 5.5) == 0.0
    assert contrast.build_lift([(0.0, None)], 3.0, 5.5) == 0.0


def test_section_lifts_raise_only_the_builds_whose_drops_sit_too_far_over_them():
    rows = [{"drop": "Drop 1", "before": "Build 1", "over_before_lu": 6.0}, {"drop": "Drop 2", "before": "Build 2", "over_before_lu": 3.84},
            {"drop": "Drop 3", "before": "Build 3", "over_before_lu": 5.92}, {"drop": "Drop 4", "before": "Groove 2", "over_before_lu": 9.0}]
    got = contrast.section_lifts(rows, 3.0, 5.5)
    assert set(got) == {"Build 1", "Build 3"} and abs(got["Build 1"] - 1.75) < 1e-9
    assert contrast.section_lifts(rows, 3.0, 5.5, {"Build 1": 11.9})["Build 1"] == 11.9   # capped: a 0.1 dB turn is not worth a render
    m = contrast.with_section_lifts({"build": {"master": -1.0, "stab": -2.0}}, got, ["intro", "build", "drop"])
    assert m["Build 1"] == {"master": 0.75, "stab": -2.0} and m["build"] == {"master": -1.0, "stab": -2.0}


def test_a_section_name_in_the_map_wins_over_its_kind():
    from coproducer import sectiongain
    keys = {"build": {}, "Build 1": {}, "drop": {}}
    assert sectiongain.section_kind("Build 1", keys) == "Build 1"
    assert sectiongain.section_kind("Build 2", keys) == "build"
    assert sectiongain.section_kind("Drop 3", keys) == "drop"


def test_floor_lifts_are_per_section_and_the_balance_top_holds():
    rows = [{"section": "Break 1", "lufs": -23.6}, {"section": "Break 2", "lufs": -18.8}, {"section": "Drop 1", "lufs": -16.6},
            {"section": "Intro", "lufs": -25.1}]
    need = contrast.shortfall_each(rows, 6.0)
    assert set(need) == {"Break 1", "Intro"} and abs(need["Intro"] - 2.5) < 1e-9   # Break 2 was never short: it stays where it is
    m = contrast.with_section_lifts({}, {"Intro": 7.0}, ["intro", "break", "drop"])
    assert m["Intro"]["master"] == 5.5 and m["drop"]["master"] == -1.5 and m["break"]["master"] == -1.5

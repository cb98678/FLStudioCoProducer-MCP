"""The evaluation panel's rules (src/coproducer/panel.py)."""
from coproducer import panel, stylepack


def test_yes_no_and_plan_questions():
    assert panel.yes_no("Yes, the kick is on every beat") is True and panel.yes_no("No.") is False and panel.yes_no("It seems...") is None
    qs = panel.plan_questions(stylepack.load("dubstep"))
    assert qs[0]["expect"] is False and qs[1]["expect"] is True          # half time: not four on the floor, snare on 3
    qs = panel.plan_questions(stylepack.load("techno"))
    assert qs[0]["expect"] is True


def test_verdict_rules():
    critic_bad = panel.grade_critic([{"q": "a", "expect": True, "answer": "no"}, {"q": "b", "expect": False, "answer": "yes"}])
    assert critic_bad["grade"] == 0.0 and not critic_bad["trusted"]
    f = [{"judge": "dsp", "item": "loudness", "ok": False}, {"judge": "critic", "item": "muddy low end", "ok": False},
         {"judge": "similarity", "item": "drop sounds like the references", "ok": False}, {"judge": "critic", "item": "drop sounds like the references", "ok": False},
         {"judge": "critic", "item": "vocal clear", "ok": False}, {"judge": "similarity", "item": "vocal clear", "ok": True}]
    v = panel.verdict(f, critic_bad)                                          # an untrusted critic is listed, never counted
    assert [p["item"] for p in v["problems"]] == ["loudness"]
    assert v["ask_person"] == [] and not v["passed"]
    assert {n["item"] for n in v["notes"]} == {"muddy low end", "drop sounds like the references", "vocal clear"}
    critic_ok = panel.grade_critic([{"q": "a", "expect": True, "answer": "yes"}, {"q": "b", "expect": False, "answer": "no"}])
    v = panel.verdict(f, critic_ok)                                           # a trusted critic counts as one weaker judge
    assert [p["item"] for p in v["problems"]] == ["loudness", "drop sounds like the references"]
    assert v["ask_person"] == [{"item": "vocal clear", "for": ["similarity"], "against": ["critic"]}]
    assert v["notes"][0]["item"] == "muddy low end"


def test_plan_questions_have_items():
    qs = panel.plan_questions(stylepack.load("house"))
    assert [q["item"] for q in qs][-1] == "voice audible in the first drop" and qs[-1]["expect"] is None and qs[-1]["yes_means_voice"] is False

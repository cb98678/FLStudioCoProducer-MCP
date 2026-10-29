from pathlib import Path

from coproducer.cards.build import build_card, calibration_summary, save_result
from coproducer.cards.gate import run_gate
from coproducer.cards.parse import build_prompt, card_header, parse_reply, validate_card

REPO = Path(__file__).resolve().parents[1]
MODULES = REPO / "modules"
CARDS = sorted((REPO / "cards" / "calibration").glob("*.card.md"))


def good_reply(name="split_frames", layer="l0_transport", extra_import=""):
    d = MODULES / layer / name
    code = (d / (name + ".py")).read_text()
    code = code.replace("from __future__ import annotations\n", "from __future__ import annotations\n" + extra_import, 1)
    return "\n".join("```python %s\n%s```" % (f, t) for f, t in ((name + ".py", code), ("module.toml", (d / "module.toml").read_text()),
                                                             ("test_%s.py" % name, (d / ("test_%s.py" % name)).read_text())))


def test_all_calibration_cards_are_complete():
    assert len(CARDS) == 10
    for c in CARDS:
        text = c.read_text()
        assert validate_card(text) == [], c.name
        assert card_header(text)["name"] in c.name
        assert "—" not in text
    assert validate_card((REPO / "cards" / "TEMPLATE.card.md").read_text().replace("Card NN", "Card 99")) == []


def test_validate_names_the_missing_field():
    text = CARDS[1].read_text().replace("8. **Out of scope.**", "8. **Nothing.**")
    assert validate_card(text) == ["missing field: Out of scope"]
    assert validate_card("hello")[0].startswith("no header")


def test_parse_reply_accepts_both_label_styles():
    reply = "**a.py**\n```python\nx = 1\n```\nmodule.toml:\n```toml\n[module]\n```\n```python test_a.py\nassert True\n```\n```python\nunlabeled\n```"
    assert parse_reply(reply) == {"a.py": "x = 1\n", "module.toml": "[module]\n", "test_a.py": "assert True\n"}
    assert "Fix only what the report lists." in build_prompt("CARD", "old", "lint: LM-005")


def test_gate_passes_a_good_module_and_names_each_failure():
    files = parse_reply(good_reply())
    assert run_gate("split_frames", files, MODULES)["passed"] is True
    bad = parse_reply(good_reply(extra_import="import os\n"))
    r = run_gate("split_frames", bad, MODULES)
    assert not r["passed"] and r["stage"] == "lint" and "LM-005" in r["report"]
    assert run_gate("split_frames", {}, MODULES)["stage"] == "files"
    broken = dict(files, **{"split_frames.py": files["split_frames.py"].replace("max_len", "max_ln", 1)})
    assert run_gate("split_frames", broken, MODULES)["stage"] in ("lint", "tests")
    assert not run_gate("split_frames", broken, MODULES)["passed"]
    assert not (MODULES / "l0_transport" / "split_frames" / "os").exists()                                  # the real tree is untouched


def test_build_loop_retries_with_the_gate_report_and_saves_only_on_pass(tmp_path):
    card = (REPO / "cards" / "calibration" / "02_split_frames.card.md").read_text()
    replies, seen = [good_reply(extra_import="import os\n"), good_reply()], []

    def ask(system, user):
        seen.append(user)
        return replies[len(seen) - 1]

    res = build_card(card, ask, MODULES, tries=3)
    assert res["passed"] and [a["passed"] for a in res["attempts"]] == [False, True]
    assert "Gate report:" in seen[1] and "LM-005" in seen[1] and "Fix only what the report lists." in seen[1]
    out = save_result(res, tmp_path)
    assert (out / "split_frames.py").is_file() and (out / "attempts.json").is_file()
    assert calibration_summary([res]) == {"cards": 1, "pass_at_1": 0, "pass_at_3": 1, "mean_attempts_on_passing": 2.0}


def test_build_loop_survives_model_errors_and_bad_cards():
    card = (REPO / "cards" / "calibration" / "02_split_frames.card.md").read_text()

    def ask(system, user):
        raise ConnectionError("model server is down")

    res = build_card(card, ask, MODULES, tries=2)
    assert not res["passed"] and [a["stage"] for a in res["attempts"]] == ["model", "model"]
    assert build_card("nonsense", ask, MODULES)["problems"][0].startswith("no header")

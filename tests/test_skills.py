import json
import re
from pathlib import Path

from coproducer.registry import Registry
from coproducer.skills_eval import check_eval
from coproducer.skillsgen import RULES, SKILL_LAYERS, drift, generate

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / "skills"
ASSERT_TYPES = None


def skill_dirs():
    return sorted(p for p in SKILLS.iterdir() if (p / "SKILL.md").is_file())


def test_every_planned_skill_exists_with_good_frontmatter():
    names = {p.name for p in skill_dirs()}
    assert names == set(SKILL_LAYERS) and len(names) == 23
    for d in skill_dirs():
        text = (d / "SKILL.md").read_text(encoding="utf-8")
        m = re.match(r"---\nname: (.+)\ndescription: (.+)\n---\n", text)
        assert m and m.group(1) == d.name and 40 < len(m.group(2)) <= 1024, d.name
        assert text.count("\n") < 300 and "—" not in text, d.name
        assert (d / "evals" / "prompts.json").is_file() and (d / "references").is_dir()


def test_skills_do_not_name_tools_that_do_not_exist():
    assert drift(REPO) == {}


def test_generated_catalogs_are_current(tmp_path):
    generate(REPO, tmp_path)
    for f in tmp_path.rglob("*.md"):
        committed = SKILLS / f.relative_to(tmp_path)
        assert committed.is_file() and committed.read_text(encoding="utf-8") == f.read_text(encoding="utf-8"), "run coproducer gen: %s" % committed


def test_rules_text_covers_every_lint_rule():
    lint = (REPO / "src" / "coproducer" / "lint.py").read_text()
    assert set(re.findall(r"LM-\d{3}", lint)) <= set(RULES)


def test_eval_files_are_valid_and_name_real_tools():
    from coproducer.orchestrator.meta_tools import META
    from coproducer.skills_eval import CHECKS, JUDGED

    reg = Registry(REPO / "modules").load()
    known = set(reg.modules) | set(META)

    def walk(a):
        assert a["type"] in CHECKS or a["type"] in JUDGED or a["type"] == "any_of", a
        if "module" in a:
            assert a["module"] in known, a
        for x in a.get("of", []):
            walk(x)
        for k in ("a", "b"):
            if a["type"] == "called_before":
                assert a[k] in known, a

    for d in skill_dirs():
        data = json.loads((d / "evals" / "prompts.json").read_text())
        assert data["skill"] == d.name and len(data["evals"]) == 3
        assert sum(not e["should_trigger"] for e in data["evals"]) <= 1
        for e in data["evals"]:
            for a in e["assertions"]:
                walk(a)
    for e in json.loads((SKILLS / "cross-evals.json").read_text())["evals"]:
        assert set(e["skills"]) <= {p.name for p in skill_dirs()}


def test_assertion_checker_decides_structural_checks_and_flags_judgment():
    writes = {"set_track_volume_db_verified"}
    ev = json.loads((SKILLS / "studio-ops" / "evals" / "prompts.json").read_text())["evals"][0]
    good = {"calls": [{"module": "list_tracks_summary", "args": {}, "ok": True},
                      {"module": "set_track_volume_db_verified", "args": {"index": 2, "db": -3}, "ok": True, "verified": True}]}
    r = check_eval(ev, good, {"writes": writes})
    assert r["failed"] == [] and r["needs_review"] == ["within_delta_cap"]
    bad = {"calls": [{"module": "set_track_volume_db_verified", "args": {}, "ok": True, "verified": False}]}
    r = check_eval(ev, bad, {"writes": writes})
    assert r["failed"] == ["called_before", "all_writes_verified"] and not r["passed"]
    delete_ev = json.loads((SKILLS / "studio-ops" / "evals" / "prompts.json").read_text())["evals"][2]
    assert check_eval(delete_ev, {"asks": [{"question": "Delete?", "options": ["a", "b"]}], "calls": []}, {"writes": writes})["passed"]
    loop_ev = json.loads((SKILLS / "orchestrator-guide" / "evals" / "prompts.json").read_text())["evals"][1]
    repeat = {"calls": [{"module": "set_track_volume_verified", "args": {"index": 1}}] * 2}
    assert "same_call_not_repeated" in check_eval(loop_ev, repeat, {"writes": writes})["failed"]

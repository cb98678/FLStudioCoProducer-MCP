"""Linter rules LM-001 to LM-015 and registry behavior, using small throwaway modules."""
from pathlib import Path

import pytest

from coproducer.lint import lint_module, lint_tree
from coproducer.registry import Registry

REPO = Path(__file__).resolve().parents[1]

SRC = '''from __future__ import annotations

from coproducer.result import Result, ok


def get_thing(x: int) -> Result:
    """Return x."""
    return ok(x)
'''
TEST = '''def test_golden(fn):
    assert True


def test_failure(fn):
    assert True
'''


def manifest(name="get_thing", layer="L4", side="pure", auto="A0", verifier="none", calls="[]", extra=""):
    return f'''[module]
name = "{name}"
layer = "{layer}"
summary = "Return x."
version = "1.0.0"

[io]
input = \'\'\'{{"type":"object","required":["x"],"properties":{{"x":{{"type":"integer"}}}}}}\'\'\'
output = \'\'\'{{"type":"integer"}}\'\'\'

[policy]
side_effect = "{side}"
autonomy = "{auto}"
cost = "instant"
idempotent = true
verifier = "{verifier}"

[deps]
min_api = 0
calls = {calls}
models = []
binaries = []
packages = []

[tests]
golden = "test_{name}.py::test_golden"
failure = "test_{name}.py::test_failure"
{extra}'''


def make(tmp_path, name="get_thing", src=SRC, man=None, test=TEST, layer_dir="l4_measures"):
    d = tmp_path / layer_dir / name
    d.mkdir(parents=True)
    (d / f"{name}.py").write_text(src.replace("get_thing", name), encoding="utf-8")
    (d / "module.toml").write_text(man if man is not None else manifest(name=name), encoding="utf-8")
    if test is not None:
        (d / f"test_{name}.py").write_text(test, encoding="utf-8")
    return d


def rules(d):
    return {v.rule for v in lint_module(d, {})}


def test_repo_modules_all_pass_lint():
    bad = lint_tree(REPO / "modules")
    assert not bad, {k: [str(x) for x in v] for k, v in bad.items()}


def test_registry_loads_every_repo_module():
    reg = Registry(REPO / "modules").load()
    assert reg.rejected == {} and len(reg.modules) > 150


def test_clean_module_passes(tmp_path):
    assert rules(make(tmp_path)) == set()


@pytest.mark.parametrize("name,src,expect", [
    ("two_funcs", SRC + "\n\ndef get_other(x: int) -> Result:\n    return ok(x)\n", "LM-001"),
    ("badverb_thing", SRC.replace("get_thing", "badverb_thing"), "LM-002"),
    ("get_thing", SRC.replace("(x: int)", "(x)"), "LM-004"),
    ("get_thing", SRC.replace("-> Result", "-> int"), "LM-004"),
    ("get_thing", SRC.replace("from coproducer.result import Result, ok", "import requests\nfrom coproducer.result import Result, ok"), "LM-005"),
    ("get_thing", SRC.replace("    return ok(x)", "    raise ValueError(x)"), "LM-006"),
    ("get_thing", SRC.replace("    return ok(x)", "    try:\n        return ok(x)\n    except:\n        return ok(0)"), "LM-006"),
    ("get_thing", SRC.replace("    return ok(x)", "    return call('nope')"), "LM-008"),
    ("get_thing", SRC.replace('"""Return x."""', '"""Return x."""\n    p = "C:\\\\data\\\\x"'), "LM-013"),
    ("get_thing", SRC.replace("Return x.", "Return x \u2014 now."), "LM-014"),
    ("get_thing", SRC.replace('    """Return x."""\n', ""), "LM-015"),
])
def test_linter_rejects(tmp_path, name, src, expect):
    d = make(tmp_path, name=name, src=src.replace("two_funcs", name) if name != "get_thing" else src)
    assert expect in rules(d), rules(d)


def test_size_budget_enforced(tmp_path):
    body = "\n".join(f"    v{i} = x + {i}" for i in range(45))
    d = make(tmp_path, src=SRC.replace("    return ok(x)", body + "\n    return ok(x)"))
    assert "LM-003" in rules(d)
    d2 = make(tmp_path, name="get_wide", src=SRC.replace("(x: int)", "(a: int, b: int, c: int, d: int, e: int, f: int, g: int)").replace("get_thing", "get_wide"))
    assert "LM-003" in rules(d2)


def test_manifest_problems(tmp_path):
    assert "LM-009" in rules(make(tmp_path, man="[module]\nname='get_thing'\n"))
    assert "LM-009" in rules(make(tmp_path, name="get_two", man=manifest(name="get_two", side="magic")))


def test_tests_must_exist_and_match(tmp_path):
    assert "LM-011" in rules(make(tmp_path, test=None))
    assert "LM-011" in rules(make(tmp_path, name="get_other", test="def test_golden(fn):\n    pass\n"))


def test_write_modules_need_verifier_and_verified(tmp_path):
    man = manifest(side="writes_fl_sandbox", auto="A2", verifier="none")
    assert "LM-010" in rules(make(tmp_path, man=man))
    man = manifest(name="set_thing", side="writes_fl_sandbox", auto="A2", verifier="readback")
    assert "LM-012" in rules(make(tmp_path, name="set_thing", man=man))


def test_upward_calls_rejected_by_linter(tmp_path):
    root = tmp_path
    make(root, name="get_high", layer_dir="l4_measures", man=manifest(name="get_high", layer="L4"))
    low_src = SRC.replace("get_thing", "get_low").replace("    return ok(x)", '    return call("get_high", x=x)').replace(
        "from coproducer.result", "from coproducer import call\nfrom coproducer.result")
    make(root, name="get_low", src=low_src, layer_dir="l2_verified",
         man=manifest(name="get_low", layer="L2", calls='["get_high"]'))
    bad = lint_tree(root)
    assert any(v.rule == "LM-007" for v in bad.get("get_low", []))


def test_registry_policies(tmp_path):
    make(tmp_path)
    reg = Registry(tmp_path).load()
    assert reg.call("get_thing", x=3).value == 3
    assert reg.call("get_thing", x="a").error.code == "E_ARG"
    nf = reg.call("get_thin", x=1)
    assert nf.error.code == "E_NOT_FOUND" and nf.error.detail["nearest"] == ["get_thing"]
    reg.halted = True
    assert reg.call("get_thing", x=1).error.code == "E_HALTED"


def test_registry_autonomy_ceiling_and_approval(tmp_path):
    make(tmp_path, name="set_thing", man=manifest(name="set_thing", side="writes_fl_sandbox", auto="A2", verifier="readback"),
         src=SRC.replace("ok(x)", "ok(x, verified=True)"), test=TEST + "\n# verified\n")
    low = Registry(tmp_path, ceiling="A1").load()
    assert low.call("set_thing", x=1).error.code == "E_AUTONOMY"
    make(tmp_path, name="check_thing", man=manifest(name="check_thing", auto="A1"))
    asks = []
    reg = Registry(tmp_path, ceiling="A2", approver=lambda n, a: asks.append(n) or False).load()
    assert reg.call("check_thing", x=1).error.code == "E_AUTONOMY" and asks == ["check_thing"]
    reg.approver = lambda n, a: True
    assert reg.call("check_thing", x=1).ok


def test_registry_contains_a_raising_module_and_unverified_write(tmp_path):
    make(tmp_path, name="get_boom", src=SRC.replace("get_thing", "get_boom").replace("    return ok(x)", "    return 1 // 0"))
    make(tmp_path, name="set_lazy", man=manifest(name="set_lazy", side="writes_fl_sandbox", auto="A2", verifier="readback"),
         src=SRC.replace("get_thing", "set_lazy") + "\n# verified\n", test=TEST + "\n# verified\n")
    reg = Registry(tmp_path).load()
    assert reg.call("get_boom", x=1).error.code == "E_INTERNAL"
    assert reg.call("set_lazy", x=1).error.code == "E_NOT_VERIFIED"


def test_observer_sees_every_call(tmp_path):
    make(tmp_path)
    seen = []
    reg = Registry(tmp_path, observer=lambda n, a, r, dt: seen.append((n, r.ok))).load()
    reg.call("get_thing", x=1)
    reg.call("nope")
    assert seen == [("get_thing", True), ("nope", False)]

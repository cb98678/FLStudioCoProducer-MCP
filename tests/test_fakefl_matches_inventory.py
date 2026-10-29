"""The fake FL must expose the same names, parameter order and since-levels as the real API stubs."""
import inspect
import json
from importlib import resources

from coproducer.fakefl import FakeFL


def _inv():
    with resources.files("coproducer.data").joinpath("api_inventory.json").open(encoding="utf-8") as f:
        return json.load(f)


def test_fake_signatures_match_stubs():
    inv, fl = _inv(), FakeFL()
    problems = []
    for mname, mod in fl.modules.items():
        for fname in dir(mod):
            if fname.startswith("_") or not callable(getattr(mod, fname)):
                continue
            spec = inv.get(f"{mname}.{fname}")
            if spec is None and f"{mname}.{fname}" in FakeFL.ASSUMED:
                continue
            if spec is None:
                problems.append(f"{mname}.{fname} not in stubs")
                continue
            real = [p["name"] for p in spec["params"]]
            fake = list(inspect.signature(getattr(mod, fname)).parameters)
            if real != fake:
                problems.append(f"{mname}.{fname}: stubs {real} fake {fake}")
    assert not problems, "\n".join(problems)


def test_api_level_hides_newer_functions():
    old = FakeFL(api_level=2)
    assert not hasattr(old.modules["plugins"], "setParamValue")  # since 8
    assert hasattr(FakeFL(api_level=37).modules["plugins"], "setParamValue")

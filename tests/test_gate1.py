"""Gate 1 acceptance: G1-1 (measure report against independent meters) and G1-5 (BPM and key accuracy)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

BENCH = Path(__file__).resolve().parents[1] / "tools" / "gate1_bench.py"


@pytest.fixture(scope="module")
def bench():
    spec = importlib.util.spec_from_file_location("gate1_bench", BENCH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gate1_bench"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_g1_1_measure_report_matches_independent_meters(bench, tmp_path):
    r = bench.g1_1(tmp_path)
    failed = [(row["fixture"], c) for row in r["rows"] for c in row["checks"] if not isinstance(c, dict) or not c["ok"]]
    assert r["fixtures"] >= 19 and r["checks"] >= 100
    assert not failed, failed


def test_g1_5_dsp_accuracy_meets_the_proposed_thresholds(bench):
    r = bench.g1_5(seconds_per_key=3.0)
    v = bench.g1_5_verdict(r)
    assert v["pass"], (v["checks"], r["tempo"]["silent_wrong_cases"])


def test_blind_tempo_is_never_silently_wrong(bench):
    """Every wrong top candidate must come with ambiguous=True, so a caller knows to ask for a hint."""
    r = bench.g1_5(seconds_per_key=2.0)
    assert r["tempo"]["silent_wrong"] == 0, r["tempo"]["silent_wrong_cases"]

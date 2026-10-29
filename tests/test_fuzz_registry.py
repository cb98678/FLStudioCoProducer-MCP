"""Fuzz the registry on the fake FL. A quick sample by default; set COPRODUCER_FUZZ=full to hit all modules (about 8 minutes)."""
import os
import random

import pytest

from coproducer import fuzz

SAMPLE = ["set_rough_balance", "restore_solo_group", "wait_for_reply", "check_sandbox_path", "list_tracks_summary", "load_targets_file",
          "op_mixer_set_current_tempo", "op_patterns_set_pattern_length", "render_via_cli", "build_bus", "separate_stems", "set_tempo_verified",
          "write_midi_file", "read_audio_file", "build_measure_report", "call_agent_llm", "run_gui_recipe", "encode_sysex", "decode_body"]


@pytest.fixture
def world(tmp_path):
    w = fuzz.build_world(tmp_path)
    yield w
    fuzz.close_world(w)


def test_hostile_arguments_never_get_past_the_registry(world):
    names = world.reg.names() if os.environ.get("COPRODUCER_FUZZ") == "full" else [n for n in SAMPLE if n in world.reg.modules]
    assert names
    bad = []
    for n in names:
        bad += [o for o in fuzz.fuzz_module(world, n, random.Random(fuzz.SEED), chaos=3 if os.environ.get("COPRODUCER_FUZZ") != "full" else 25) if o.status == "defect"]
    assert not bad, "\n".join("%s [%s] %s: %s" % (o.module, o.code, o.label[:50], o.note[:120]) for o in bad[:20])


def test_the_generator_covers_every_type_and_marks_wrong_types():
    schema = {"type": "object", "required": ["a"], "properties": {"a": {"type": "integer", "minimum": 0}, "b": {"type": "string"}, "c": {"type": "array", "items": {"type": "number"}}},
              "additionalProperties": False}
    cases = fuzz.cases_for(schema, random.Random(1))
    labels = [c.label for c in cases]
    assert "baseline" in labels and "missing a" in labels and "unknown argument" in labels
    assert any(c.expect_arg_error for c in cases) and any(c.label.startswith("c=") for c in cases)
    assert not any(c.expect_arg_error and c.label.startswith("a wrong type 7") for c in cases)  # 7 is a valid integer


def test_judge_flags_each_kind_of_failure():
    from coproducer.result import fail, ok
    c = fuzz.Case("x", {})
    assert fuzz.judge("m", c, {"exc": ValueError("boom")}, False, 0.1).code == "ESCAPED"
    assert fuzz.judge("m", c, {}, True, 15).code == "HANG"
    assert fuzz.judge("m", c, {"res": 5}, False, 0.1).code == "NOT_A_RESULT"
    assert fuzz.judge("m", c, {"res": fail("E_INTERNAL", "x")}, False, 0.1).status == "defect"
    assert fuzz.judge("m", c, {"res": ok({"v": float("nan")})}, False, 0.1).code == "NOT_STRICT_JSON"
    assert fuzz.judge("m", fuzz.Case("w", {}, True), {"res": ok()}, False, 0.1).code == "ARG_ACCEPTED"
    assert fuzz.judge("m", c, {"res": fail("E_ARG", "bad")}, False, 0.1).status == "refused"

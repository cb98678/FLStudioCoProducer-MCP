
from coproducer.cli import polish_cmd as pc
from coproducer.result import ok


def _props(*calls):
    return [{"name": n, "arguments": a, "valid": True, **extra} for n, a, extra in calls]


def test_eq_db_to_value_is_linear_and_clamped():
    assert pc.eq_db_to_value(0) == 0.5 and abs(pc.eq_db_to_value(7.0) - 0.75) < 1e-9 and pc.eq_db_to_value(99) == 1.0 and pc.eq_db_to_value(-99) == 0.0


def test_moves_are_capped_deduplicated_and_unusable_ones_dropped():
    props = _props(("adjust_eq_band", '{"band":"mid","db":9}', {}), ("adjust_eq_band", '{"band":"mid","db":-2}', {}),
                   ("adjust_eq_band", '{"band":"high","db":-3}', {}), ("adjust_master_gain", '{"db":-3}', {"direction_ok": False}))
    props.append({"name": "adjust_eq_band", "arguments": '{"band":"presence","db":2}', "valid": False})
    assert pc.eq_moves(props) == [("mid", 6.0), ("high", -3.0)] and pc.gain_move(props) is None
    assert pc.gain_move(_props(("adjust_master_gain", '{"db":3}', {"direction_ok": True}))) == 3.0


def test_heard_needs_the_right_sign_and_enough_size():
    assert pc.heard(4.0, 3.0) and not pc.heard(4.0, 1.0) and not pc.heard(4.0, -3.0) and pc.heard(-3.0, -2.0)


class Stub:
    def __init__(self, mid_effect=4.0):
        self.calls, self.reports, self.mid_effect, self.eq = [], 0, mid_effect, {0: 0.5, 1: 0.5, 2: 0.5}

    def __call__(self, name, **kw):
        self.calls.append(name)
        if name == "check_desktop_ready":
            return ok({"title": "s.flp - FL Studio 2026"})
        if name == "set_eq_gain_verified":
            self.eq[kw["band"]] = kw["value"]
            return ok(kw["value"])
        if name == "op_mixer_get_eq_gain":
            return ok(self.eq[kw["band"]])
        if name == "build_measure_report":
            self.reports += 1
            if self.reports == 1:
                return ok({"loudness": {"lufs": -20.0}, "crest": {"rms_db": -18.0}, "bands": {"mid": -15.0, "high_mid": -15.0, "bass": -3.0}})
            return ok({"loudness": {"lufs": -17.0}, "crest": {"rms_db": -15.0}, "bands": {"mid": -15.0 + self.mid_effect, "high_mid": -15.0 + self.mid_effect, "bass": -3.0}})
        if name == "apply_gain_trim":
            return ok({"applied_delta_db": 3.0, "before_db": -3.37})
        if name == "render_with_restart":
            return ok({"path": "/r.wav"})
        if name == "call_agent_llm":
            return ok({"message": {"content": "", "tool_calls": [{"function": {"name": "adjust_master_gain", "arguments": '{"db":3}'}},
                                                                  {"function": {"name": "adjust_eq_band", "arguments": '{"band":"mid","db":4}'}}]}})
        return ok({"bpm": 128.0, "candidates": [], "key": "C", "source": "dsp", "observations": [], "path": "/r.wav"})


def test_polish_applies_checks_and_puts_everything_back(tmp_path):
    call = Stub()
    r = pc.polish(call, tmp_path / "s.flp", tmp_path)
    assert r["passed"] and r["eq_checks"]["mid"]["heard"] and abs(r["eq_checks"]["mid"]["measured_db"] - 4.0) < 0.01
    assert call.eq == {0: 0.5, 1: 0.5, 2: 0.5} and r["steps"]["restore_save"]["ok"] and "restore_fader" in r["steps"]


def test_polish_fails_when_a_move_is_not_heard(tmp_path):
    r = pc.polish(Stub(mid_effect=0.5), tmp_path / "s.flp", tmp_path)
    assert not r["passed"] and r["eq_checks"]["mid"]["heard"] is False


def test_only_unusable_proposals_fail_the_polish(tmp_path):
    class Wrong(Stub):
        def __call__(self, name, **kw):
            if name == "call_agent_llm":
                return ok({"message": {"content": "", "tool_calls": [{"function": {"name": "adjust_master_gain", "arguments": '{"db":-3}'}}]}})
            return super().__call__(name, **kw)
    r = pc.polish(Wrong(), tmp_path / "s.flp", tmp_path)
    assert not r["passed"] and "nothing usable" in r["steps"]["proposals"]["error"]


def test_a_gain_only_polish_checks_the_loudness_moved_by_the_applied_amount(tmp_path):
    class GainOnly(Stub):
        def __call__(self, name, **kw):
            if name == "call_agent_llm":
                self.calls.append(name)
                return ok({"message": {"content": "", "tool_calls": [{"function": {"name": "adjust_master_gain", "arguments": '{"db":3}'}}]}})
            return super().__call__(name, **kw)
    r = pc.polish(GainOnly(), tmp_path / "s.flp", tmp_path)
    assert r["gain_check"] == {"applied_db": 3.0, "moved_lu": 3.0, "ok": True} and r["passed"] and r["kept"] is False
    r = pc.polish(GainOnly(), tmp_path / "s.flp", tmp_path, keep_if_heard=True)
    assert r["kept"] is True and "restore_save" not in r["steps"]

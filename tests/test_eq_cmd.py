
from coproducer.cli import eq_cmd
from coproducer.result import fail, ok


class Stub:
    def __init__(self, fail_on=None):
        self.log, self.fail_on, self.n, self.set_values = [], fail_on, 0, {}

    def __call__(self, name, **kw):
        self.log.append(name)
        if name == self.fail_on:
            return fail("E_NOT_VERIFIED", "stub")
        if name == "set_eq_gain_verified":
            self.set_values[kw["band"]] = kw["value"]
        if name == "render_with_restart":
            self.n += 1
            return ok({"path": "/r%d.wav" % self.n})
        if name == "build_measure_report":
            boosted = any(v != 0.5 for v in self.set_values.values())
            return ok({"loudness": {"lufs": -14.0 + (1.0 if boosted else 0.0)}, "crest": {"rms_db": -12.0 + (1.0 if boosted else 0.0)},
                       "bands": {"bass": -10.0 + (3.0 if boosted else 0.0), "air": -20.0}})
        return ok({})


def test_band_deltas_only_compares_bands_both_have_and_adds_back_the_total_change():
    assert eq_cmd.band_deltas({"bands": {"a": -10.0, "b": -5.0}}, {"bands": {"a": -7.5, "c": 1.0}}) == {"a": 2.5}
    flat, tested = {"bands": {"a": -10.0, "b": -20.0}, "crest": {"rms_db": -12.0}}, {"bands": {"a": -10.0, "b": -26.0}, "crest": {"rms_db": -6.0}}
    assert eq_cmd.band_deltas(flat, tested) == {"a": 6.0, "b": 0.0}       # b fell 6 dB relative to a signal that got 6 dB louder, so it did not change


def test_calibrates_three_bands_and_puts_the_eq_back_flat(tmp_path):
    call = Stub()
    r = eq_cmd.eq_calibration(call, tmp_path / "s.flp", tmp_path)
    assert r["passed"] and set(r["bands"]) == {"low", "mid", "high"} and len(r["bands"]["mid"]) == 2 and r["bands"]["mid"][0]["peak_db"] == 3.0 + 1.0 - 0.0
    assert call.set_values == {0: 0.5, 1: 0.5, 2: 0.5} and r["restore_save"]


def test_a_failed_set_is_reported_and_the_eq_still_restored(tmp_path):
    call = Stub(fail_on="save_sandbox_project")
    r = eq_cmd.eq_calibration(call, tmp_path / "s.flp", tmp_path)
    assert not r["passed"]

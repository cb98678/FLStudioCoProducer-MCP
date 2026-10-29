import json

import pytest

from coproducer import edison as E


class Region:
    def __init__(self, name, a, b):
        self.Name, self.SampleStart, self.SampleEnd = name, a, b


class FakeSample:
    def __init__(self, n=44100, ch=2, rate=44100):
        self.Length, self.NumChans, self.SampleRate = n, ch, rate
        self.regions, self.amps = [], []

    @property
    def RegionCount(self):
        return len(self.regions)

    def GetRegion(self, i):
        return self.regions[i]

    def AddRegion(self, name, a, b):
        self.regions.append(Region(name, a, b))
        return len(self.regions) - 1

    def MSToSamples(self, t):
        return t * self.SampleRate / 1000.0

    def AmpFromTo(self, a, b, v):
        self.amps.append((a, b, v))


class FakeEditor:
    SelectionStartS, SelectionEndS = 100, 900


class FakeUtils:
    def __init__(self):
        self.messages = []

    def ShowMessage(self, m):
        self.messages.append(m)


def run(script, sample):
    """Execute a generated script the way Edison does: enveditor names are globals, `from enveditor import *` is a no-op here."""
    code = script.replace("from enveditor import *\n", "")
    g = {"EditorSample": sample, "Editor": FakeEditor(), "Utils": FakeUtils()}
    exec(compile(code, "<pyscript>", "exec"), g)  # noqa: S102 (our own generated text)
    return g


def test_filename_rules():
    assert E.script_filename("coproducer probe") == "coproducer probe.pyscript"
    with pytest.raises(ValueError):
        E.script_filename("../evil")


def test_probe_script_writes_state(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "probe.json"
    s = FakeSample()
    s.AddRegion("a", 10, 20)
    run(E.probe_script("probe.json"), s)
    d = json.loads(out.read_text())
    assert d["length"] == 44100 and d["channels"] == 2 and d["selection_end"] == 900
    assert d["regions"] == [{"name": "a", "start": 10, "end": 20}]


def test_probe_script_refuses_paths():
    for bad in ("C:/x/p.json", "..\\p.json", "a/b.json"):
        with pytest.raises(ValueError):
            E.probe_script(bad)


def test_regions_script_cuts_between_slice_starts():
    s = FakeSample(n=44100)
    run(E.regions_script([0, 250, 500], prefix="vox"), s)
    got = [(r.Name, r.SampleStart, r.SampleEnd) for r in s.regions]
    assert got == [("vox 1", 0, 11024), ("vox 2", 11025, 22049), ("vox 3", 22050, 44099)]
    s2 = FakeSample(n=44100)
    run(E.regions_script([100], end_ms=300), s2)
    assert s2.regions[0].SampleEnd == round(300 * 44.1) - 1


@pytest.mark.parametrize("bad", [[], [5, 5], [10, 5], [-1, 4]])
def test_regions_script_refuses_bad_times(bad):
    with pytest.raises(ValueError):
        E.regions_script(bad)


def test_gain_script_is_linear_factor():
    s = FakeSample()
    run(E.gain_script(-6.0), s)
    assert s.amps[0][:2] == (100, 900) and s.amps[0][2] == pytest.approx(0.5012, abs=1e-3)
    with pytest.raises(ValueError):
        E.gain_script(40)


def test_no_em_dash():
    import pathlib
    assert "—" not in pathlib.Path(E.__file__).read_text(encoding="utf-8")


class AudioSample(FakeSample):
    """A mono list-backed sample that really performs the range methods the runner uses."""

    def __init__(self, data, rate=1000):
        super().__init__(n=len(data), ch=1, rate=rate)
        self.data = list(data)

    @property
    def Length(self):
        return len(self.data)

    @Length.setter
    def Length(self, v):
        pass

    def SamplesToMS(self, n):
        return n * 1000.0 / self.SampleRate

    def AmpFromTo(self, a, b, v):
        for i in range(a, b + 1):
            self.data[i] *= v

    def SilenceFromTo(self, a, b):
        self.AmpFromTo(a, b, 0.0)

    def ReverseFromTo(self, a, b):
        self.data[a : b + 1] = self.data[a : b + 1][::-1]

    def InsertSilence(self, a, b):
        self.data[a:a] = [0.0] * (b - a + 1)

    def DeleteFromTo(self, a, b, copy=False):
        del self.data[a : b + 1]

    def TrimFromTo(self, a, b):
        self.data = self.data[a : b + 1]

    def NormalizeFromTo(self, a, b, vol, only_if_above=False):
        peak = max(abs(x) for x in self.data[a : b + 1])
        self.AmpFromTo(a, b, vol / peak)

    def ConvertToMono(self, mode):
        pass


def run_job(tmp_path, monkeypatch, ops, sample):
    monkeypatch.chdir(tmp_path)
    (tmp_path / E.JOB_FILE).write_text(json.dumps(E.check_job(ops)))
    run(E.runner_script(), sample)
    return json.loads((tmp_path / E.RESULT_FILE).read_text())


def test_runner_grid_regions_on_the_beat(tmp_path, monkeypatch):
    s = AudioSample([0.5] * 4000, rate=1000)  # 120 bpm: a beat is 500 ms = 500 samples
    out = run_job(tmp_path, monkeypatch, [{"op": "grid", "bpm": 120, "step_beats": 1, "offset_ms": 0}], s)
    assert [(r["start"], r["end"]) for r in out["regions"]][:2] == [(0, 499), (500, 999)] and len(out["regions"]) == 8


def test_runner_fit_and_trim_to_bars(tmp_path, monkeypatch):
    s = AudioSample([0.5] * 5000, rate=1000)  # one bar at 120 bpm is 2000 samples
    out = run_job(tmp_path, monkeypatch, [{"op": "fit_length", "bpm": 120, "bars": 2}], s)
    assert out["after"] == 4000 and len(s.data) == 4000
    s2 = AudioSample([0.5] * 1500, rate=1000)
    run_job(tmp_path, monkeypatch, [{"op": "fit_length", "bpm": 120, "bars": 1}], s2)
    assert len(s2.data) == 2000 and s2.data[-1] == 0.0
    s3 = AudioSample([0.5] * 9000, rate=1000)
    run_job(tmp_path, monkeypatch, [{"op": "trim_to_bars", "bpm": 120, "bars": 2, "offset_ms": 500}], s3)
    assert len(s3.data) == 4000


def test_runner_fades_gain_and_normalize(tmp_path, monkeypatch):
    s = AudioSample([1.0] * 1000, rate=1000)
    run_job(tmp_path, monkeypatch, [{"op": "fade_in", "ms": 100}, {"op": "fade_out", "ms": 100}, {"op": "gain", "db": -6.0}], s)
    assert s.data[0] < 0.02 and s.data[-1] < 0.02 and s.data[500] == pytest.approx(0.5012, abs=1e-3)
    assert s.data[50] < s.data[99] < s.data[500]
    s2 = AudioSample([0.25, -0.5, 0.1], rate=1000)
    run_job(tmp_path, monkeypatch, [{"op": "normalize"}], s2)
    assert max(abs(x) for x in s2.data) == pytest.approx(1.0)


def test_runner_reports_a_failing_op_and_stops(tmp_path, monkeypatch):
    class Boom(AudioSample):
        def ReverseFromTo(self, a, b):
            raise RuntimeError("nope")

    out = run_job(tmp_path, monkeypatch, [{"op": "reverse"}, {"op": "gain", "db": 0}], Boom([0.1] * 10))
    assert out["log"] == [{"i": 0, "ok": False, "error": "RuntimeError nope"}]


@pytest.mark.parametrize("bad", [[], [{"op": "stretch"}], [{"op": "gain"}], [{"op": "gain", "db": 99}],
                                 [{"op": "grid", "bpm": 0, "step_beats": 1}], [{"op": "regions", "times_ms": [5, 5]}]])
def test_check_job_refuses(bad):
    with pytest.raises(ValueError):
        E.check_job(bad)

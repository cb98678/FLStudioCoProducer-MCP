"""soundbrief.revise: what a match round changes on the patch."""
from coproducer import soundbrief


def _spec(cutoff):
    return {"oscillators": [{"volume": 0.75, "wavetable": "analog_warm", "unison": 4.0, "detune": 0.25}],
            "envelopes": [{"attack": 0.01, "hold": 0.0, "decay": 1.0, "sustain": 0.0, "release": 0.3}],
            "filters": [{"type": "lowpass_24", "cutoff": cutoff, "resonance": 5.0}], "fx_chain": []}


def _cmp(ratio):
    return {"differences": {"centroid_ratio": ratio}}


def test_a_dark_remake_with_the_filter_open_gets_upper_harmonics():
    new, done = soundbrief.revise(_spec(1.0), _cmp(0.24), {})
    assert len(new["oscillators"]) == 2 and new["oscillators"][1]["wavetable"] == "analog_basic"
    assert new["fx_chain"][0]["type"] == "FXDistortion" and new["fx_chain"][0]["wet"] > 0
    assert new["filters"][0]["cutoff"] == 1.0
    again, _ = soundbrief.revise(new, _cmp(0.5), {})     # the next round drives harder, no third oscillator
    assert len(again["oscillators"]) == 2 and again["fx_chain"][0]["wet"] > new["fx_chain"][0]["wet"]
    assert any("osc B" in x for x in done)


def test_a_dark_remake_with_the_filter_closed_opens_the_cutoff_first():
    new, done = soundbrief.revise(_spec(0.5), _cmp(0.5), {})
    assert new["filters"][0]["cutoff"] > 0.5 and len(new["oscillators"]) == 1
    assert any(x.startswith("cutoff") for x in done)

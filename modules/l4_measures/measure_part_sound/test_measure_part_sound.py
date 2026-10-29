"""Synthetic parts whose sound is known: a saw pluck that dies away, a square pad with a slow attack and a held level, a sine bass."""
import numpy as np

RATE = 44100


def tone(f0, secs, shape="saw", count=30):
    t = np.arange(int(secs * RATE)) / RATE
    ks = range(1, count + 1) if shape == "saw" else range(1, count + 1, 2) if shape == "square" else [1]
    return sum(np.sin(2 * np.pi * k * f0 * t) / k for k in ks if k * f0 < RATE / 2.2)


def notes(fn, gap, n, f0s):
    """n notes, each followed by gap seconds of silence."""
    out = []
    for i in range(n):
        out += [fn(f0s[i % len(f0s)]), np.zeros(int(gap * RATE))]
    return np.concatenate(out)


def pluck(f0):
    t = np.arange(int(0.6 * RATE)) / RATE
    return 0.5 * tone(f0, 0.6) * np.minimum(1, t / 0.002) * np.exp(-t / 0.15)


def pad(f0):
    t = np.arange(int(1.6 * RATE)) / RATE
    amp = np.where(t < 0.2, t / 0.2, 0.6 + 0.4 * np.exp(-(t - 0.2) / 0.1))
    amp = np.where(t > 1.2, amp * np.exp(-(t - 1.2) / 0.05), amp)
    return 0.3 * tone(f0, 1.6, "square") * amp


def test_a_pluck_and_a_pad_read_as_themselves(rig, wav):
    got = rig.call("measure_part_sound", path=wav("pluck", notes(pluck, 0.2, 6, [220.0, 246.9, 261.6])), role="pluck").value
    s = got["sound"]
    assert s["attack_s"] <= 0.01 and s["sustain"] == 0.0 and abs(s["decay_s"] - 0.15 * np.log(10)) < 0.06   # -20 dB after 0.35 s
    assert s["shape"] == "saw" and abs(s["harmonics"]["slope_db_per_octave"] + 6.0) < 1.5 and "plucked (short decay)" in s["words"]
    assert s["register"]["median"] in ("A3", "B3", "C4") and s["width"]["word"] == "mono"
    draft = got["starting_point"]["spec"]
    assert len(draft["oscillators"][0]["custom_harmonics"][-1]) >= 20 and draft["envelopes"][0]["sustain"] == 0.0

    s = rig.call("measure_part_sound", path=wav("pad", notes(pad, 0.4, 3, [110.0, 130.8])), role="pad").value["sound"]
    assert 0.12 < s["attack_s"] < 0.2 and abs(s["sustain"] - 0.6) < 0.08 and s["release_s"] is not None and s["release_s"] < 0.4
    assert s["shape"] == "square" and s["harmonics"]["odd_minus_even_db"] > 12 and "soft, slow attack" in s["words"]


def test_a_sine_bass_and_a_wide_part(rig, wav):
    def sub(f0):
        t = np.arange(int(0.5 * RATE)) / RATE
        return 0.6 * np.sin(2 * np.pi * f0 * t) * np.minimum(1, t / 0.005) * np.minimum(1, (0.5 - t) / 0.01)
    got = rig.call("measure_part_sound", path=wav("sub", notes(sub, 0.25, 4, [55.0, 61.7])), role="bass").value
    assert got["sound"]["shape"] == "sine" and got["starting_point"]["spec"]["global"]["mono"] is True
    m = notes(pluck, 0.2, 4, [330.0])
    rng = np.random.default_rng(0)
    left, right = m + 0.05 * rng.standard_normal(len(m)) * (np.abs(m) > 0.01), np.roll(m, 300)
    wide = rig.call("measure_part_sound", path=wav("wide", np.stack([left, right], 1))).value
    assert wide["sound"]["width"]["word"] in ("medium", "wide") and wide["starting_point"]["spec"]["oscillators"][0]["unison"] >= 2.0


def test_failures(rig, wav, tmp_path):
    assert rig.call("measure_part_sound", path=str(tmp_path / "missing.wav")).error.code == "E_IO"
    assert rig.call("measure_part_sound", path=wav("quiet", np.zeros(RATE))).error.code == "E_NOT_FOUND"
    assert rig.call("measure_part_sound", path=wav("x", np.zeros(RATE)), start_s=2.0, end_s=1.0).error.code == "E_ARG"
    assert rig.call("measure_part_sound", path="").error.code == "E_ARG"


def test_a_held_drone_and_a_slow_swell_still_read_as_notes():
    """No fast onset (a drone already sounding when the slice starts, a pad swelling in over a second): read as held notes, not as nothing."""
    from coproducer import soundbrief
    drone = 0.3 * tone(55.0, 4.0, "square")
    d = soundbrief.describe(drone, RATE)
    assert d["notes"] >= 1 and d.get("register", {}).get("median", "").startswith("A")
    t = np.arange(int(3.0 * RATE)) / RATE
    swell = 0.3 * tone(220.0, 3.0, "saw") * np.minimum(1.0, t / 1.2) ** 2
    assert soundbrief.describe(swell, RATE)["notes"] >= 1
    assert soundbrief.describe(np.zeros(RATE), RATE)["notes"] == 0

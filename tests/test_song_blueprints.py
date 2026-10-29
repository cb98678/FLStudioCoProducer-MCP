"""Moves from the person's song breakdowns (Clarity, Red Lights, Another Night, 2026-10-29): every new option realizes, the voice-led pad
holds its common tones, a lead can phrase in threes across the bar, and the pump can recover on a curve."""
from __future__ import annotations

from coproducer import pump, stylepack, variety

BANK = variety.load_bank()
NEW = ("harmony.pop_I_V_vi_IV", "harmony.sus_ii_V_vi_iii_IV", "harmony.minor_i_VI_III_VII", "harmony.eurodance_i_VI_VII_v", "bass.euro_gallop",
       "bass.inverted_turnaround", "bass.empty_verse_square_drop", "chords.tresillo_332_pluck", "chords.voice_led_pad", "arp.three_over_four",
       "mix.exp_recovery_pump", "vocal.dry_verse_wide_chorus", "chords.pad_and_spaced_stabs", "bass.roll_then_long_drop")


def test_every_blueprint_option_is_in_the_bank_and_cites_a_checked_record():
    refs = variety.sources(which=("references",))
    assert set(refs) == {"clarity", "red_lights", "another_night"} and all(r["verified"] and r["urls"] for r in refs.values())
    for oid in NEW:
        o = variety.find(BANK, oid)
        assert o["sources"] and all(s["song"] in variety.sources() for s in o["sources"]), oid


def test_the_voice_led_pad_keeps_common_tones_while_the_bass_leaps():
    gm, eb, bb, f = [55, 58, 62], [51, 55, 58], [58, 62, 65], [53, 57, 60]     # Red Lights' chords as root-position triads
    prev, moved = None, 0
    for keys in (gm, eb, bb, f):
        led = stylepack.lead_voices(prev, keys, 50, 74)
        assert sorted(k % 12 for k in led) == sorted(k % 12 for k in keys) and 50 <= min(led) and max(led) <= 74
        if prev:
            moved += sum(abs(a - b) for a, b in zip(sorted(prev), led))
        prev = led
    assert moved == 7                                                               # small steps; root position would jump far more


def test_a_three_over_four_lead_crosses_the_bar_and_resolves_on_bar_four():
    spec = variety.find(BANK, "arp.three_over_four")["engine"]
    secs = [{"name": "drop", "start": 0, "end": 4}]
    ck = lambda pc, base=60: [base + pc, base + pc + 3, base + pc + 7]  # noqa: E731
    notes = stylepack.arp_notes({"arp": spec}, secs, lambda b: 9, ck, 9, "minor")
    steps = sorted({round(n[0] * 4) for n in notes})
    assert steps[:12] == [0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33]            # every third 16th through bars 1 to 3
    assert [s for s in steps if s >= 48] == [48, 52, 56, 60]                       # bar 4 on the beat


def test_the_exp_pump_recovers_fast_then_eases_in():
    lin = pump.pump_points([1.0], 4.0, -24.0)
    exp = pump.pump_points([1.0], 4.0, -24.0, curve="exp")
    assert len(exp) == len(lin) + 4 and all(lo[0] == ex[0] for lo, ex in zip(lin[:3], exp[:3]))
    mid = [v for t, v in exp if 1.1 < t < 1.3]
    assert mid == sorted(mid) and mid[0] > pump.db_to_fader(-24.0)                 # rising from the dip
    assert "curve" in str(variety.find(BANK, "mix.exp_recovery_pump")["engine"])

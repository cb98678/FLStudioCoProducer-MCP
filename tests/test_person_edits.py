"""Rules taken from the person's own edit of the techno remix (friends_techno_produced_2.flp, 2026-10-26), so every later remix starts there."""
import json
import struct

from coproducer import fxlib, remixbuild, remixplan, transitions


def test_the_drum_bus_flanger_is_saved_neutral_and_out_of_the_default_recipes():
    entry = transitions.neutral("fx_swell", fxlib.load_entry("fh Drum Group Fruity Flanger"))
    state = bytes.fromhex(next(h for e, h in entry["events"] if e == 213))
    ints = struct.unpack("<%di" % (len(state) // 4), state)
    assert ints[10] == 4000 and ints[11] == 0          # dry at 0 dB, wet off: silent wherever no clip drives it
    assert transitions.neutral("reverb_throw", {"events": [[213, "00"]]}) == {"events": [[213, "00"]]}
    for name in ("techno", "club_house"):
        recipe = json.load(open("recipes/production/%s.json" % name))
        assert not [x for steps in recipe["transitions"].values() for x in steps if x.get("recipe") == "fx_swell"]


def test_the_persons_sound_and_levels_are_the_starting_point():
    assert remixbuild.SERUM_PRESETS["stab"] == "PL Crusty Pluck [LCV]" and remixbuild.SERUM_DB["stab"] == -2.5
    assert remixplan.SONG_FORM_DB == {"orig": -5.0, "fx": -6.5}


def test_a_chop_keeps_the_songs_beat_phase():
    """The person moved every Curse of Curves chop later by about the part of a beat its first word sits before a beat (2026-10-26)."""
    old = (remixplan.SOURCE_BPM, remixplan.ORIGIN_S, remixplan.VOCAL_MULTIPLE)
    try:
        remixplan.SOURCE_BPM, remixplan.ORIGIN_S, remixplan.VOCAL_MULTIPLE = 145.994, 13.44, 1.0
        meta = {"chops": {"hook": {"orig_start_s": 26.36}, "line1": {"orig_start_s": 46.433}, "beat": {"orig_start_s": 13.44 + 4 * 60 / 145.994}}}
        hook, line = remixbuild.chop_phase(meta, "hook"), remixbuild.chop_phase(meta, "line1")
        assert abs(hook - 0.437) < 0.01 and abs(line - 0.28) < 0.01          # beats: 0.18 s and 0.115 s at 146 bpm
        assert abs(hook * 60 / 145.994 / (240 / 145.994) - 0.109) < 0.005      # the person's own moves: 0.078 to 0.125 bar (hook), 0.0625 (line)
        assert remixbuild.chop_phase(meta, "beat") == 0.0 and remixbuild.chop_phase(meta, "hook_echo") == hook
        assert remixbuild.chop_phase({"chops": {"x": {}}}, "x") == 0.0
    finally:
        remixplan.SOURCE_BPM, remixplan.ORIGIN_S, remixplan.VOCAL_MULTIPLE = old


def test_house_starts_from_the_persons_master_b(tmp_path):
    """The Curse of Curves master the person picked ("B is great", 2026-10-26): kick with less sub, clap, hats, FX and arp lower, vocal up."""
    import numpy as np
    import soundfile as sf

    from coproducer import oneshots, stylepack
    house = stylepack.load("house")
    assert house["kick_sub_shelf"]["hz"] == 60 and house["kick_sub_shelf"]["db"] == -4.5
    assert remixbuild.start_db("clap", -4.0, False, remixbuild.SERUM_DB, house) == -7.5
    assert remixbuild.start_db("arp", 3.0, True, remixbuild.SERUM_DB, house) == -6.5    # the style's balance wins over the Serum sound's level
    assert remixbuild.start_db("arp", 3.0, True, remixbuild.SERUM_DB, None) == remixbuild.SERUM_DB["arp"]
    rate = 44100
    t = np.arange(rate) / rate
    x = 0.4 * np.sin(2 * np.pi * 35 * t) + 0.4 * np.sin(2 * np.pi * 400 * t)
    p = tmp_path / "k.wav"
    sf.write(str(p), x.astype(np.float32), rate, subtype="PCM_16")
    oneshots.shelve(p, 60, -4.5)
    y, _ = sf.read(str(p))

    def level(sig, hz):
        return 20 * np.log10(abs(np.dot(sig[rate // 2:], np.sin(2 * np.pi * hz * t[rate // 2:]))) + 1e-9)
    assert -5.0 < level(y, 35) - level(x, 35) < -3.0 and abs(level(y, 400) - level(x, 400)) < 0.3   # the sub drops, the body stays

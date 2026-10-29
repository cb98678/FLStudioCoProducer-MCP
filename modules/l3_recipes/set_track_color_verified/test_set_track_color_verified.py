def test_sets_in_the_reference_order(rig):
    rig.fake.mixer[1]["color"] = 0x50AF4C  # (76, 175, 80) as blue, green, red
    r = rig.call("set_track_color_verified", index=3, rgb=[255, 235, 59], like_index=1, like_rgb=[76, 175, 80])
    assert r.ok and r.meta["verified"] and r.value["order"] == "bgr" and rig.fake.mixer[3]["color"] == (59 << 16) | (235 << 8) | 255
    rig.fake.mixer[1]["color"] = (76 << 16) | (175 << 8) | 80
    r = rig.call("set_track_color_verified", index=3, rgb=[255, 235, 59], like_index=1, like_rgb=[76, 175, 80])
    assert r.value["order"] == "rgb" and rig.fake.mixer[3]["color"] == (255 << 16) | (235 << 8) | 59


def test_reads_fls_signed_alpha_form(rig):
    rig.fake.mixer[1]["color"] = (0xFF000000 | 0x50AF4C) - (1 << 32)  # what FL returns: signed, alpha 0xFF
    r = rig.call("set_track_color_verified", index=3, rgb=[255, 235, 59], like_index=1, like_rgb=[76, 175, 80])
    assert r.ok and r.value["order"] == "bgr"


def test_failures(rig):
    r = rig.call("set_track_color_verified", index=3, rgb=[1, 2, 3], like_index=1, like_rgb=[76, 175, 80])  # reference colour is the default 0
    assert r.error.code == "E_NOT_VERIFIED"
    assert rig.call("set_track_color_verified", index=3, rgb=[1, 2], like_index=1, like_rgb=[1, 2, 3]).error.code == "E_ARG"

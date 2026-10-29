import copy

from coproducer import projorg
from coproducer.testflp import project, with_organization


def _open(rig, tmp_path, names):
    """A saved organized project, and a fake FL whose inserts carry the given names (and enough of them)."""
    f = with_organization(project({0: "Kick", 1: "Snare", 2: "Reese Bass", 3: "Chop Hook", 4: "FX Bed"}, {0: [0]}), inserts=6)
    for c in range(5):
        f.set_track(c, c + 1)
    projorg.apply(f, projorg.plan(f))
    path = tmp_path / "org.flp"
    f.save(str(path))
    base = rig.fake.mixer[1]
    while len(rig.fake.mixer) < 10:
        rig.fake.mixer.append({**copy.deepcopy(base), "name": "Insert %d" % len(rig.fake.mixer)})
    for i, n in enumerate(names, start=1):
        rig.fake.mixer[i]["name"] = n
    return str(path)


def test_builds_family_buses(rig, tmp_path):
    path = _open(rig, tmp_path, ["Kick", "Snare", "Reese Bass", "Chop Hook", "FX Bed"])
    rig.fake.mixer[1]["color"] = 0x50AF4C  # FL reports the drum green (76, 175, 80) as blue, green, red
    r = rig.call("build_family_buses", project=path)
    assert r.ok and r.meta["verified"] is True
    assert [(b["family"], b["bus"], b["name"]) for b in r.value["buses"]] == [("drums", 6, "Drums Bus"), ("vocals", 7, "Vocals Bus"), ("fx", 8, "FX Bus")]
    m = rig.fake.mixer
    assert m[6]["color"] == (59 << 16) | (235 << 8) | 255  # yellow (255, 235, 59) in the same order
    assert set(m[1]["routes"]) == {6} and set(m[2]["routes"]) == {6} and set(m[4]["routes"]) == {7} and set(m[5]["routes"]) == {8}
    assert m[6]["routes"] == {0: 0.8} and m[3]["routes"] == {0: 0.8}  # buses reach the master, bass is left alone
    assert rig.call("build_family_buses", project=path).ok  # idempotent: same inserts, same result


def test_failures(rig, tmp_path):
    path = _open(rig, tmp_path, ["Kick", "Snare", "Reese Bass", "Wrong", "FX Bed"])
    assert rig.call("build_family_buses", project=path).error.code == "E_ARG"  # a different project is open
    path = _open(rig, tmp_path, ["Kick", "Snare", "Reese Bass", "Chop Hook", "FX Bed"])
    rig.fake.mixer[1]["color"] = 0x50AF4C
    rig.fake.mixer[6]["name"] = "My reverb"
    assert rig.call("build_family_buses", project=path).error.code == "E_ARG"  # the insert is taken
    assert rig.call("build_family_buses", project=path, families=["tuba"]).error.code == "E_ARG"
    assert rig.call("build_family_buses", project=str(tmp_path / "no.flp")).error.code == "E_IO"


def test_takes_the_colour_order_from_an_insert_that_shows_its_colour(rig, tmp_path):
    path = _open(rig, tmp_path, ["Kick", "Snare", "Reese Bass", "Chop Hook", "FX Bed"])
    rig.fake.mixer[1]["color"] = (0xFF000000 | 0x636C71) - (1 << 32)  # kick still shows the default grey
    rig.fake.mixer[4]["color"] = (33 << 16) | (150 << 8) | 243 | 0  # the vocal insert shows blue in red, green, blue order
    r = rig.call("build_family_buses", project=path)
    assert r.ok and rig.fake.mixer[6]["color"] == (255 << 16) | (235 << 8) | 59

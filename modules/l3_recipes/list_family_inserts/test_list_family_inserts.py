from coproducer import projorg
from coproducer.testflp import project, with_organization


def _saved(tmp_path):
    f = with_organization(project({0: "Kick", 1: "Snare", 2: "Reese Bass", 3: "Chop Hook", 4: "FX Bed"}, {0: [0]}), inserts=6)
    for c in range(5):
        f.set_track(c, c + 1)
    projorg.apply(f, projorg.plan(f))
    path = tmp_path / "org.flp"
    f.save(str(path))
    return str(path)


def test_lists_by_family(rig, tmp_path):
    r = rig.call("list_family_inserts", project=_saved(tmp_path), families=["drums", "vocals", "fx"])
    assert r.ok and [(i["track"], i["name"], i["family"]) for i in r.value["inserts"]] == [(1, "Kick", "drums"), (2, "Snare", "drums"), (4, "Chop Hook", "vocals"), (5, "FX Bed", "fx")]
    assert r.value["first_free"] == 6 and r.value["bus_names"]["fx"] == "FX Bus" and r.value["inserts"][0]["rgb"] == [76, 175, 80]


def test_failures(rig, tmp_path):
    path = _saved(tmp_path)
    assert rig.call("list_family_inserts", project=path, families=["tuba"]).error.code == "E_ARG"
    assert rig.call("list_family_inserts", project=str(tmp_path / "no.flp")).error.code == "E_IO"
    assert rig.call("list_family_inserts", project="").error.code == "E_ARG"

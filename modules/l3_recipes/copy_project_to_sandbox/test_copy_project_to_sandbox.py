from coproducer.services import set_service


def test_copies_and_hashes(rig, tmp_path):
    box = tmp_path / "box"
    box.mkdir()
    set_service("sandbox_root", str(box))
    orig = tmp_path / "songs" / "track.flp"
    orig.parent.mkdir()
    orig.write_bytes(b"FLhd" * 100)
    (orig.parent / "sample.wav").write_bytes(b"x" * 10)
    r = rig.call("copy_project_to_sandbox", source=str(orig), project="track_a")
    assert r.ok and r.meta["verified"] and r.value["original_hash"] == r.value["copy_hash"]
    assert (box / "track_a" / "track.flp").read_bytes() == orig.read_bytes() and not (box / "track_a" / "sample.wav").exists()
    again = rig.call("copy_project_to_sandbox", source=str(orig), project="track_b", include_folder=True)
    assert again.ok and (box / "track_b" / "sample.wav").exists()
    assert orig.read_bytes() == b"FLhd" * 100


def test_rejects_bad_sources(rig, tmp_path):
    assert rig.call("copy_project_to_sandbox", source=str(tmp_path / "no.flp"), project="p").error.code == "E_NOT_FOUND"
    box = tmp_path / "box"
    box.mkdir()
    set_service("sandbox_root", str(box))
    inside = box / "p" / "a.flp"
    inside.parent.mkdir()
    inside.write_bytes(b"x")
    assert rig.call("copy_project_to_sandbox", source=str(inside), project="p").error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("copy_project_to_sandbox", source=str(inside), project="../escape").error.code == "E_ARG"
    big = tmp_path / "big" / "a.flp"
    big.parent.mkdir()
    big.write_bytes(b"x" * 2_000_000)
    assert rig.call("copy_project_to_sandbox", source=str(big), project="q", include_folder=True, max_mb=1).error.code == "E_ARG"

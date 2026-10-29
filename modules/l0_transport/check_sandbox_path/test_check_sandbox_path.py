def test_inside_ok(fn, tmp_path):
    root = tmp_path / "sb"
    (root / "p").mkdir(parents=True)
    r = fn("check_sandbox_path")(str(root / "p" / "x.flp"), str(root))
    assert r.ok


def test_outside_and_traversal_refused(fn, tmp_path):
    f = fn("check_sandbox_path")
    root = tmp_path / "sb"
    root.mkdir()
    assert f(str(tmp_path / "real.flp"), str(root)).error.code == "E_SANDBOX_VIOLATION"
    assert f(str(root / ".." / "real.flp"), str(root)).error.code == "E_SANDBOX_VIOLATION"
    assert f("", str(root)).error.code == "E_ARG"

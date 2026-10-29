from coproducer.services import clear_services, set_service


def test_reads_nested_key(fn):
    set_service("config", {"sandbox": {"root": "sbx", "n": 3}})
    f = fn("get_config_value")
    assert f("sandbox.root").value == "sbx" and f("sandbox").value == {"root": "sbx", "n": 3}


def test_missing_key_and_config(fn):
    f = fn("get_config_value")
    assert f("a").error.code == "E_NOT_FOUND"
    set_service("config", {"a": {"b": 1}})
    assert f("a.c").error.code == "E_NOT_FOUND" and f("a.b.c").error.code == "E_NOT_FOUND"
    clear_services()

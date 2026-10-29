from coproducer.services import set_service


def test_returns_recorded_values(rig):
    set_service("config", {"probe": {"fl_version": "2026.1.7", "api_level": 45}})
    assert rig.call("get_fl_versions").value == {"fl": "2026.1.7", "api": 45}


def test_not_recorded(rig):
    set_service("config", {})
    assert rig.call("get_fl_versions").error.code == "E_NOT_FOUND"

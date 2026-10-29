from coproducer.services import clear_services


def test_halts_everything(rig, desk):
    assert rig.call("halt_input").value == {"halted": True} and desk.halt.flag
    assert rig.call("click_at", x=1, y=1).error.code == "E_HALTED"


def test_without_flag(rig):
    clear_services()
    assert rig.call("halt_input").error.code == "E_UNSUPPORTED_API"

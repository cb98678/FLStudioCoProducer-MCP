def test_types_text(rig, desk):
    assert rig.call("type_text", text="Serum 2").value == {"typed": 7}
    assert ("type", "Serum 2") in desk.fake.log


def test_refuses_control_characters(rig, desk):
    assert rig.call("type_text", text="a\nb").error.code == "E_ARG" and rig.call("type_text", text="a\x1bb").error.code == "E_ARG"
    assert not [e for e in desk.fake.log if e[0] == "type"]
    desk.halt.flag = True
    assert rig.call("type_text", text="ok").error.code == "E_HALTED"

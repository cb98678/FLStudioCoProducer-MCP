from coproducer.services import set_service


class _Backend:
    def __init__(self, ins, outs):
        self._i, self._o = ins, outs

    def get_input_names(self):
        return self._i

    def get_output_names(self):
        return self._o


def test_finds_ports_with_index_suffix(fn):
    set_service("midi_backend", _Backend(["Other 0", "coproducer-out 2"], ["coproducer-in 1", "Other 1"]))
    r = fn("find_midi_ports")()
    assert r.ok and r.value["host_out"] == "coproducer-in 1" and r.value["host_in"] == "coproducer-out 2"


def test_reports_missing_port(fn):
    set_service("midi_backend", _Backend(["x"], ["coproducer-in"]))
    r = fn("find_midi_ports")()
    assert r.error.code == "E_NOT_FOUND"

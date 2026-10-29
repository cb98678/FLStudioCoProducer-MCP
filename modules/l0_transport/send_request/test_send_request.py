from coproducer.services import set_service


class _T:
    def __init__(self, boom=False):
        self.sent, self.boom = [], boom

    def send(self, b):
        if self.boom:
            raise OSError("port closed")
        self.sent.append(b)


def test_sends_in_order(fn):
    t = _T()
    set_service("transport", t)
    r = fn("send_request")([[1, 2], [3]])
    assert r.value == {"sent": 2} and t.sent == [b"\x01\x02", b"\x03"]


def test_no_transport_and_send_error(fn):
    f = fn("send_request")
    assert f([[1]]).error.code == "E_UNSUPPORTED_API"
    set_service("transport", _T(boom=True))
    assert f([[1]]).error.code == "E_IO"

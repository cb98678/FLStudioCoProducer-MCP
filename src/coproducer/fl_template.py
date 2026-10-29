"""Handler half of the generated FL-side dispatcher (inlined after the L0 and L1 sources).

It is small on purpose: receive SysEx frames, reassemble requests, run one op per idle tick,
send the reply. No music logic, no retries, no policy. Python 3.9 compatible.
Names such as parse_frame and OPS come from the sources that the generator inlines above this text.
"""

PROTOCOL_VERSION = 1
MAX_PAYLOAD = 200
MSG_REQUEST, MSG_REPLY, MSG_ERROR, MSG_PING, MSG_PONG = 1, 2, 3, 4, 5
PREFIX = [0x7D, 0x43, 0x50]
MAX_PARTIAL = 8

_partial = {}
_queue = []
_stats = {"frames": 0, "ignored": 0, "requests": 0, "errors": 0}


def _info():
    out = {"proto": PROTOCOL_VERSION, "max_payload": MAX_PAYLOAD, "queue": len(_queue), "stats": dict(_stats)}
    for key, fn in (("api", lambda: general.getVersion()), ("fl", lambda: ui.getVersion()),
                    ("project", lambda: ui.getProgTitle())):
        try:
            out[key] = fn()
        except Exception as e:  # noqa: BLE001
            out[key] = "unavailable: %s" % type(e).__name__
    return out


def _send(msg_type, req_id, name, data):
    body = encode_body(name, data)
    if not body.ok:
        body = encode_body(name, {"ok": False, "value": None,
                                  "error": {"code": "E_INTERNAL", "message": "reply not encodable"}})
    packed = encode_sysex(body.value).value
    chunks = split_frames(packed, MAX_PAYLOAD).value or [[]]
    for i, chunk in enumerate(chunks):
        frame = build_frame(PROTOCOL_VERSION, msg_type, req_id, i, len(chunks), chunk)
        if frame.ok:
            _debug("sysex out, %d bytes" % len(frame.value))
            device.midiOutSysex(bytes(frame.value))


def _error(req_id, name, code, message):
    _stats["errors"] += 1
    _send(MSG_ERROR, req_id, name or "error", {"ok": False, "value": None, "error": {"code": code, "message": message}})


def _builtin_echo(text: str = "") -> dict:
    return {"ok": True, "value": text, "error": None}


def _builtin_config(max_payload: int = 0) -> dict:
    global MAX_PAYLOAD
    if type(max_payload) is int and 8 <= max_payload <= 4000:
        MAX_PAYLOAD = max_payload
    return {"ok": True, "value": MAX_PAYLOAD, "error": None}


def _builtin_info() -> dict:
    return {"ok": True, "value": _info(), "error": None}


def _builtin_probe(name: str = "", mutating: bool = False, args=None) -> dict:
    """Run one probe from fl_probes by name; an empty name lists them. Mutating probes need mutating=True."""
    table = dict(PROBE_TABLE)
    if mutating:
        table.update(MUTATING_PROBES)
    if name == "":
        return {"ok": True, "value": sorted(table), "error": None}
    fn = table.get(name)
    if fn is None:
        return {"ok": False, "value": None, "error": {"code": "E_NOT_FOUND", "message": "no probe " + name}}
    try:
        return {"ok": True, "value": fn(**(args or {})), "error": None}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "value": None, "error": {"code": "E_INTERNAL", "message": "%s: %s" % (type(e).__name__, e)}}


def _run_request(req_id, parts):
    joined = [b for i in range(len(parts)) for b in parts[i]]
    raw = decode_sysex(joined)
    msg = decode_body(raw.value) if raw.ok else raw
    if not msg.ok:
        return _error(req_id, "", "E_ARG", "undecodable request")
    name, args = msg.value["name"], msg.value["data"]
    fn = OPS.get(name)
    if fn is None:
        return _error(req_id, name, "E_NOT_FOUND", "unknown op " + name)
    try:
        res = fn(**args)
    except TypeError as e:
        return _error(req_id, name, "E_ARG", "bad arguments: %s" % e)
    except Exception as e:  # noqa: BLE001
        return _error(req_id, name, "E_INTERNAL", "%s: %s" % (type(e).__name__, e))
    _stats["requests"] += 1
    _send(MSG_REPLY, req_id, name, res)


def _take(frame):
    if frame["type"] == MSG_PING:
        return _send(MSG_PONG, frame["req_id"], "pong", _info())
    if frame["type"] != MSG_REQUEST:
        return None
    slot = _partial.setdefault(frame["req_id"], {"total": frame["total"], "parts": {}})
    slot["parts"][frame["seq"]] = frame["payload"]
    while len(_partial) > MAX_PARTIAL:
        _partial.pop(next(iter(_partial)))
    if len(slot["parts"]) == slot["total"]:
        del _partial[frame["req_id"]]
        _queue.append((frame["req_id"], slot["parts"]))


_DEBUG_LEFT = [12]


def _debug(text):
    """Print the first few events so a missing reply can be traced in View > Script output."""
    if _DEBUG_LEFT[0] > 0:
        _DEBUG_LEFT[0] -= 1
        print("Coproducer:", text)


def OnSysEx(event):
    data = list(event.sysex)
    _debug("sysex in, %d bytes, starts %s, ours=%s" % (len(data), data[:6], data[1:4] == PREFIX))
    if data[1:4] != PREFIX:
        _stats["ignored"] += 1
        return
    event.handled = True
    _stats["frames"] += 1
    parsed = parse_frame(data)
    if parsed.ok:
        _take(parsed.value)
    else:
        _stats["errors"] += 1


def OnIdle():
    if _queue:
        req_id, parts = _queue.pop(0)
        _run_request(req_id, parts)


def OnInit():
    print("Coproducer bridge ready, protocol", PROTOCOL_VERSION)
    try:
        print("Coproducer: port number %s, assigned %s" % (device.getPortNumber(), device.isAssigned()))
    except Exception as e:  # noqa: BLE001
        print("Coproducer: port info unavailable:", type(e).__name__)


def OnDeInit():
    print("Coproducer bridge stopped")

from __future__ import annotations

from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def find_midi_ports(prefix: str = "coproducer") -> Result:
    """Find the virtual MIDI ports for the bridge: send to '<prefix>-in', listen on '<prefix>-out'.

    Port names are matched by prefix because loopMIDI appends an index. Errors: E_UNSUPPORTED_API without a
    MIDI backend, E_NOT_FOUND when a port is missing.
    """
    backend = get_service("midi_backend")
    if backend is None:
        try:
            import mido
            backend = mido
        except ImportError:
            return fail("E_UNSUPPORTED_API", "install mido and python-rtmidi to use MIDI ports")
    try:
        outs, ins = list(backend.get_output_names()), list(backend.get_input_names())
    except Exception as e:  # noqa: BLE001
        return fail("E_UNSUPPORTED_API", f"MIDI backend failed: {e}")
    send_to = [n for n in outs if n.lower().startswith(prefix.lower() + "-in")]
    listen_on = [n for n in ins if n.lower().startswith(prefix.lower() + "-out")]
    if not send_to or not listen_on:
        return fail("E_NOT_FOUND", f"need ports '{prefix}-in' and '{prefix}-out'", outputs=outs, inputs=ins)
    return ok({"host_out": send_to[0], "host_in": listen_on[0], "all_outputs": outs, "all_inputs": ins})

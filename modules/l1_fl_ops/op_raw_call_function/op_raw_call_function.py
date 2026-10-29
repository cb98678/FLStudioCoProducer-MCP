import arrangement
import channels
import device
import general
import mixer
import patterns
import playlist
import plugins
import transport
import ui


def op_raw_call_function(module: str, function: str, args: list) -> dict:
    """Call one allowlisted FL function by name, for functions newer than the generated ops."""
    bad = _check_args({"module": module, "function": function}, {"module": "s", "function": "s"})
    if bad:
        return bad
    return _raw(globals(), module, function, args)

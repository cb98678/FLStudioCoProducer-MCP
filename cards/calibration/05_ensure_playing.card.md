### Card 05. `ensure_playing` (L2, writes FL in sandbox)

1. **Goal.** Make the transport play if it is not already playing, and confirm.
2. **Signature.** `def ensure_playing(timeout_s: float = 2.0) -> Result`
3. **I/O.** `value`: `{"was_playing": bool, "is_playing": bool}`. Errors: `E_ARG` (timeout not positive); `E_NOT_VERIFIED` (still not playing at the timeout); underlying errors pass through.
4. **Sources.** The [transport reference](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/transport/): `transport.start` toggles play and pause, so the function MUST check state before it calls start (file 02, FX-14).
5. **Imports and class.** `writes_fl_sandbox`. Allowed: `time`. Calls `op_transport_is_playing` and `op_transport_start`.
6. **Budget.** 30 lines, nesting 3, 1 parameter.
7. **Acceptance tests (fake FL).**
   - Stopped: result ok, `was_playing` false, `is_playing` true, exactly one start call, `meta.verified` true.
   - Already playing: ok, zero start calls, `meta.verified` true.
   - Fake ignores start: failure `E_NOT_VERIFIED` after at most `timeout_s` plus 0.1 seconds, with `timeout_s=0.05` in the test.
   - `timeout_s=0` returns `E_ARG`.
8. **Out of scope.** Stopping, looping, tempo, waiting for the song to end.

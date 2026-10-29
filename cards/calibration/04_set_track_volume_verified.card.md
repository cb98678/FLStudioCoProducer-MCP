### Card 04. `set_track_volume_verified` (L2, writes FL in sandbox)

1. **Goal.** Set a mixer track's volume and confirm it took effect.
2. **Signature.** `def set_track_volume_verified(track: int, value: float, tol: float = 0.001) -> Result`
3. **I/O.** `value` of the result: `{"before": float, "after": float, "changed": bool}`. Errors: `E_ARG` (value outside 0 to 1, tol not positive, track invalid); `E_NOT_VERIFIED` (readback differs from the request by more than `tol`); any error from the underlying ops passes through.
4. **Sources.** Behavior of `mixer.setTrackVolume` and `mixer.getTrackVolume` in the [mixer tracks reference](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/mixer/tracks/). Prior art note: FL can silently ignore a scripted write (file 02, FX-17), which is why the readback exists.
5. **Imports and class.** `writes_fl_sandbox`. Calls only `op_mixer_get_track_volume` and `op_mixer_set_track_volume` through `registry.call`.
6. **Budget.** 35 lines, nesting 3, 3 parameters.
7. **Acceptance tests (fake FL).**
   - Track at 0.5, request 0.8: result ok, `before` 0.5, `after` 0.8, `changed` true, `meta.verified` true, exactly one set call.
   - Track already at 0.8, request 0.8: ok, `changed` false, `meta.verified` true, zero set calls (idempotent).
   - Fake configured to ignore writes: result is a failure with code `E_NOT_VERIFIED`, `meta.verified` false, and `value` still carries `before` and `after`.
   - `value=1.2` returns `E_ARG` and makes no calls.
   - The underlying get fails with `E_TIMEOUT`: the result is that failure, `meta.verified` false.
8. **Out of scope.** Converting dB, retrying a write, snapshotting, touching other tracks.

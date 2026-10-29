### Card 03. `op_mixer_get_track_volume` (L1, inside FL)

1. **Goal.** Return a mixer track's volume as a float from 0 to 1.
2. **Signature.** `def op_mixer_get_track_volume(track: int) -> dict`. Returns `{"ok": bool, "value": float | None, "error": str | None}`. L1 ops return plain dicts because they run inside FL; the host converts them to `Result`.
3. **I/O.** Input: `track`, integer from 0 up to the track count. Output `value`: the volume. Errors: `"E_ARG"` when the index is negative, not an integer, or not less than the track count.
4. **Sources.** `mixer.getTrackVolume` and `mixer.trackCount` in the [mixer tracks reference](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/mixer/tracks/). The agent MUST use the signatures as written there and the argument check MUST come before the call.
5. **Imports and class.** `reads_fl`, FL-side rule set: `import mixer` only.
6. **Budget.** 15 lines, nesting 2, 1 parameter.
7. **Acceptance tests (fake FL, 3 tracks, volumes 0.8, 0.5, 1.0).**
   - `track=0` returns ok and `0.8`.
   - `track=2` returns ok and `1.0`.
   - `track=3` returns `E_ARG`. `track=-1` returns `E_ARG`. `track=1.5` returns `E_ARG`. `track=True` returns `E_ARG`.
   - The function never calls any setter (assert via the fake's call log).
8. **Out of scope.** Converting to dB, caching, retries, writing.

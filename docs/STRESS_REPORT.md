# Stress and fragility report (Gate 0 hardening)

Run on 2026-10-21 against FL Studio 2026 Producer Edition v26.1.7 (build 5654, API 45) on the Windows 11 machine, plus the cloud workspace for the fake-FL runs.
Everything here can be repeated; the commands are at the end.

## What was tested

| Layer | What it does | Where it ran |
| --- | --- | --- |
| Module tests | Each of the 269 modules has its own test file (golden case and failure case) | cloud and Windows |
| Contract fuzz | Every module is called with hostile arguments built from its own input schema: boundary and extreme numbers, NaN and infinity, empty and 50,000 character text, NUL bytes, lone surrogates, path tricks, Windows device names, deep nesting, wrong types, missing and unknown arguments, and 25 random mixes per module | cloud (Linux) and Windows |
| Live bridge stress | Read-only abuse of the real MIDI bridge into FL: latency, soak, bad arguments straight to FL, oversize payloads, hostile operation names, id wraparound, unread replies, 8 concurrent callers, garbage on the wire, reconnects | your machine, real FL |
| Desktop weirdness | FL minimized, another program in front, focus thrash, screenshot while minimized | your machine, real FL |

A call counts as a **defect** when it raises past the registry, hangs, comes back as `E_INTERNAL`, returns an error code that is not in the list, accepts a wrong-typed argument, or writes a file outside the sandbox.
It counts as **fragile** when the result is not strict JSON, is over 1 MB, or takes over 3 seconds.

## Results

| Run | Result |
| --- | --- |
| Test suite, cloud | 800 passed |
| Test suite, Windows | 799 passed, 1 skipped (the Python 3.9 check, which needs 3.9) |
| Contract fuzz, cloud | 269 modules, 22,422 calls: 117 defects on the first pass, 0 after fixes |
| Contract fuzz, Windows | 269 modules, 22,422 calls: 0 defects, 20 fragile (all deliberate waits, below) |
| Live bridge stress | 10 scenarios. 9 pass on every run. Concurrent callers passed on 3 of 5 repeats; on the other 2 one read in 320 timed out after FL went quiet for about 6 s (see "Fragile") |
| Desktop weirdness | 7 of 7 pass |

Raw reports: `docs/reports/fuzz_cloud_2026-10-21.json`, `docs/reports/fuzz_windows_2026-10-21.json`.

### Live bridge numbers (real FL, MIDI over loopMIDI)

| Scenario | Result |
| --- | --- |
| Ping latency | 300 pings, 0 failed, median 40.4 ms, p95 46.5 ms, max 52.4 ms |
| Read soak | 600 reads in 29 s, 0 timeouts or internal errors, none slower than 1 s |
| Bad arguments sent straight to FL | 351 calls with indexes such as -1, 2^31, 2^64, NaN, text, lists, objects: every one answered, none unanswered |
| Payload sizes | 0 to 20,000 junk characters (the bridge splits frames at 200 bytes): all answered |
| Hostile operation names | 96 calls (empty, `__import__`, `../etc/passwd`, 3,000 character names, text with NUL): refused, nothing executed |
| Request id wraparound | 12 pings across the 14 bit id wrap: 0 failed |
| Unread replies | 40 replies left unread, next calls still got their own answers |
| Concurrent callers | 8 threads x 40 calls: 0 wrong answers, 0 errors |
| Garbage on the wire | 89 junk messages (foreign sysex, truncated frames, bad checksum, wrong version, unknown types, zero and oversize totals, incomplete multi-frame groups, unterminated sysex, a start byte inside sysex, 60 random messages): bridge never went deaf |
| Reconnect loop | 12 open and close cycles of the MIDI ports: 0 failed |

FL's own counters after the abuse showed 2,179 frames, 65 ignored (the junk) and 585 error replies (the bad requests), and it kept answering.

## Defects found and fixed

| # | Found by | Root cause | Fix | Pinned by |
| --- | --- | --- | --- | --- |
| 1 | fuzz | `wait_for_reply` accepted any timeout, so one call could wait forever | `timeout_s` capped at 60 s | `test_wait_for_reply_cannot_be_asked_to_wait_forever` |
| 2 | fuzz | NaN and infinity pass JSON Schema number bounds and then break maths, waits and JSON output | the registry refuses them in any argument | `test_registry_refuses_nan_infinity_nul_and_lone_surrogates_in_any_argument` |
| 3 | fuzz | NUL bytes and lone surrogates in text crashed every file call with `ValueError` or `UnicodeEncodeError` | refused at the registry as `E_ARG` | same test, plus nested case |
| 4 | fuzz | JSON Schema accepts `3.0` as an integer, then `range()` and indexing raised `TypeError` (list modules) | whole floats are turned into ints where the schema says integer | `test_a_whole_float_is_accepted_for_an_integer_argument` |
| 5 | fuzz | file calls that were not guarded (name too long, locked, vanished) raised `OSError` and came back as `E_INTERNAL` | the registry answers `E_IO` | `test_an_unguarded_os_error_becomes_e_io_not_a_crash` |
| 6 | fuzz | three TOML loaders crashed on a file that is not UTF-8 text | any `ValueError` is `E_IO` | `test_toml_loaders_survive_a_file_that_is_not_text` |
| 7 | fuzz | FL answers an out-of-range value with `RuntimeError("Range error")`, which the FL-side dispatcher reported as `E_INTERNAL` (68 cases in tempo and pattern length) | reported as `E_ARG` (the FL-side script must be reinstalled to pick this up) | `test_fl_range_errors_are_argument_errors` |
| 8 | fuzz | `render_via_cli` returned `E_RENDER_FAILED`, a code that does not exist | uses `E_IO` | its module test |
| 9 | fuzz | `restore_solo_group` and `set_rough_balance` ran `int()` on any key | schema now requires numeric keys, boolean states and at most 500 entries | `test_index_maps_refuse_keys_and_values_that_are_not_indexes` |
| 10 | fuzz | `build_bus` took any number of tracks (14 s for 1,000) | at most 126 tracks | schema |
| 11 | fuzz | `read_audio_file` with `max_seconds` 1e308 overflowed | capped at 86,400 s | `test_read_audio_file_cannot_be_asked_for_an_absurd_length` |
| 12 | Windows fuzz | a path argument of `CON` (or `NUL`, `AUX`, `PRN`, `COM1` to `COM9`, `LPT1` to `LPT9`, with or without an extension) made Windows read the console and block forever, and it then froze every later call in that process | path-like arguments that are device names are refused on every machine. Microsoft documents the reserved names and that `NUL.txt` equals `NUL` ([Naming Files, Paths, and Namespaces](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file), updated 2024-08-28) | `test_windows_device_names_and_network_paths_are_refused_in_path_arguments` |
| 13 | Windows fuzz | paths that start with two slashes (`\\server\share`, `\\?\`, `\\.\`) and colons outside a drive letter reach the network or a device and can block on a name lookup | refused with the same guard | same test |
| 14 | review | the guard missed arguments named `path_a` and `path_b`, and arguments that become file names (recipe name, script name, template name, project source) | name match widened, and a schema marker `"x-path": true` covers the rest. A test lists any future file-like argument that is not guarded | `test_every_string_argument_that_names_a_file_is_guarded` |
| 15 | review | `BridgeClient` shared one transport and one id counter between threads | one request on the wire at a time (a lock) | `test_bridge_client_is_safe_from_many_threads` |

Tooling fixes made on the way: the fuzz runner now exits with a message when no module finishes for 200 seconds (a hung job had blocked the Windows job queue for hours), and the live stress test falls back to the raw MIDI driver when the `mido` library refuses to send a malformed message on purpose.

## Fragile, known and accepted

- **Deliberate waits.** 20 fuzz calls took over 3 seconds: `wait_for_change` waits for its default 5 s, and `generate_audio` with 600 s of audio takes about 5 s on the fake runner. Nothing hung.
- **Timeouts are bounded, not short.** Reads retry twice on timeout (about 6 s worst case); writes never retry.
- **Rare lost answers from FL.** Across about 25,000 steady pings and 5 repeats of the 8-thread test, three odd events appeared and could not be reproduced on demand: two pings failed fast (about 40 ms, in the same run) and, in 2 of 5 concurrency runs, one read timed out after FL went quiet for about 6 s (three tries of 2 s). The other 14,400 pings in four later 150 second runs were all clean, with none slower than 300 ms. Cause not found; FL freezing its script thread (autosave, a dialog) is the leading guess, not a measurement. The system is built for it: reads retry twice, writes never retry, and every `*_verified` write reads the value back, so a lost reply shows up as a timeout and not as a silent wrong state. `coproducer probe stress --only stalls` repeats the measurement and now records the error text of any failure.
- **One request at a time.** The bridge is a single wire. Concurrent callers are safe but queue up; the MCP server already serialises tool calls.
- **FL-side fix needs a reinstall.** Defect 7 lives in the script FL loads. Run `coproducer setup` and reload the script in FL's MIDI settings to pick it up. Until then FL's range errors are still reported as `E_INTERNAL` (harmless, only the wrong code).

## Not tested, and why

- Non-sysex MIDI (notes, controllers) into the bridge port: could play or record sounds in the open project.
- FL closed, crashed or frozen in the middle of a call. Recovery after a deliberate FL restart is exercised by `render_with_restart` (bridge back in a few seconds, measured), but a crash was not provoked on your machine.
- A locked screen, UAC prompts and elevated windows (Windows blocks input to them by design).
- Multi-monitor and DPI changes while a recipe runs.
- Real model failures (out of memory, corrupt weights). The scheduler and workers were tested with a fake runner; the real stacks were verified at install time.
- Runs of hours. The longest live run here was about 2 minutes of continuous traffic.

## Repeat it

```
python tools/fuzz_all.py --out fuzz.json                      # all modules on the fake FL, about 8 to 11 minutes
python -m pytest -q                                           # tests; COPRODUCER_FUZZ=full also fuzzes every module inside pytest
coproducer probe stress                                       # live bridge, read-only (FL open, Coproducer script selected)
coproducer probe stress --only desktop                        # briefly minimizes FL and opens Notepad; restores both
```

## Final numbers

| Check | Result |
| --- | --- |
| Modules | 269, each with its own test file |
| Tests, cloud (Linux, Python 3.13) | 800 passed |
| Tests, Windows (Python 3.11.3, venv) | 799 passed, 1 skipped |
| Lint | clean on both |
| Fuzz, cloud | 22,422 calls, 0 defects, 20 slow (deliberate waits) |
| Fuzz, Windows | 22,422 calls, 0 defects, 20 slow (deliberate waits) |
| Dependency check on the Windows machine | all four model environments match `cli/stacks.py`; no host drift reported |
| Live bridge, final run | 9 of 10 scenarios pass; concurrent callers had 1 timeout in 320 reads that run |
| Desktop weirdness, final run | 7 of 7 pass |

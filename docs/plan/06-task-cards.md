# 06. Task Cards and the Local-Agent Build Loop

A task card is the unit of work for a small local coding model. It is one page that holds everything the model needs, so it never has to guess, never has to browse the repository, and never sees the whole system.

## 1. The card template

Every card has these eight fields. A card missing any field is rejected before it reaches an agent.

| # | Field | Content |
| --- | --- | --- |
| 1 | Goal | One sentence. One job. |
| 2 | Signature | Exact function name, typed parameters, return type |
| 3 | I/O schema | Input and output JSON Schema, plus the error codes it may return |
| 4 | Official sources | The exact manual or reference entries for any FL API call used, with links. For model adapters, the pinned repository commit and README section |
| 5 | Allowed imports and side-effect class | From file 04, section 4. Anything else is a lint failure |
| 6 | Size budget | Line, nesting, and parameter limits |
| 7 | Acceptance tests | Given and expected pairs, including at least one failure case. These become the module's test file |
| 8 | Out of scope | What the module must not do. This is the most useful field for keeping small models on task |

Cards are plain files at `cards/<layer>/<module>.card.md`. A script validates that all eight fields exist and that the card's tests parse.

## 2. The prompt given to the local coding agent

The agent receives a fixed system prompt and one card. It receives nothing else.

```
You write exactly one Python module for a larger system. Follow the card.

Output exactly three files in this order, each in a fenced block labeled with its path:
1. <name>.py       the module. One public function, named as in the card.
2. module.toml     the manifest, filled in from the card.
3. test_<name>.py  pytest tests that implement every acceptance test in the card.

Rules:
- Return a Result using ok(...) or fail(code, message). Never raise.
- Import only what the card allows. Call other modules only with registry.call("name", ...).
- Stay inside the size budget. If you cannot, say so and stop.
- Do not add features the card lists as out of scope.
- Do not write prose outside the three files.
```

On a failed gate, the retry prompt is the original card plus the previous output plus the gate report verbatim, with one line: "Fix only what the report lists."

## 3. The build loop

```
card -> local agent -> three files -> GATE -> registry + generated docs
                          ^              |
                          |   fail       |
                          +--(report)----+   up to N tries, then escalate
```

1. **Queue.** Cards are ordered by layer so lower layers exist before higher ones call them.
2. **Isolation.** Each card is built in its own working branch or directory, so a bad attempt never touches registered modules.
3. **Gate.** One command runs: the linter (file 04, section 5), the module's tests against the fake FL harness or synthetic audio, and the size check. Pass or fail, with a machine-readable report.
4. **Retry.** Up to 3 attempts with the report fed back. Attempts and tokens are recorded.
5. **Escalate.** After 3 failures, the card goes to a stronger model or to you. The failure is recorded with the card as a data point on card quality, because repeated failures usually mean the card is ambiguous.
6. **Register.** A passing module is added to the registry. Catalog docs and the skills references regenerate.
7. **Never auto-merge cards that touch the bridge protocol** (L0) or the sandbox checks. These get a human review of the diff.

## 4. The calibration set

Before any local model is trusted with real cards, ten cards spanning the layers are run against each candidate model. The ten cards are written out in full in section 6.

| Measure | Definition | Starting threshold to adopt a model |
| --- | --- | --- |
| pass@1 | Cards whose first attempt passes the gate | At least 6 of 10 |
| pass@3 | Cards that pass within 3 attempts | At least 9 of 10 |
| Retry efficiency | Mean attempts on passing cards | At most 1.6 |
| Cost | Median output tokens and wall time per card | Used as a tiebreak |
| Scope discipline | Cards where the output added nothing from "out of scope" | 10 of 10 |

The thresholds are starting values. Gate 0 records the real distribution and may adjust them. The winner is the model with the best pass@1 among those that meet the thresholds, with cost as the tiebreak. A stronger model MAY be configured for escalations only.

## 5. Card authoring checklist

1. Could a person who has never seen the repository write this from the card alone? If not, add to the card.
2. Does every number in a test come from a derivation the card states (not a guess)?
3. Is there at least one failure case per error code the card lists?
4. Does "out of scope" name the two most likely overreaches?
5. Is each official-source entry a link to a specific page, not a site?
6. Is the function small enough that the size budget is realistic with margin?

## 6. The ten calibration cards

### Card 01. `encode_sysex` (L0, pure)

1. **Goal.** Pack a list of bytes into 7-bit form so it can travel in a SysEx message.
2. **Signature.** `def encode_sysex(data: list[int]) -> Result`
3. **I/O.** Input: list of integers, each 0 to 255. Output `value`: list of integers, each 0 to 127. Errors: `E_ARG` for any element not an integer in 0 to 255.
4. **Sources.** Algorithm defined in file 03, section 4.4, item 1. No FL API used.
5. **Imports and class.** `pure`. Allowed: `typing`, and the Result helpers.
6. **Budget.** 25 lines, nesting 2, 1 parameter.
7. **Acceptance tests.**
   - `[]` returns `[]`.
   - `[0xFF]` returns `[0x01, 0x7F]`.
   - `[0x80, 0x01]` returns `[0x01, 0x00, 0x01]`.
   - Seven bytes of `0xFF` return `[0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F]`.
   - Eight bytes of `0x00` return ten bytes, all zero.
   - For every input in a set of 200 random lists, every output byte is at most 127 (property test).
   - `[256]` returns an `E_ARG` failure. `[-1]` returns `E_ARG`. `["a"]` returns `E_ARG`. `[True]` returns `E_ARG`.
8. **Out of scope.** Framing, checksums, I/O, decoding. Do not mutate the input list.

Derivation note: in each group of up to 7 input bytes, the header byte's bit `i` (value `1 << i`) is the top bit of input byte `i`. The data bytes follow with their top bit cleared. A final partial group of `n` bytes yields `n + 1` bytes.

### Card 02. `split_frames` (L0, pure)

1. **Goal.** Split a byte list into consecutive chunks of at most N bytes.
2. **Signature.** `def split_frames(data: list[int], max_len: int) -> Result`
3. **I/O.** `value`: list of lists. Errors: `E_ARG` if `max_len` is less than 1 or `data` is not a list.
4. **Sources.** File 03, section 4.2, item 4. No FL API used.
5. **Imports and class.** `pure`.
6. **Budget.** 15 lines, nesting 2, 2 parameters.
7. **Acceptance tests.**
   - `([0,1,2,3,4], 2)` returns `[[0,1],[2,3],[4]]`.
   - `([], 5)` returns `[]`.
   - `([1,2], 5)` returns `[[1,2]]`.
   - `([1,2,3,4], 4)` returns `[[1,2,3,4]]`.
   - `([1,2,3], 0)` returns `E_ARG`. `("abc", 2)` returns `E_ARG`.
   - Joining the chunks always reproduces the input (property test).
8. **Out of scope.** Headers, sequence numbers, 7-bit checks.

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

### Card 06. `measure_true_peak` (L4, reads files)

1. **Goal.** Measure the true peak of an audio file in dBTP using oversampling.
2. **Signature.** `def measure_true_peak(path: str, oversample: int = 4) -> Result`
3. **I/O.** `value`: `{"dbtp": float, "per_channel": list[float]}`. For a file that is all zeros, `dbtp` is `-120.0`. Errors: `E_IO` (missing or unreadable file); `E_ARG` (`oversample` not 2, 4, or 8; empty file).
4. **Sources.** True peak is defined in ITU-R BS.1770; this module implements the common oversampling approximation. Library docs: `soundfile.read`, `scipy.signal.resample_poly`. Gate 0 compares output with a reference meter on reference signals.
5. **Imports and class.** `reads_files`. Allowed: `numpy`, `scipy.signal`, `soundfile`, `pathlib`, `math`.
6. **Budget.** 30 lines, nesting 2, 2 parameters.
7. **Acceptance tests (synthetic audio, 48 kHz).**
   - A 997 Hz sine of amplitude 0.5, 1 second: `dbtp` is -6.02 within 0.1.
   - A 997 Hz sine of amplitude 1.0: `dbtp` is 0.0 within 0.2.
   - Inter-sample case: a sine at one quarter of the sample rate with a 45 degree phase and amplitude 1.0 has sample peak near -3.01 dBFS; `dbtp` is 0.0 within 0.2. The test also asserts that `dbtp` exceeds the sample peak by at least 2.5 dB.
   - Stereo file with a loud left and quiet right: `per_channel` has two entries and the file value equals the maximum.
   - All-zero file returns -120.0.
   - Missing path returns `E_IO`. `oversample=3` returns `E_ARG`.
8. **Out of scope.** Loudness, normalization, resampling to other rates, writing files.

### Card 07. `measure_integrated_loudness` (L4, reads files)

1. **Goal.** Measure a file's integrated loudness in LUFS per ITU-R BS.1770.
2. **Signature.** `def measure_integrated_loudness(path: str) -> Result`
3. **I/O.** `value`: `{"lufs": float, "gated_silence": bool}`. If the file is entirely below the absolute gate, `lufs` is -70.0 and `gated_silence` is true. Errors: `E_IO`; `E_ARG` when the file is shorter than 0.4 seconds.
4. **Sources.** The [pyloudnorm listing](https://pypi.org/project/pyloudnorm/0.0.1) describes a BS.1770 implementation; the agent MUST use the library's meter and MUST NOT implement the filters itself. Gate 0 verifies the library on reference signals and records the pinned version.
5. **Imports and class.** `reads_files`. Allowed: `numpy`, `soundfile`, `pyloudnorm`, `pathlib`.
6. **Budget.** 25 lines, nesting 2, 1 parameter.
7. **Acceptance tests (synthetic audio, 48 kHz, 20 seconds).**
   - A 1 kHz sine, the same in both channels, at -23 dBFS peak: `lufs` within 0.3 of -23.0.
   - The same signal 6 dB louder: `lufs` is higher by 6.0 within 0.1.
   - Silence: `lufs` -70.0, `gated_silence` true.
   - A 0.2 second file returns `E_ARG`. A missing file returns `E_IO`.
8. **Out of scope.** True peak, loudness range, normalization, writing files.

### Card 08. `compare_note_sequences` (L4, pure)

1. **Goal.** Score how similar two note lists are in rhythm and pitch, for the melody-preservation check.
2. **Signature.** `def compare_note_sequences(a: list[dict], b: list[dict], tol_beats: float = 0.125, pitch_classes: bool = True, allow_transpose: bool = False) -> Result`
3. **I/O.** A note is `{"start": float, "length": float, "pitch": int, "velocity": int}`, with start and length in beats. `value`: `{"score": float, "onset_f1": float, "pitch_match": float}`, each from 0 to 1. Score is `0.5 * onset_f1 + 0.5 * pitch_match`. Errors: `E_ARG` for malformed notes, negative `tol_beats`, or both lists empty.
4. **Sources.** Definitions below. No FL API used.
   - A note in `a` matches a note in `b` if their starts differ by at most `tol_beats`. Each note matches at most once, greedy by smallest difference.
   - `onset_f1` is the F1 of matched onsets (precision = matched / len(b), recall = matched / len(a)).
   - `pitch_match` is the fraction of matched pairs with equal pitch (equal pitch class if `pitch_classes`). If `allow_transpose`, the semitone shift in range -12 to 12 that maximizes `pitch_match` is used.
   - If there are no matched pairs, `pitch_match` is 0.
5. **Imports and class.** `pure`. Allowed: `typing`, `math`.
6. **Budget.** 40 lines, nesting 3, 5 parameters.
7. **Acceptance tests.**
   - Identical lists: score 1.0.
   - Same notes with every pitch +12: score 1.0 with `pitch_classes` true; `pitch_match` 0.0 and score 0.5 with `pitch_classes` false.
   - Same notes with every pitch +2: score 0.5 with `allow_transpose` false; 1.0 with `allow_transpose` true.
   - Same pitches, each start moved by 0.5 beat (more than tolerance): `onset_f1` 0.0 and score 0.0.
   - One list empty, the other not: score 0.0.
   - Both empty: `E_ARG`. A note missing `pitch`: `E_ARG`.
8. **Out of scope.** Reading MIDI files, quantizing, chord logic, extracting a top line from chords.

### Card 09. `separate_stems` (L5, model adapter)

1. **Goal.** Split an audio file into stems using the Demucs stack and return the stem file paths.
2. **Signature.** `def separate_stems(input_path: str, out_dir: str, stems: int = 4, model: str = "htdemucs") -> Result`
3. **I/O.** `value`: `{"stems": {"drums": str, "bass": str, "other": str, "vocals": str}}` for 4 stems (6 stems adds guitar and piano). Errors: `E_IO` (input missing); `E_SANDBOX_VIOLATION` (output folder outside the sandbox); `E_ARG` (stems not 4 or 6); `E_GPU_BUDGET` and `E_MODEL` pass through from the scheduler and the runner.
4. **Sources.** Pinned Demucs release and command-line options, recorded by the installer in `models/registry.toml` at setup. The agent MUST NOT import the model library; it calls `registry.call("load_model", name="demucs")` and then runs the stack's command through the runner that the registry provides. The [libretta listing](https://pypi.org/project/libretta/) notes small Demucs weights.
5. **Imports and class.** `writes_files`, cost `gpu`. Allowed: `pathlib`.
6. **Budget.** 40 lines, nesting 3, 4 parameters.
7. **Acceptance tests (the runner is faked unless marked `gpu`).**
   - With the fake runner: four files appear in `out_dir`, each path is returned, `unload_model` is called once at the end even on failure.
   - Output folder `C:\Windows`: `E_SANDBOX_VIOLATION`, and no load call is made.
   - Missing input: `E_IO`. `stems=5`: `E_ARG`.
   - `load_model` returns `E_GPU_BUDGET`: the same error is returned and the runner is not called.
   - `gpu` smoke test (run only at setup): a 5 second synthetic mixture of a click track and a sine produces four non-empty files whose durations are within 0.05 seconds of the input.
8. **Out of scope.** Judging stem quality (that is `detect_silence` and `detect_leakage`), resampling, naming stems beyond the fixed names.

### Card 10. `render_via_cli` (L6, process run)

1. **Goal.** Render a saved sandbox project to audio using FL Studio's command-line options and return the output path.
2. **Signature.** `def render_via_cli(project_path: str, out_dir: str, fmt: str = "wav", timeout_s: int = 600) -> Result`
3. **I/O.** `value`: `{"path": str, "project_hash": str, "elapsed_s": float}`. Errors: `E_SANDBOX_VIOLATION` (project or output outside the sandbox); `E_NOT_FOUND` (FL executable path from config missing, or project file missing); `E_ARG` (`fmt` not wav, flac, mp3, or ogg, or timeout not positive); `E_TIMEOUT`; `E_IO` (nonzero exit, or no output file after exit).
4. **Sources.** The [export reference](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/fformats_save_export.htm) documents the render options (`/R`, `/E<format>`, `/F<folder>`, `/O<outfolder>`). The agent MUST copy the flag syntax from that page at build time and MUST build the argument list in one place. Gate 0 records the real executable name and output location in `config.toml`; the module reads both from config and MUST NOT hardcode them.
5. **Imports and class.** `writes_files`. Allowed: `subprocess`, `pathlib`, `hashlib`, `time`. Reads the config through the registry call `get_config_value`.
6. **Budget.** 40 lines, nesting 3, 4 parameters.
7. **Acceptance tests (a stub executable stands in for FL; it is a small script that writes a WAV into the requested folder).**
   - Normal run: returns the output path, the file exists, `project_hash` equals the SHA-256 of the project file, argument list contains the format flag and the project path.
   - Stub exits with code 1: `E_IO` and the detail includes the exit code.
   - Stub exits 0 but writes nothing: `E_IO`.
   - Stub sleeps longer than the timeout (test uses `timeout_s=1`): `E_TIMEOUT`, and the process is terminated.
   - Project path in `C:\Users\x\Documents\real.flp`: `E_SANDBOX_VIOLATION` and the executable is not started.
   - `fmt="aiff"`: `E_ARG`.
8. **Out of scope.** Saving the project, loop or range selection, stems, measuring the result, retrying.

## 7. After the ten

When a model passes the calibration thresholds, the remaining cards are generated in bulk:

1. L0 to L2 cards come from the protocol spec, the generator, and wrapper templates. Many L2 cards differ only in which L1 ops they wrap.
2. L3 cards are written from the workflows in file 09. Each names the L2 calls it composes.
3. L4 cards carry the formulas and a synthetic-signal test with a derived expected value.
4. L5 cards each carry a pinned repository commit and a smoke test.
5. L6 cards each carry a recorded screenshot set and a post-condition check.

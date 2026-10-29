### Card 09. `separate_stems` (L5, model adapter)

1. **Goal.** Split an audio file into stems using the Demucs stack and return the stem file paths.
2. **Signature.** `def separate_stems(input_path: str, out_dir: str, stems: int = 4, model: str = "htdemucs") -> Result`
3. **I/O.** `value`: `{"stems": {"drums": str, "bass": str, "other": str, "vocals": str}}` for 4 stems (6 stems adds guitar and piano). Errors: `E_IO` (input missing); `E_SANDBOX_VIOLATION` (output folder outside the sandbox); `E_ARG` (stems not 4 or 6); `E_GPU_BUDGET` and `E_MODEL` pass through from the scheduler and the runner.
4. **Sources.** Pinned Demucs release and command-line options, recorded by the installer in `models/registry.toml` at setup. The agent MUST NOT import the model library; it calls `call("load_model", name="demucs")` and then runs the stack's command through the runner that the registry provides. The [libretta listing](https://pypi.org/project/libretta/) notes small Demucs weights.
5. **Imports and class.** `writes_files`, cost `gpu`. Allowed: `pathlib`.
6. **Budget.** 40 lines, nesting 3, 4 parameters.
7. **Acceptance tests (the runner is faked unless marked `gpu`).**
   - With the fake runner: four files appear in `out_dir`, each path is returned, `unload_model` is called once at the end even on failure.
   - Output folder `C:\Windows`: `E_SANDBOX_VIOLATION`, and no load call is made.
   - Missing input: `E_IO`. `stems=5`: `E_ARG`.
   - `load_model` returns `E_GPU_BUDGET`: the same error is returned and the runner is not called.
   - `gpu` smoke test (run only at setup): a 5 second synthetic mixture of a click track and a sine produces four non-empty files whose durations are within 0.05 seconds of the input.
8. **Out of scope.** Judging stem quality (that is `detect_silence` and `detect_leakage`), resampling, naming stems beyond the fixed names.

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

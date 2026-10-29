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

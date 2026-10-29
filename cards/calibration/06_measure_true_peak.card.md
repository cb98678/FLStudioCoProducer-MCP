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

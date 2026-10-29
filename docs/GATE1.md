# Gate 1: ears and generators (acceptance record)

Run on 2026-10-21. Repeat with `python tools/gate1_bench.py --out gate1.json` (also runs inside `pytest` as `tests/test_gate1.py`).

## G1-1 Measure report (passes)

`build_measure_report` was run on 19 fixtures whose answers are known from how they were built (sine levels, white noise, drum loop, mono, out of phase, hard clipped, a real intersample over, a silent gap, loudness steps, DC offset, bass in the side channel, 44.1/48/96 kHz, 16/24 bit/float).
Each value was checked against something that is not our code: the maths of the signal, ffmpeg's EBU R128 meter (`ebur128=peak=true`), and pyloudnorm.

| What | Tolerance |
| --- | --- |
| Sample peak, RMS | 0.1 dB |
| Integrated loudness vs ffmpeg and pyloudnorm | 0.15 LU |
| Loudness range vs ffmpeg | 0.6 LU |
| True peak vs maths and ffmpeg | 0.35 dB |
| Correlation | 0.02 |

Result: 108 checks, 0 failed. The first run had 2 failures; both were a wrong fixture of mine (an "intersample" signal that was not an over, and an edge click that made ffmpeg and our meter see different peaks), not a measurement defect. Fixed in the fixture, with a slow fade so every meter sees the same peak.

## G1-5 DSP accuracy (passes the agreed rules)

Labeled set (synthetic, so the answer is exact): 68 tempo cases (16 tempos x plain/swung/noisy, plus techno, house, dubstep, drum and bass and hip-hop patterns) and 96 key cases (all 24 keys x clean, 30 cents detuned, 14 dB noise, with a techno drum loop on top).

| Measure | Result |
| --- | --- |
| Tempo, blind, top candidate exactly right (within 1 percent) | 73.5 percent |
| Tempo, blind, right or an octave off (double or half) | 97.1 percent |
| Tempo, true value among the candidates | 100 percent |
| Tempo, wrong top candidate that was NOT flagged ambiguous | 0 |
| Tempo, with the genre's tempo range given | 100 percent exact |
| Key, exact | 100 percent |
| Key, exact or relative major/minor | 100 percent |

**Finding.** Blind tempo reads 124 to 135 BPM techno and house patterns as half tempo (64 for 128), and 80 and 90 BPM hip-hop as double. The true tempo is always in the candidate list, and with the genre range (or the project tempo as a hint) it is right every time. The defect was that these wrong answers were not flagged. `estimate_bpm_dsp` now flags `ambiguous` when a 2:1 or 3:2 relative has real strength and lists them in `relatives`. The flag is raised on 41 of the 50 correct blind answers too, so treat blind tempo as a shortlist and always give a hint. FL knows the project tempo, and the genre profiles carry the range.

**Limit.** The key set is synthetic chords. 100 percent says the algorithm is right on clean harmonic material, not that it is 100 percent on real mixes. Real tracks with a known key and tempo are needed to measure that.

### Pass rules (accepted by the owner on 2026-10-22)

| Rule | Value |
| --- | --- |
| Tempo: true value in the candidate list | at least 99 percent |
| Tempo: wrong top answer without the ambiguous flag | 0 |
| Tempo: exact when the genre range is given | at least 95 percent |
| Tempo: exact blind | at least 70 percent |
| Key: exact | at least 90 percent |
| Key: exact or relative | at least 95 percent |

# Mix and master targets: proposal for your decision

Nothing here is active. `targets/streaming_default.toml` stays blank until you approve; the proposed values are in `targets/streaming_default.PROPOSED.toml`.

## What your three reference tracks measure

Decoded from 128 kbps MP3 to 48 kHz WAV, measured with the project's own `build_measure_report` (raw numbers: `docs/reports/reference_measurements.json`).

| Measure | Don'tellmecalmdown | Howiesim | Notorious | Spread |
| --- | --- | --- | --- | --- |
| Integrated loudness (LUFS) | -13.94 | -13.72 | -13.90 | 0.2 |
| Loudest short-term (LUFS) | -11.8 | -12.1 | -12.0 | 0.3 |
| True peak (dBTP) | -3.12 | -1.81 | -3.57 | 1.8 |
| Loudness range (LU) | 5.22 | 3.63 | 3.93 | 1.6 |
| Crest factor (dB) | 11.3 | 12.5 | 10.68 | 1.8 |
| Stereo correlation | 0.928 | 0.964 | 0.981 | 0.05 |
| Side minus mid below 120 Hz (dB) | -21.5 | -21.0 | -26.4 | 5.4 |
| Clipped samples | 0 | 0 | 0 | 0 |
| Tempo (blind, flagged ambiguous on all three) | 159.8 (or 79.8) | 130.2 | 140.1 | |
| Key (blind) | B minor, weak margin | G major, near tie with G minor | F major | |

Band levels (dB, relative to full scale, bands as defined in `dsp.DEFAULT_BANDS`): the three tracks agree within 2.4 dB in every band, so a single spectrum target works.

| Band | sub | bass | low mid | mid | high mid | presence | air |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Average of the three | -2.7 | -4.4 | -16.1 | -14.8 | -17.6 | -19.8 | -21.6 |

## One conflict you need to settle

All three references sit at about **-14 LUFS**, which is Spotify's reference level, not the roughly -9 LUFS club master you chose earlier. They have 3 to 5 LU of loudness range and 11 to 12 dB of crest factor, which is a streaming master, not a hard-limited club one.

- **Match the references (-14 LUFS)**: the proposed file below. Backed by Spotify's own guidance ([Loudness normalization](https://support.spotify.com/bd-en/artists/article/loudness-normalization)) and by tracks you picked.
- **Louder (-9 LUFS)**: only if you want a club master. No reference of yours measures that, so I would need a reference at that level, and Spotify advises a -2 dBTP ceiling above -14 LUFS.

## Proposed values (derived from the table, in `targets/streaming_default.PROPOSED.toml`)

| Setting | Proposed | Basis |
| --- | --- | --- |
| Integrated loudness | -14.0 LUFS, plus or minus 1.0 LU | References -13.7 to -13.9; Spotify reference level. The tolerance is my choice |
| True peak ceiling | -1.0 dBTP | Spotify guidance for lossy delivery; references -1.8 to -3.6 |
| Loudness range | 3 to 6 LU | References 3.6 to 5.2 |
| Crest factor | 10 to 13 dB | References 10.7 to 12.5 |
| Stereo correlation floor | 0.85 | References 0.93 to 0.98, with room |
| Mono below | 120 Hz, side minus mid at most -20 dB | References -21 to -26 dB; -20 is the module's own mono threshold |
| Spectrum | within 3 dB per band of the reference average | Tracks agree within 2.4 dB |
| Clipping | 0 samples | All references 0 |

## Caveats

- The references are 128 kbps MP3. The encoder cuts high frequencies and can move true peaks, so the "air" band and true peak are least reliable. WAV or FLAC versions would tighten those two.
- Three tracks give three data points per number. Treat the ranges as a starting point.
- Blind tempo and key are ambiguous on all three, as the Gate 1 bench predicted. Tell me the real tempo and key if you know them and I will record them in the genre profiles.
- Apple Music's level (-16 LUFS) comes only from a secondary source ([Production Expert](https://www.production-expert.com/production-expert-1/apple-choose-16lufs-loudness-level-for-apple-music-heres-why)); check Apple's own documentation before relying on it.

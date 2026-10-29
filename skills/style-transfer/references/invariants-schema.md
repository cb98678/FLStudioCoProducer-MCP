# Invariants file (specs/<project>/invariants.toml)

All keys are required except `must_keep` and `free_to_change`. Any value still starting with `FILL` is refused by `load_invariants_file`.

```toml
tempo_source_bpm = 128        # from estimate_bpm_dsp, confirmed by the human
tempo_policy = "genre"        # keep | genre | half_time
energy_arc = "a few words in the human's terms"
must_keep = []
free_to_change = ["drums", "bass_sound", "arrangement_details", "fx"]

[key]
tonic = "A"
mode = "minor"

[melody]
track = "lead"
midi = "specs/PROJECT/melody.mid"   # human reviewed
contour_threshold = 0.0             # chosen by the human; compare_note_sequences score

[harmony]
chord_loop = ["Am", "F", "C", "G"]  # from detect_chord_loop, human confirmed
bars_per_loop = 4

[[sections]]
name = "drop"
bars = 32
```

Tempo policy: `keep` uses the source tempo; `genre` uses the genre profile's range (a clean ratio of the source if one exists); `half_time` keeps the feel and re-expresses the drum pattern at half or double time.

Notes are stored in beats, not seconds.

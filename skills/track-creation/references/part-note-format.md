# Note lists

Notes are dictionaries in beats: `{"pitch": 60, "start": 0.0, "duration": 1.0, "velocity": 100}`.
`pitch` is a MIDI number 0 to 127, `start` and `duration` are in quarter-note beats, `velocity` 0 to 127.
A drum pattern is the same list with one pitch per drum, using the pitch map of the human's drum plugin or kit (ask if unknown).
Changing tempo does not change these numbers: they are beats, not seconds.

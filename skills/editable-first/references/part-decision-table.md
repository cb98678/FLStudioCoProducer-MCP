# Part decision table

Use with `docs/PRODUCTION_POLICY.md`. The first matching row wins.

| Question | Yes | No |
| --- | --- | --- |
| Is it the human's own recording, or a vocal performance? | Keep or place it as audio | Next |
| Is it a riser, downlifter, reverse crash, impact or sweep? | Audio on the FX channel | Next |
| Is it a long evolving texture or a resample the human wants baked? | Audio | Next |
| Is it a drum hit? | Sampler channel plus pattern | Next |
| Is it pitched and note-based? | Synth channel plus piano-roll notes | Build editable and ask |

## Matching a generated sound with a synth

1. Measure the generated sound: fundamental, harmonic ratios, decay, band energy.
2. Choose a synth patch the human owns that is close; clone its channel so the patch comes along.
3. Play a test note, render, and compare the same measurements. Adjust the patch, the note keys (raw key is MIDI minus 12 before the patch offset) and velocities.
4. Stop when the bands agree within a few dB; taste is the human's call.

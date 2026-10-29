# Verifier arguments (the `verify` object of a step)

| Verifier | Passes when | `verify` keys |
| --- | --- | --- |
| `none` | always; reads only | none |
| `readback` | the result reports `verified: true` | none |
| `file_nonempty` | the file named by a path in the result exists and has bytes | `path` (default `value.path`) |
| `measure_within` | a number in the result is inside a range | `path`, `min`, `max` |
| `stems_not_silent` | every stem in a mapping has sound | `path` (default `value.stems`) |
| `key_match` | two audio files have the same estimated key | `a`, `b` |
| `bpm_match` | tempo is within tolerance of a wanted value | `path`, `bpm`, `tolerance`, `allow_octave` |
| `melody_similarity` | the melody score is at least a minimum | `a`, `b` (note lists), `min` |
| `screenshot_post` | the window matches an expectation | `title_contains`, `dialog_contains`, `no_dialog`, `element` |
| `original_untouched` | the original project's hash is unchanged | none |
| `human_review` | the person approves | none |

Paths are dotted: `value.stems`, `meta.verified`. A path that starts with `$s02.` reads the value from step `s02`'s result.

### Card 08. `compare_note_sequences` (L4, pure)

1. **Goal.** Score how similar two note lists are in rhythm and pitch, for the melody-preservation check.
2. **Signature.** `def compare_note_sequences(a: list[dict], b: list[dict], tol_beats: float = 0.125, pitch_classes: bool = True, allow_transpose: bool = False) -> Result`
3. **I/O.** A note is `{"start": float, "length": float, "pitch": int, "velocity": int}`, with start and length in beats. `value`: `{"score": float, "onset_f1": float, "pitch_match": float}`, each from 0 to 1. Score is `0.5 * onset_f1 + 0.5 * pitch_match`. Errors: `E_ARG` for malformed notes, negative `tol_beats`, or both lists empty.
4. **Sources.** Definitions below. No FL API used.
   - A note in `a` matches a note in `b` if their starts differ by at most `tol_beats`. Each note matches at most once, greedy by smallest difference.
   - `onset_f1` is the F1 of matched onsets (precision = matched / len(b), recall = matched / len(a)).
   - `pitch_match` is the fraction of matched pairs with equal pitch (equal pitch class if `pitch_classes`). If `allow_transpose`, the semitone shift in range -12 to 12 that maximizes `pitch_match` is used.
   - If there are no matched pairs, `pitch_match` is 0.
5. **Imports and class.** `pure`. Allowed: `typing`, `math`.
6. **Budget.** 40 lines, nesting 3, 5 parameters.
7. **Acceptance tests.**
   - Identical lists: score 1.0.
   - Same notes with every pitch +12: score 1.0 with `pitch_classes` true; `pitch_match` 0.0 and score 0.5 with `pitch_classes` false.
   - Same notes with every pitch +2: score 0.5 with `allow_transpose` false; 1.0 with `allow_transpose` true.
   - Same pitches, each start moved by 0.5 beat (more than tolerance): `onset_f1` 0.0 and score 0.0.
   - One list empty, the other not: score 0.0.
   - Both empty: `E_ARG`. A note missing `pitch`: `E_ARG`.
8. **Out of scope.** Reading MIDI files, quantizing, chord logic, extracting a top line from chords.

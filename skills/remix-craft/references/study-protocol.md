# Studying an original and its remix

For each pair the person brings (files in the sandbox, never the person's originals written), work through these steps and write the
result to sandbox/remix_study/SONG/REMIXER.md, then add what it teaches to moves.md.

1. **Analyse both.** `build_song_analysis` on the original and on the remix: stems, tempo and beat grid, key vote, transcribed words with
   their times, sections. Check the key with `estimate_key_dsp` on each mix and say when the two readings differ.
2. **Tempo and key change.** The remix's tempo against the original's (same, double, half, or a stretch: how many percent) and its key
   (same, relative, transposed). Listen for whether the vocal was stretched or re-sung.
3. **Where every line went.** Match the remix's transcribed words to the original's lines. For each original line: absent, whole, or
   chopped; in which remix section and function (mix in, verse, riserchorus, drop, breakdown, climax, mix out); treated how (filtered,
   pitched, stuttered, gated, reversed). This shows the anchor and how much was kept.
4. **What is new.** Drums, bass, chords under the same melody (compare the bass roots and chord readings section by section), the lead
   sounds, any element taken from the original's background into the foreground. `measure_part_sound` on the remix's stems describes
   the new sounds.
5. **The energy curve.** `measure_section_levels` and `measure_band_energy` on both: loudness, low end and brightness per section, how
   each drop differs from the one before, where the climax is, how long the mix in, breakdown and mix out run.
6. **The form.** Write the remix's form as functions, in Osborn's terms (rotations, riserchorus, drop) and in club terms (mix in, ramp,
   breakdown, climax), next to the original's verse and chorus form.
7. **The reading.** One paragraph: what the remixer decided (purpose, anchor, how much kept, tempo, harmony, form) and the one move that
   makes it work. Then the moves to add, each with the bars where it happens.

8. **Loops and kit.** `extract_song_loops` on both, per section of the form (skill `loops-and-kits`): the drum, bass and music loops with
   their repetitions averaged, the kit, the drum patterns and the bass line as MIDI. How cleanly a loop averages says how programmed the
   part is (Freejak's drums -21 to -30 dB, the original Sorry's -4 to -11 dB). `find_matching_loops` ranks FL's factory loops and kicks
   against them.
9. **The page.** docs/remix_studies/SONG_REMIXER.md with a form map image (every bar, the stems' levels, the functions), the reading,
   the facts table, where every line went (named by number and its first words, never reprinted), the form, drums, bass, harmony,
   energy, the moves with their bars, the options added, and the limits. Then the options in the bank, the moves in moves.md.

Measures that held up on Sorry: per-bar stem levels; three-band step profiles of the drum stem (the attack, not the level, so a ringing kick
is one hit); the bass notes per 16th of the averaged bass loop; chords from the other stem's chroma with the bass's lowest note; the vocal's
pitch percentiles and pitch-class shares (key kept or not), its formants (a resampled vocal moves them) and line timing (the stretch); the
tuning with pYIN on a monophonic stem, not a whole-mix estimate (librosa's estimate read Sorry 20 cents sharp; pYIN said 3 cents);
side-under-mid per band for width.

Limits to say out loud: stems separated from a finished remix bleed; words transcribed from a chopped vocal are partial; a key read from a
bass-heavy mix can land a fifth away. What only ears can judge goes to the person as a question.

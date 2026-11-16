# The person's brief (2026-11-06), and what each line became

The person, after the Hello Toni 2 transcription: "look we are getting better but I want update more. you try to use math to replicate
notes you heard in the music exactly and it sounds terrible. lets try to re write this skills like this for vocals and padding and bass."
The brief they gave, quoted in full:

> Act as an experienced session keyboardist and arranger creating a background MIDI track. Do NOT follow, copy, or mimic the main vocal
> melody's rhythm or phrasing. Instead, create a complementary, supportive arrangement that leaves maximum frequency and rhythmic space
> for the singer.
>
> - Function: Provide harmonic anchoring and steady rhythm. Use sustained chords (pads/whole notes) or simple, repetitive rhythmic
>   ostinatos that stay firmly on the grid.
> - Contrast: If the vocal melody is fast and rhythmic, use long, smooth, legato chords. If the vocal is slow and spacious, use a subtle,
>   rhythmic arpeggio that stays tucked in the background.
> - Syncopation & Off-Notes: Forbid any erratic or random off-beat notes. All syncopation must be strictly deliberate, groove-based, and
>   locked to the drum grid (e.g., pulling back slightly on the 2 and 4).
> - Call-and-Response: Only introduce melodic motion or flourishes during dead spaces, specifically when the vocal phrases end or during
>   transitions between song sections.
> - Velocity: Do not make all notes a flat 127 velocity. Use natural human velocity curves, softening the notes that land on weak beats.

With three rules for prompts: name the functional role in production terms; demand restraint and low density (limit polyphony to 3 or 4
notes); define the grid relationship (quantize to 1/8 or 1/16, no unquantized triplets unless part of a continuous groove).

| Line of the brief | Here |
| --- | --- |
| Do not follow the vocal's rhythm or phrasing | the vocal is read only for where she sings, how fast, and her range; no part takes her notes or rhythm |
| Leave frequency space | the pad sits under her low note and over the bass octave; the answer line over her high note, only in her rests |
| Harmonic anchoring, steady rhythm, on the grid | pad chords held or re-struck per bar; bass on named cells; every start on its role's grid (the check counts off-grid starts) |
| Contrast | phrase modes by syllables per beat: hold (busy), pulse, move (spacious: the keys figure plays) |
| No random off-beat notes | syncopation only from arranger.CELLS, the same cell every bar of a section; the check counts bass starts outside the cells |
| "pulling back slightly on the 2 and 4" | done with velocity (beats 2 and 4 under 1 and 3) and length, not timing: the person's own rule keeps keys and bass quantized |
| Call and response only in dead spaces | the answer line: rests of at least 1.5 beats, an 8th of air each side, never two in one bar, not every rest |
| Velocity curves, weak beats softer | arranger.VEL by 16th position, scaled per role, a small fixed variation; the check fails a flat or maxed part |
| Polyphony 3 or 4 | pad at most 4 (3 when she is busy), keys, bass and answer one at a time |
| Quantize to 1/8 or 1/16 | bass and pad on 16ths, keys and answer on 8ths |

Why the rules are code: a prompt asks; it does not stop a writer from scattering notes. Here the notes are written by `arranger.py` and
`check_support_parts` fails any part that breaks a rule, so a broken part is caught before anyone hears it.

---
name: song-blueprints
description: Use when the person wants a remix or track in the manner of a known record or era (Zedd's Clarity, Tiesto's Red Lights, Real McCoy's Another Night, 90s Eurodance, 2010s progressive house), brings a written breakdown of a song to learn from, or asks to mix and match techniques (progressions, bass grooves, pluck rhythms, held pads, pumps, vocal spaces) from studied songs, including the vocal-led layers recipe (pad under spaced stabs, rolling then long bass, chords that follow the voice).
---

# Song blueprints

The person (2026-10-29) brought three written breakdowns, of Clarity, Red Lights and Another Night, and asked for them as "skills, recipes, options and guidance" so the pieces can be mixed and matched. The same day they asked for a recipe of their own: synths that follow the voice's chords, long pad chords under stabs that are spaced out, a bass that rolls sometimes and stretches out when it drops, and piano rolls as long as a section. This skill holds both, checked against public sources, and maps every move to the option, module or manual step that makes it. It works on top of `remix-from-stems`, `creative-variety` and `track-creation`; their rules still hold.

## Rules

- A breakdown is a claim until a source confirms it. Each reference page splits what the sources confirm from what only the breakdown says. Never tell the person an unconfirmed key or chord is the record's.
- A move can be good even when its attribution is not: an option keeps the technique and says the attribution is unconfirmed (harmony.eurodance_i_VI_VII_v).
- Take the moves, never the record: chord functions, step grids, layer roles, spaces and curves. Melodies, hooks, lyrics and samples belong to the record. The voice in a remix is the person's song.
- The project's targets win over a breakdown's numbers. The breakdowns master to -6 to -4.5 LUFS; this project masters to the style's targets (about -8 LUFS, panel checked) unless the person asks for louder. Their gain-staging peaks are starting points; the part-level loop sets the real levels.
- Every new breakdown goes the same way: verify (web, latest sources, cite), a reference page here, options with their source in `src/coproducer/data/options` (the record under "references" in sources.json), tests (tests/test_variety.py checks every option overlays a valid pack and cites a known source).

## The blueprints

| Record | Confirmed | The moves worth taking | Page |
| --- | --- | --- | --- |
| Clarity (Zedd feat. Foxes, 2012) | A flat major, 128 bpm; transcriptions of the chords disagree | a progression that floats and never lands on I, suspended ii and V, inverted chords keeping the bass moving, 3-over-4 lead phrasing, a pump that keeps going without a kick | references/clarity.md |
| Red Lights (Tiesto, 2013) | Gm Eb Bb F, 125 bpm, G minor | an acoustic 3-3-2 pluck verse with empty lows, a heavy mono bass only at the drop, a voice-led pad whose upper voices barely move, a layered drop lead, an exponential pump recovery | references/red-lights.md |
| Another Night (Real McCoy, 1993) | 126 bpm; rap verse by O-Jay, sung chorus by Karin Kasar; chords unconfirmed | the Euro-gallop bass (root, octave, octave, rest), a barking house-organ chord stab, a dry rap verse against a wide washed chorus | references/another-night.md |
| The vocal-led layers recipe (the person's, 2026-10-29) | first built on Girlish Type Men (sandbox\remix\gtm_vocal_v6) | chords per section from the voice, a held pad under stabs with whole bars of space, a bass that rolls in verses and holds longer notes in drops, section-long piano rolls | this page, "The vocal-led layers recipe" |

## Mix and match

Each row is one move and what makes it. Lock options in `build_song_plan` (options.variety.lock, for example {"harmony": "harmony.minor_i_VI_III_VII", "bass": "bass.euro_gallop", "chords": "chords.tresillo_332_pluck"}) or from the shell with `--lock`. Moves from different records combine freely; the brief decides.

| Move | Option, module or step | From |
| --- | --- | --- |
| I V vi IV, two bars a chord | harmony.pop_I_V_vi_IV | Clarity (remix transcriptions) |
| ii sus4, V sus4, vi7, iii7, IV add9: never on I | harmony.sus_ii_V_vi_iii_IV | Clarity (Hooktheory) |
| i VI III VII, the minor anthem loop | harmony.minor_i_VI_III_VII | Red Lights |
| i VI VII v, Eurodance into a minor v | harmony.eurodance_i_VI_VII_v | Another Night (unconfirmed) |
| Chords that follow the voice section by section | `voiceharmony.section_loops` on the voice's notes, written to the plan's bar_roots and root_quality | the person's recipe |
| Held pad under spaced stabs | chords.pad_and_spaced_stabs (its own Pad part) | the person's recipe |
| Voice-led held pad, no stabs | chords.voice_led_pad (`stylepack.lead_voices`) | Red Lights |
| 3-3-2 plucked chords | chords.tresillo_332_pluck; for single notes arp.tresillo_pluck | Red Lights |
| Rolling bass in verses, long notes in drops | bass.roll_then_long_drop | the person's recipe |
| Root, octave, octave, rest | bass.euro_gallop | Another Night |
| The chord's third in the bass on every fourth bar | bass.inverted_turnaround | Clarity |
| No low end until the drop | bass.empty_verse_square_drop | Red Lights |
| 3-over-4 lead resolving on bar 4 | arp.three_over_four | Clarity |
| Pump that recovers on a curve | mix.exp_recovery_pump (`pump.pump_points`, curve exp) | Red Lights |
| Pump without a kick (breakdowns) | mix.ghost_trigger_pulse | Clarity's ghost-kick lead pump; the demos |
| Dry verse voice, wide chorus voice | vocal.dry_verse_wide_chorus | Another Night |
| Layered drop lead, house organ, PWM bass | references/sound-recipes.md (serum-mcp `generate_preset` specs) | Red Lights, Another Night |
| Frequency lanes, gain staging, master targets | references/mix-guide.md | all three |
| Fills and sweeps on the last beat of bar 4 or 8 | the drum plan's last-bar fills and the fx options' cues already land there; check the plan | all three |
| Piano rolls as long as a section | the plan's "pattern_bars": 16 (`remixbuild.blocks`, `flpfile.Flp.add_part_blocks`) | the person, 2026-10-29 |

## The vocal-led layers recipe

For a song whose voice should lead every instrument (the person, 2026-10-29, on Girlish Type Men):

1. Fit and tune the voice first when asked (skill `gui-fallback`: `quantize_vocal_gui`, `apply_vocal_tuning_gui`), and keep its notes (Newtone's MIDI, or the intake's sung melody).
2. Place the notes on the remix grid (`voiceharmony.to_remix`), weigh them per bar (`voiceharmony.weights_by_bar`) and run `voiceharmony.section_loops`: each section kind gets the four chords of the key that hold its sung notes best (two bars a chord, one in builds), and kinds the voice barely sings borrow the loop it sings most. Try the key's own v and a major V (qualities) and keep the better total. Write bar_roots and root_quality into the plan.
3. Lock chords.pad_and_spaced_stabs and bass.roll_then_long_drop (or swap in any row above: bass.euro_gallop under the same pads is a Eurodance take), set "pattern_bars": 16, and keep a lead that doubles the voice only where it helps (lead_notes cut to the later drops leaves the first drop to pad, stabs and voice).
4. Build with `tools/remix_song.py ... --plan PLAN --match-sounds`: the pad's Serum sound takes the voice's tone and the envelope and width of the pad option's sound (sound.flex_simmering_pad), never the voice's own staccato envelope.
5. Check by ear: the pad under the voice, the space between stab groups, the long drop bass against the pump. Read the pattern list: one piano roll per section, a repeated section reusing its roll.

## Steps for a blueprint remix

1. Brief first (`remix-from-stems`, `remix-craft`): the song's own mood, key, tempo and hook. A blueprint is a palette for this song, not a template to fill.
2. Choose the moves: two to four rows from the table that fit the brief, at most one per category from each record so the result is a blend, not a copy. Say which record each came from.
3. Lock them and draft (`build_song_plan` with options.variety.lock); read the choices back; keep the record's own chords unless the brief asks for a re-harmonization (the harmony rows replace them).
4. Sounds: generate from references/sound-recipes.md with serum-mcp `generate_preset`, or use them as the direction for `match_part_sound` so the tone still comes from the song.
5. Build, produce, render and master with `tools/remix_song.py` as usual; the panel and the listening gates decide.
6. Report the moves in plain words with their records, and what you would try instead.

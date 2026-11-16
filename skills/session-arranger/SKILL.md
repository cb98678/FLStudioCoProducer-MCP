---
name: session-arranger
description: Use whenever keys, pads, chords, a bass or any melodic part is written under or around a vocal (a remix, a new track over a singer, "make piano and bass for her voice", "pads and bass for this vocal", "something that supports the singer"), and whenever the person says the parts copy the vocal, sound like a transcription, are too busy, random or off-beat. Write them as a session keyboardist and arranger would: complementary to the vocal, low density, locked to the grid, groove-based syncopation only, fills only in her rests, natural velocities. Covers the two recipes the person kept (band, band_guide: chosen at creation), write_support_parts, check_support_parts, a plan's support block and the build's support pass over every style pack.
---

# Session arranger: parts that make room for the singer

The person (2026-11-06), after hearing Hello Toni 2's voice and guitar transcribed note for note: "you try to use math to replicate notes
you heard in the music exactly and it sounds terrible." The brief they gave is in references/brief.md, in their words, with what each
line became here. The short version: read the song, never copy it. Keys, pad, bass and answer line are written fresh from four readings.

## Choose at creation: band or band_guide

The person heard four versions of Hello Toni 2 and kept two (2026-11-06: "I like 2 and 4 both ... so I can choose at time of creation").
Both keep her own instruments (the separated "other" stem: her guitar, keys, strings) under the arranged parts. Ask which one before the
plan is drafted, unless they already said; write the answer into the plan and the decision log.

| Recipe | What plays around her voice | How to ask for it |
| --- | --- | --- |
| **band** (option 2, the default) | the arranged or fitted parts, and her own instruments about 6 dB under her | `tools/remix_song.py ... --support band`; `build_song_plan` options support {"mode": "band"} |
| **band_guide** (option 4) | the same, plus a guide melody of her main notes (the note she holds longest in each half bar, snapped to the key, at most two a bar) about 6 dB under her | `--support band_guide`; support {"mode": "band_guide"} |
| off | the style pack's parts exactly as written (for A/B only) | `--support off` |

`--no-original` (keep_original false) leaves her instruments out. Without the other stem there is nothing to keep, and the plan says so.

## Two ways the parts are made

| The plan's support parts_from | Who writes the notes | Used by |
| --- | --- | --- |
| arranger | `arranger.arrange`: pad, keys figure, bass on the section cells (SECTION_CELLS by section name), answer line | packs that keep the song's own feel: straight_song, organic_deep |
| pack (every genre pack) | the pack writes its own groove; the build fits it around her (`arranger.fit_part`): the arp only in her rests or under a spacious phrase (call and response), the stabs held as one legato chord per bar under a busy phrase, stab and pad notes inside her range moved an octave down (not under C3), at most four notes struck together, flat velocities given the beat curve; the bass keeps the pack's cells (already deliberate) with the beat curve | tech house, house, techno and every other genre pack |

Every style pack carries a "support" block (parts_from, default_mode) that the plan starts from. In the build (`remixbuild.support_state`)
the vocal is read on the remix grid through the clips that place it (where she sings per 16th at a 20 dB floor, her onsets, her range by
YIN), the chords come from the plan's roots, the answer line goes on the arp channel where the pack's arp is silent, the guide joins it
when asked, and `arranger.check` runs on the result (the build report's "support"). A plan's explicit "support_parts" (from
`write_support_parts`) still win over both.

## The four readings (and nothing else)

| Reading | Where it comes from |
| --- | --- |
| The key | the song analysis's key vote (`build_song_analysis`), checked against the chord table |
| The chord of each bar | the chord table: skill `stem-transcription` (chroma plus plucked notes, close calls by hand) or the analysis's bar roots; a reading with a margin under 0.1 against its parallel (A against Am) is unsure |
| Where she sings and rests, per 16th | her stem's envelope (`write_support_parts` reads it; a stem with bleed needs a 20 dB floor instead of 30) joined with a pitch reading of her line when there is one; joined means sung if either says so, the safe side for the answer line |
| How busy each two-bar phrase is | her syllable onsets per beat over the phrase |

Her transcribed notes are a reading of where and how fast she sings, and of her range. They are never played.

## The roles

| Role | Job | Rules written into `arranger.py` and measured by `check_support_parts` |
| --- | --- | --- |
| Pad (harmonic anchor) | sustained chords | at most 4 notes at once (3 under a busy vocal); voiced under her low note (top at least 2 semitones under her 10th percentile) and over the bass octave (C3 up); each chord in the inversion closest to the last; an unsure third is left out (a sus2 shape) |
| Keys (background figure) | only under a spacious vocal: a broken chord in 8ths (root, fifth, third, fifth), soft | 1 note at a time, the 8th grid, velocity about two thirds of the pad's |
| Bass (rhythm-section anchor) | one groove cell per section, roots with fifths and octaves | 1 note at a time, the 16th grid, starts only where its cell puts them; an approach note (a scale step into the next root) only on the last 8th of a phrase's last bar or before a section changes cell |
| Answer line (call and response) | a few scale tones only in her rests | starts an 8th after she stops, ends an 8th before she comes back, at most 4 notes, never two figures in one bar, over her high note; not every rest gets one |
| Her voice | stays her audio | chunked and fitted per skills `vocal-chunking` and `newtime-newtone`; no synth doubles her melody unless the person asks; then the simplified guide (arranger.guide_melody: the note she holds longest in each half bar, snapped to the key, on the 8th grid, at most two a bar, never her ornaments) rather than her line as sung (`voiceharmony.lead_rows`) |

**Contrast** (per two-bar phrase): 1.5 syllables a beat or more is busy, and the keys hold long legato chords, one per chord change; 0.75 or
less (or under 30 % of the phrase sung) is spacious, and the pad thins to root and fifth while the keys figure moves; in between, the
pad is re-struck each bar. These are starting values: tune them by ear per song and write the reason down.

**Syncopation** only from the named cells (arranger.CELLS): whole, halves, halves_fifth, quarters, eighths, eighths_octave, push (the
'and' of 2 into beat 3), anticipate (the last 8th takes the next bar's root). The same cell every bar of a section; a section may swap
cells for its last bars as a lift. Nothing else lands off the beat.

**Velocity** by beat strength: beat 1 about 104, beat 3 96, beats 2 and 4 88, the other 8ths 76, 16ths 64, scaled per role, with a small
fixed variation from each note's place (the same every run). Never flat, never 127. The person's "pulling back slightly on the 2 and 4"
is made with velocity and length on the grid, not by moving notes: their own rule keeps keys and bass quantized. FL's channel swing is
the way to add timing feel to a whole part.

## Steps

1. Read the song: the analysis, the chord table, her stem (the level-raised copy for a quiet recording), her range.
2. Name the sections in bars (0-based, end exclusive) and give each a bass cell that fits its energy: the quiet ones whole or halves, the
   choruses push or eighths, a lift for the last bars before a peak. Decide per song (the person: guidelines, not guardrails).
3. `write_support_parts`: the parts, the phrase modes, the cells, the answers used, the check, a JSON and a MIDI file in the sandbox.
4. `check_support_parts` passes before anyone hears it. A failure names the rule and the role.
5. Into FL, editable. In a remix: the plan's support block does it in the build (above). By hand: a plan's "support_parts" (from
   `write_support_parts`) play on the pad, stab, bass and arp channels in place of the style's own, and an arranged bass silences the
   sub. A stand-alone project (her stems as reference clips, the parts in 16-bar piano rolls) is how Hello Toni 2 was first done.
6. The instruments are chosen for this song, every part (skill `sound-design-recipes`, "Choosing the sound": a library preset or a
   sound made for it, never the last song's). In a remix the build does it (`select_part_sound`). In a stand-alone project, test each
   choice in a command-line render with a held chord and a scale first. A demo channel can sound off its written octave (BooBass,
   Bien Duro channel 9, sounds an octave under: write the bass an octave up on it). The Hello Toni 2 instruments below were that song's
   choice, not a set for the next one.
7. Balance by measured level against her vocal (live median over 0.4 s blocks): pad about 6 dB under, bass about 3 to 5 under, keys and
   answer 8 to 10 under. Then the person's ear decides.

## Worked example: Hello Toni 2 (take 2), 2026-11-06

`sandbox\songs\hellotoni2_take2\arranged\` (build_arranged3.py, arrangement.json, arranged.flp, arranged_parts_only.flp, the renders).
D major, 117.5 bpm, 47 bars, the D A G A loop with an Em and an Am. She sings fast: 1.5 to 2.6 syllables a beat in 18 of 24 phrases, so the
keys hold through most of it (18 hold, 5 pulse, 1 move: the figure plays only bars 25 and 26). Her range B3 to G4 put the pad at B2 to
A3 (139 notes); the bass has 142, the keys 16, the answer 10. Bass cells: verse whole then halves, choruses push, the hook anticipate, the whisper whole and soft, verse 2 halves with
fifths, chorus 2 push with eighths for its last 4 bars. Four answers in her rests (bars 14, 26, 46, 47). The check passed with no
failures; rendered back, the bass's root sounds on all 46 bar downbeats and the pad's three strongest pitch classes hold at least two
chord tones in 46 of 46 bars. Levels against her vocal: pad -6.1 dB, bass -4.6, keys and answer about -9.

The person could not choose between a guide melody and keeping her guitar, so all four were built and rendered
(arranged_1_parts, arranged_2_parts_her_guitar, arranged_3_parts_guide, arranged_4_parts_guide_her_guitar, each an FLP and an mp3 in
listen_v2): the guide has 81 notes over 47 bars, mostly D4 to F#4 on FLEX Synth Strings (Song For You channel 8) about 6 dB under her;
her guitar sits 6 dB under her; the master has 3 dB of headroom (her vocal and guitar together reached 0 dBFS without it). The person
decides by ear. When a choice is unclear and cheap to render, build every option and let them listen.

## Rules

- Never play a transcribed note. Transcription (skill `stem-transcription`) is for reading, and for when the person asks for the notes.
- Restraint: low density is the default. Silence is part of the arrangement.
- Every rule lives in code and in the check, not only in this text.
- The person's preferences hold: editable first, piano rolls a section long (up to 16 bars), keys and bass quantized.

## Sources

- The person's brief, 2026-11-06 (references/brief.md).
- `src/coproducer/arranger.py`, `tests/test_arranger.py`; this project's `docs/LESSONS_TO_RECIPES.md` (the session-arranger rows).

---
name: remix-craft
description: Use before planning any remix, whenever the person asks what a remix should be or how DJs and producers approach one, and when they bring an original song with its remixes to study. Decide the remix's purpose, anchor, how much of the original it keeps, tempo, key and harmony, form and drops per song, the way professional remixers work, instead of laying a new beat under the song's own verse and chorus order.
---

# Remix craft

The person (2026-10-28): "you keep making a recipe to copy paste the same format of remix over and over again regardless of the song. The
style, structure, drops and overall production needs to be varied and creative and inventive, not locked to the same format." The cause
was in the arranger: it maps every verse to a groove and every chorus to a drop, so the song's own order became every remix's form, and
the option bank only decorated it. This skill comes before `creative-variety` and `remix-from-stems`: they choose patterns and build; this
one decides what the remix is. The research behind it, with sources, is `docs/REMIX_RESEARCH.md`.

## What professionals do, in one paragraph

A remix takes a record to an audience or a room it would not reach (Langford). It is built around one or two anchors from the original: the
whole vocal (Todd Terry's "Missing"), one line nobody noticed (MK's "Push the Feeling On"), a short instrumental figure (Chris Lake's guitar
run on Taylor Swift's "Opalite"), a bassline (Honey Dijon). How much it keeps runs from extended (the song, longer), through selective
(some parts added and removed) to reflexive (a new piece that still names the original) (Navas). Tempo, key and harmony are choices:
double or half time, a stretch of up to about 10% on the vocal, the relative major or minor, new chords under the same melody. The form is
designed, not inherited: club mixes are built for mix points and an energy ramp, and EDM pop splits the chorus into a riserchorus (the hook
over the build) and a drop (Osborn). Drop two is never drop one again. One song supports many different readings: "Cola" has at least
eleven official remixes, from a 2:52 chilled mix to an 8:24 club mix.

## Decide these before any pattern

Write each decision into the creative brief (skill `remix-from-stems`, references/creative-brief.md) with the reason from the song.

1. **Purpose and room.** Peak-time club, warm-up, festival, afternoon or boat party, radio, home listening, a DJ tool. The room decides the
   tempo band, the drop style, the mix in and out, and the length (radio 3 to 3.5 minutes, club 7 to 8).
2. **The anchor(s)**, at most two: the whole vocal, the hook line, an overlooked line, an instrumental figure, a bassline, a texture.
   Solo the vocal stem first; it usually shows the direction. Say why this anchor carries the song.
3. **How much it keeps**: extended, selective or reflexive. Keep the anchor and the song's meaning; everything else is open. Too much of
   the original is a bootleg; too little and the artist does not hear their song. The person's rule (2026-10-28) holds whatever is
   chosen: lines stay whole and no word is ever cut, while which lines are kept, in what order and in what role is this remix's choice.
4. **Tempo**: the original tempo, double or half time, a stretch within about 10%, or the genre's standard tempo when the vocal takes
   it (Freejak took Sorry from 100 to house's 128, x1.28, pitch and formants kept; the form option's tempo "standard"). Ballads go up; a
   bouncy vocal can come down a little: the person (2026-10-28) allows up to 6 % slower, never more, pitch and formants kept. Say what
   the vocal will sound like.
5. **Key and harmony**: keep the chords, swap to the relative major or minor, write a new progression under the vocal and check it
   against the vocal's notes, change only the chord where the vocal clashes, or flip the mood (major to a darker minor). Reharmonising is
   one of the strongest ways to make a remix new; say what the new harmony does to the song's feeling.
6. **Form**: choose a form design from references/moves.md, or write a new one, as a list of functions (mix in, verse, riserchorus, drop,
   breakdown, climax, mix out) with the source lines each one plays and how they are treated (whole, chopped, filtered, stuttered, pitched).
   Two remixes of the same song never share a form design.
7. **Drops**: plan each one. What changes from drop one to drop two (bass pattern, voicing, drums, a new element), where the climax
   falls (the last chorus in vocal music, the last quarter in instrumental music), and the moments that make them land (a silent bar
   carried by tails, the drop's melody teased before it, the hook over the drop beat at the end).
8. **Sound and groove**: drums and groove first; the bass's job (support, or the star: rolling, wobbling, talking); one bold sound move
   (a role swap such as strings becoming the bass, a gate turning a pad into a rhythm, overdrive after the reverb and delay).
9. **Versions**: the club mix first; radio edit, dub and instrumental when the person or the room needs them.

## Make the plan carry the concept

- `build_song_plan` drafts sections in the song's own order, and a form option can now turn each pass's function (verse_as, chorus_as,
  drop_after, tail_break: verse 1 on the groove, chorus 1 sung in a break, verse 2 in a break, chorus 2 on the drop). For a form the
  options cannot express yet, rewrite the plan's sections, vocal clips and chop events before `build_remix_project`, and say in the plan's
  notes which form and anchors it uses.
- A harmony option with reharmonize replaces the record's chords under the whole song, and its loop can change chord inside the bar (two
  chords a bar, the change pushed a 16th early). The engine keeps the record's chords unless the harmony is locked: re-harmonizing is a
  decision for the concept, checked against the vocal's notes.
- Use the option bank (`creative-variety`) for grooves, kits, bass lines, chord rhythms, sounds and transitions that serve the concept;
  lock the ones the concept needs rather than taking whatever the engine draws.
- The person's earlier rules still hold: editable parts first, sounds generated to match the original, chops are whole phrases at their
  own pitch, and nothing of the user's originals is written.

## Check before rendering

- Does it differ from the last remix of this song in purpose, anchor, form and harmony, not only in patterns?
- Is the vocal intelligible everywhere it is meant to carry the song? Reverb and delay are throws and tails, not a wash (the person: the
  echo and reverb on curse house A made the song inaudible).
- Is drop two different from drop one, and is there a climax?
- Can a DJ mix in and out (8 to 16 clean bars) unless the purpose says otherwise?

## Studying the person's examples

When the person brings an original and its professional remixes, study each pair with references/study-protocol.md, then add what it
teaches to references/moves.md as a move with its source (artist, remixer, the bars where it happens), and to the option bank as choices
sourced to the study (sources.json "remixes"). The study is the point: name the decisions the remixer made, not only the measurements.
The loops, kit and patterns come from `extract_song_loops` (skill `loops-and-kits`); references/fl-howto.md has the FL Studio steps for
each move.

Studied so far (docs/remix_studies):

- **Sorry, Freejak (Clean), 2026-10-28.** The whole vocal in order at house's 128 (x1.28, pitch, key and formants kept), each pass a
  different job (verse 1 groove, chorus 1 in a break, a stop bar, the record's own hook as the drop, verse 2 in a break, chorus 2 on the
  drop), new chords (iii IV | ii V, two a bar, pushed a 16th), the dembow's 3-3-2 kept as a dotted-8th bass and pluck over a straight
  kick, the bass an octave up and ducked hard, the low end mono. The drops are within 0.5 LU of the verse groove: contrast by subtraction,
  three breaks and two stop bars in 2:39. The options: "form.whole_song_turned", "drums.house_layer_in", "bass.dotted_pump",
  "harmony.iii_IV_ii_V_pushed", "fx.stop_bar_sweep", "vocal.whole_in_order", "mix.mono_low_hard_pump". Lesson for the panel: a remix
  needs frequent, short, deep subtractions, not louder drops.

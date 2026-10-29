# The creative brief: every song gets its own remix

The person, 2026-10-26: "It sounds like you're following the same format for every song. We don't copy paste formats but make decisions based on the song, the sonic space, key, bpm, lyrics; we match the tone of the song. You are creative, let that shine in the plan."

The pipeline's rules are constraints, not a template: the vocal at its own tempo, faster or at most 6 % slower with its pitch kept, whole sung lines with no word cut (which lines, in what order and role, is the remix's choice), editable parts, the person's ear has the last word. Everything else is a decision made for this song, written down with its reason before anything is built.

## 1. Read the song before deciding anything

Write these into the brief (and `song_notes.json`, field `mood`), each with where it came from:

| Question | Evidence |
| --- | --- |
| Mood: happy, sad, bittersweet, romantic, angry, defiant, playful, comic, nostalgic, anxious, euphoric (one or two) | The lyrics' story and themes (research, never quoted), the key and mode (major, minor), the tempo, the singer's delivery (shouted, crooned, rapped, laughing), what writers and fans say about it |
| Energy and arc | Section levels of the original, where it peaks, whether it builds or stays flat |
| Sonic space | What plays: instruments, their register, attack and sustain, brightness, distortion, stereo width, the era (drum machine 1986, live band 2006), how dense the arrangement is, where there is room |
| Key, mode, harmony | The key vote, the chords (bass roots, harmony stem, a tested MIDI file), whether it is a vamp or a progression |
| Tempo and feel | Its bpm, straight or swung, half-time sections |
| The hook and the favourite parts | What people sing back, the famous riff, the line everyone quotes |

## 2. Decide, for this song

1. **Style, or a blend, from the mood and the sonic space, not from habit.** See `genre-styles` for the mood map. A sad song is not a peak-time techno track unless there is a reason (and the reason is written down).
2. **Tempo.** Inside the rule (at most 6 % slower than sung, pitch kept; up to 35 % faster) choose what serves the mood: the song's own tempo, a lift, a half-time feel under it.
3. **Palette.** The remix sounds are designed to match the original's own (`sound-design-recipes`, "Choosing the sound"): `measure_part_sound` reads each part the remix answers (its attack, decay, sustain, brightness, harmonics, width and register, with words for this brief), the Serum MCP generates a sound from that reading, and `compare_part_sound` checks the remake against the original before it goes on a channel. The same key and register, similar attack and sustain, the same brightness and grit, so the new parts sound like they belong to the record. Then one or two moves that are new, named here.
4. **Arrangement.** Choose which whole lines carry this remix, in what order and in what role (the person, 2026-10-28: lines stay whole, no word cut; the form is the remix's choice, skill `remix-craft`); choose how the remix frames them. Pick moves from the menu below that fit this song, and do not reuse the last song's set wholesale. Record each with its reason in the plan's notes.
5. **The surprise.** Every remix gets at least one idea that is particular to this song (a riff turned into the lead, a key lift for the last chorus, a breakdown built from the a cappella, a call and response between two singers, a filter that follows the lyric). Say what it is and why.

## Menu of moves (choose; do not apply all)

- Intro: the hook a cappella, a filtered loop of the original, the famous riff alone, a cold open on the first line, a long DJ-friendly drum intro.
- Builds: the verse carried on into the chorus, a stutter on a title syllable, a pitch riser on the vocal, a snare roll, a drop-out bar of silence, a reversed vocal.
- Drops: the chorus whole over the drop, the hook chopped into a rhythm, an instrumental drop with the riff as the lead and the chorus after, a bass that answers the vocal.
- Breaks: the original's instruments alone, an a cappella breakdown, a half-time section, a key change into the last chorus.
- Chops and effects: call and response between lines, echo throws on line ends, gated chops, formant or pitch moves (staying in key), a filter sweep that opens with the story.
- Outro: the tagline alone, a mix-out drum loop, the original's ending, a fade on an effect tail.

## 3. Record it

The plan carries `brief` (mood, palette, decisions with reasons, the surprise) and the notes list every choice. When the person edits the result, the diff of their edit becomes a rule only when it holds across songs (`LESSONS_TO_RECIPES.md`); one song's taste stays that song's.

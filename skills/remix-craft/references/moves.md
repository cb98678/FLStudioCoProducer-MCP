# Remix moves

Each move names where it comes from. Add moves from the person's examples with the song, the remixer and the bars where the move happens.
Bar counts are starting points at 4/4; a form is written as functions, then filled with the song's own lines.

## Form designs

**F1 Hook first, one verse.** The riserchorus idea (Osborn) and DJcity's "hook first" versions. Mix in 16, riserchorus (the hook over a
build, no kick) 8, drop 16 (instrumental, or the hook chopped), the one verse 16, riserchorus 8, drop two 16 (varied), breakdown 16 to 32
(the bridge or a stripped chorus), the hook over the drop beat as the climax 16, mix out 16. Good for a song with a strong title hook and
weak verses.

**F2 The overlooked line.** MK, "Push the Feeling On": one line of the chorus that most listeners did not notice, looped and chopped into
the groove, carries the whole remix; the full chorus appears once, if at all, in the breakdown. Good for a song whose obvious hook is worn
out or does not suit the room.

**F3 Whole song, new room.** Todd Terry, "Missing": every vocal line in order, new drums, bass and harmony underneath. Extend it the club
way (Langford): 8 or 16 instrumental bars after each chorus, a breakdown of about a minute, the last chorus repeated or an instrumental pass
before it. This is close to what the pipeline did by default; choose it on purpose, for a song whose story needs every line.

**F4 Instrumental figure as the drop.** Chris Lake on "Opalite": a short figure from the original (a guitar run, a riff, a fill) becomes
the drop's lead, treated hard (reverb and delay, then overdrive after them); the vocal lives in the verses and riserchorus.

**F5 Three rotations.** Osborn's compound AAA: rotation one short (riserchorus and drop only), rotation two complete (verse, prechorus,
riserchorus, drop), rotation three altered (a bridge hybrid, then the hook over the drop beat). Each rotation adds or removes something.

**F6 One late climax.** Instrumental and hypnotic music (Wikipedia, Drop: the climax in the final quarter): layers enter and leave over 8
or 16 bar blocks, vocal fragments as texture, one real peak near the end.

**F7 Anti-drop.** Wikipedia, Drop: the chorus is more minimal than the build; the beat leaves on the hook and the vocal stands alone,
then the groove returns. Strong for an emotional chorus.

**F8 Built around the bridge.** Soundfly: make the bridge the chorus, or the second verse the intro; a remix can be built on the part of
the song nobody remembers.

**F9 Tempo switch.** Hyperbits: switch rhythm; drop one in full time and drop two in half time (or the reverse), the vocal unchanged.

**F10 Dub.** Langford's dub mix and Honey Dijon's dub versions: the drums, the bass and one synth, vocal fragments only, long mix in and out;
a DJ tool more than a song.

**F11 The whole song turned.** Freejak on Justin Bieber's "Sorry" (2026-10-28 study): every line in its order, sped up to the style's
standard tempo, each pass a different job. Intro 4 (the hook, claps, hats), verse 1 on the groove 16 (kick and bass alone for 8, then claps
and hats), chorus 1 sung over a break 7 with the bass out, a stop bar, a drop of the record's own hook 16, verse 2 in a break 7, a stop bar,
chorus 2 on the drop 16, a two-bar breath, the last hook drop 13, a one-bar end. Good for a song whose every line matters and whose own
form already lifts into a hook. Option "form.whole_song_turned".

## Drop moves

- Drop two differs from drop one: a new bass pattern, a different chord voicing, new drum fills or percussion, a new texture, a vocal
  added or removed (Lost Stories Academy).
- A bar or two of silence carried by reverb and delay tails before the return; one new element on the final chorus (Langford, part 2).
- Tease the drop's melody before the drop; build fragments of the original into it (Hyperbits).
- The hook over the drop beat as the last section, a riserchorus-drop (Osborn: David Guetta and Anne-Marie, "Don't Leave Me Alone").
- Pull energy back before the next peak: simpler drums, more space for the vocal (Lost Stories Academy).
- A stop bar: drums, bass and music out for the bar before the drop, a one-bar white-noise sweep, the last sung words hanging (Freejak,
  Sorry, bars 28 and 52). No riser builds needed; option "fx.stop_bar_sweep".
- Drop halves: the first 8 bars bright (the bass filter open, the hook up front), the second 8 darker (the bass closed by 14 dB above
  250 Hz) with a louder off-beat chord layer and the vocal further back (Freejak, Sorry, bars 29 to 44 and 71 to 83).
- Contrast by subtraction: the drops can sit within 0.5 LU of the verse groove when something leaves every 16 bars (the bass for 7 bars,
  everything for one): Freejak's breaks are 1.7 to 3.6 LU down, its stop bars 3 to 12 LU (Sorry).

## Harmony moves

- The relative major or minor: the melody still fits and the mood turns (Langford, part 2; Hyperbits).
- A new progression under the vocal, checked against its notes; one that bridges verse and chorus when they live in different harmonic
  worlds (Chris Lake).
- Change only the chord where the vocal clashes (Langford, part 3).
- Faster harmonic rhythm under the same melody: the record's IV vi V (two chords over two bars) became iii IV | ii V, two chords a bar,
  each second chord a 16th early (Freejak, Sorry, bars 5 to 83). Option "harmony.iii_IV_ii_V_pushed" (lock it; check the vocal's notes).
- Flip the mood: a bright major song made minor and darker (Soundfly). A melody that does not fix its key can be set in several modes
  (Ethan Hein on "Starman": G minor, D minor, C Mixolydian, A Phrygian).

## Tempo moves

- Double or half time: a song in the mid 90s goes to 128 or to 64 (Langford, part 2).
- A stretch within about 10% for the vocal (Langford, part 3); speeding up usually sounds better than slowing down (Berklee Online).
- Published examples: Disclosure's "You & Me" at 130 became Flume's half-time future bass (listed 150) and Rivo's afro house at 122
  (Mixgraph). The person (2026-10-28): slower is allowed "but not too slow and preserve pitch", at most 6 % (stylepack.MAX_SLOWDOWN).
- The genre's standard tempo over the smallest stretch: Freejak took Sorry from 100 to 128 (x1.28), the vocal's pitch, key and formants
  kept (same median note, formants within 3 %), no tempo change anywhere. In FL: e3 Mono or Stretch pro with F.Shift at 0.

## Sound moves

- Drums and groove first, then the bassline (Honey Dijon; Purple Disco Machine).
- Swap roles: a string motif becomes the bassline (MusicRadar, 18 tips); a pitched vocal chop plays as an instrument (Melodics).
- Gate a sustained part into a rhythm (HAAi used Duck on strings for a trance pattern).
- A harder bass from another genre's sound (Hamdi built his from a drum and bass sound).
- Overdrive after the reverb and delay so the effects distort (Chris Lake).
- A wobble or rolling bass: a filter moved by a beat-synced LFO (a triplet 8th is common), bright distortion, heavy compression, a clean
  sub under it (MusicRadar on the wobble; the sub layer is common practice). Change the LFO rate per beat or per bar to make it talk.
- Keep the record's rhythm in the new genre: Sorry's dembow 3-3-2 became a dotted-8th bass and pluck on 16th steps 1, 5, 8, 11 and 14
  (4-3-3-3-3) over a four-on-the-floor kick; the pluck plays a fifth above the bass (Freejak). Option "bass.dotted_pump".
- The bass an octave above a dancehall 808 (G1 to C2 instead of B flat 0 to C 1), its harmonics up to 1 kHz carrying it on small speakers,
  ducked 12 to 15 dB by each kick and back by the off-beat, the low end mono (Freejak, Sorry). Option "mix.mono_low_hard_pump".
- Drums that layer in: the kick alone for 8 bars under the verse, then claps on 2 and 4 and the off-beat open hat (Freejak, Sorry, bars
  5 to 20). Option "drums.house_layer_in".

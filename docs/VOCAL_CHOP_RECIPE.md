# Vocal chop recipe

How the tech-house remix cuts sung vocal into chops and phrase clips. Rules come from the "my blues aw" bug: `CP_Chop_bluesaway.wav` ended inside "away", and the same fault hit
the whiskey chop. The user's hand-cut clip `sandbox\stemstest\MyBluesAwayfixed.wav` is the regression baseline (start about 141.82 s, end about 143.88 s in the original stem), not an asset.

## Why the old cut clipped words

1. The cut points came from Whisper word times, which drift 0.2 to 0.7 s on sung vocal, then were nudged to the nearest energy minimum.
2. On a held vowel the nearest minimum sits inside the word (a dip at vibrato or a consonant), so the cut landed mid-"away".
3. Nothing checked that the cut ended in silence, and the chop was cut from the stretched file with a fixed hint instead of from the original signal.

## What the second bug taught ("ky drowns")

A gap in the signal is not always a word boundary. In "whis-KEY" the quiet stretch before the k is the mouth closure of a stop consonant, inside the word. The gap rule
ended the whiskey chop there (so it held only "whis") and started the drowns chop on the held "-ky" that follows. Stops (k, t, p, d, b, g) leave a silent closure inside words,
so energy alone cannot separate "word ends here" from "consonant closure here". Whisper cannot place the boundary either (its word times drift by 0.2 to 0.7 s), and it
reads isolated clips of a few hundred ms badly (it hears "I'm losing weight" in a good bluesaway), so it is not a final check on a finished chop.

## Rules (code: `src/coproducer/vocalchops.py`, `src/coproducer/cutrefine.py`, `tools/refine_cuts.py`, `tools/techhouse_audio.py`)

1. Each cut in `remixplan.CHOPS` names its words (`words`) and, where known, the words just outside it (`prev`, `next`). A hint time only says where to look.
2. Candidates come from the signal: syllable onsets and gap ends for a start; onsets and gap starts for an end (`cutrefine.candidates`).
3. The recogniser judges each candidate by voting over several window lengths (2 of 3): the audio to the left must end on the previous word whole, and the audio to the right
   must start on the cut's own words with no leftover word in front (one filler such as "the" is ignored). A leftover syllable such as the "Hey" of "-key" fails the right side.
4. Gap-bounded candidates (the end of a gap for a start, the start of a gap for an end) are tried before onset-only ones. Between candidates of equal standing the earliest wins.
   A leftover syllable fails the right-hand test; I first tried moving the boundary back onto the biggest timbre change, and that put 80 ms of the "ky" back
   in front of "drowns", so it was removed. The recogniser's refusal to accept a leftover is the evidence to trust.
5. A cut that ends in silence (a phrase end) is not forced onto a seam. Once the recogniser says the last word is whole, the end moves on to where the voice stops
   (`voice_end`: the level is 6 dB or more below the last 0.3 s and the 4 to 12 kHz band is quiet). The recogniser calls "okay" whole as soon as "o-kay" is under way, and the
   held "ay" runs on for another 0.6 s; it also accepts "place" for "places".
5b. Sibilants are sound. A trailing s is faint overall but loud in the 4 to 12 kHz band, so gaps are measured with that band counted (`vocalchops.gaps`, `hf_guard`), and any end
   that lands just before a hiss is extended through it (`sibilant_end`). Without this the s of "places", "drowns" and "blues" was cut off.
5c. A final s can come after a gap (third round, user listening notes 2026-10-23). In the original stem the closing hiss of "blues" sits 0.3 s after the vowel has died, with a quiet
   voiced stretch between, and the "iz" of "places" and the "dz" of "friends" come after a short vowel or a dip. Every earlier rule stopped at that first dip or at the first hiss,
   so `CP_Chop_blues`, `CP_Chop_hook` and `CP_Chop_friends_echo` read "my blue", "low place" and "friend". The rule is lexical plus signal (`cutrefine.final_s`, wanted by
   `cutrefine.wants_final_s`): if the cut's last word is spelled with a final s and the word after it does not start with s, z, sh, ch or j (so it cannot supply its own hiss), the
   end moves on to the end of the first hiss within 0.45 s. A hiss is 4 to 12 kHz level above -42 dB, within 16 dB of the total level (a bright vowel is not a hiss) and at least 5 dB
   above the 50 ms before it; once inside it only the level test applies. The end lands 15 ms after the last hiss frame, which is the dip in front of the next word. If a hiss already
   ended within 60 ms before the end, the cut has its s and nothing moves. The words after the cut come from `next`, or from `after` where `next` would also steer the recogniser (the hook's
   "the whiskey"). Long clips are not touched: they end where the voice stops. Measured on the stem: blues 142.56 to 142.94 s, hook 137.19 to 137.32 s, friends 134.92 to 135.19 s,
   drowns unchanged (it already had its s).
5d. A phrase clip ends where the sung phrase ends, not at the hint. The break-2 verse clip was hinted to end at 71.0 s ("the oasis") but the verse runs on, with no gap longer than
   0.35 s, to "cause I've got friends in low places" at 78.44 s, which is the 64 marker of the playlist. The user extended the clip by hand to there and found the phrasing hits the
   next section; the hint is now 78.2 s and the clip's tail words are "low places".
6. If an edge cannot be confirmed (cold starts such as the first word of a phrase read badly) it falls back to the signal-only rule: onset minus 20 ms in, gap start plus 30 ms out.
   The build log and `techhouse_audio.json` list which edges were confirmed.
7. Each chop is time-stretched on its own, after cutting from the original stem, with 40 ms of silence padding that is trimmed afterwards. Stretching the whole stem first
   smeared the tail of the previous word into the front of the next chop.
8. Long gaps inside a phrase chop are squeezed in the original domain (`squeeze_gaps`, `max_gap`), then the chop is stretched.
9. Finish: 90 Hz high-pass, 5 ms fade in, 35 ms fade out, peak -2 dBFS.
10. Verify visually: spectrogram, envelope, gaps and cut spans on one plot, and listen to the join of neighbouring chops (whiskey + drowns). The ear is the final judge.

Run order: `tools\refine_cuts.py` (host Python with torch, about 3 minutes, writes `cuts.json`), then `tools\techhouse_audio.py --cuts cuts.json`, then `tools\build_techhouse.py`.

## Baseline and results

| Chop | Words | Original stem span |
|---|---|---|
| bluesaway | my blues away | 141.813 to 143.860 s (baseline 141.82 to 143.88) |
| whiskey | whiskey | 137.663 to 138.483 s (was 137.66 to 138.09, which held only "whis") |
| drowns | drowns | 138.480 to 139.473 s (was 138.19 to 139.60, which started on "ky") |
| okay | I'll be okay | 146.260 to 147.630 s (was ending at 147.35, before "okay" was whole) |

## Second baseline: the hand-fixed okay clip

`sandbox\techhouse\FriendsInLowPlaces_TechHouse_v3e_userfix.flp` holds the user's own fix: the break chorus clip extended from 129147.2 ms to 130114.9 ms (stretched time), i.e.
the original stem from 147.63 s to 148.73 s. The recipe now ends that clip at 148.48 s where the voice stops (the gap starts at 148.42 s) plus a 0.25 s ring-out for long clips.
The same flaw cut the drop-2 clip's "away" at 143.22 s, now 143.89 s.

## Vocals on top of each other

`remixplan.chop_conflicts` lists chops that start while an earlier chop's dry part still sounds, and chops that ring into the next section; `tools/build_techhouse.py` prints it.
A chop may start inside an earlier echo tail but not inside a dry part. It was written after Chops 22 (user notes): a `hook_echo` tail, an `okay_echo` and a `drowns` sounded together at
the end of each drop, and in the first drop the echo also bled into the pick-up of the break's verse clip, which starts half a bar before bar 56. Now the last hook of a drop is dry, the last
answer is left out, the first drop closes on the dry `okay` and the second on `okay_echo`. The 16th chatter (friends and blues, bars 80 to 87, Chops 23 to 27) was removed: it was
cluttered and inaudible and did not give the high-pitched gabber stab it aimed for.

## Echo

`src/coproducer/chopfx.py`: ping-pong echo at 3/16 note, feedback 0.5, 5 repeats, band-limited 250 to 3800 Hz in the loop, baked into a separate `CP_Chop_<name>_echo.wav` sampler
channel (`remixplan.ECHOED`), so dry and echoed hits are both editable in the piano roll.

## Tagged for later (not built): remix recipe, original elements

The user wants a recipe for how remixes should sound, including when and how original elements come back. First item: place clips of the original instrument stems, aligned to the
bar grid (`origin_s` 27.3085, 108.478 bpm), in selected sections so the guitar melody is reminiscent of the original, for example in a break or the first drop. To decide when it is
built: which sections, which stems, what processing (filter, stretch to 124 bpm, level under the vocal).

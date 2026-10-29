# Vocal chops that keep whole words

Read this before cutting a sung vocal into chops or phrase clips. Vocals are one of the allowed audio exceptions, but a chop must still be a whole word or phrase.
The full rules and the history of each bug are in `docs/VOCAL_CHOP_RECIPE.md`; the code is `src/coproducer/vocalchops.py` and `cutrefine.py`; the host runners are
`tools/refine_cuts.py` (decide the cuts), `tools/techhouse_audio.py` (cut, stretch, shape, echo) and `tools/build_techhouse.py` (write the FL project).

## The recipe, in order

1. Name the words of every cut (`words`) and, where known, the words just outside it (`prev`, `next`, or `after` for the s rule). A hint time only says where to look.
2. Take candidate edges from the signal, not from the recogniser's word times (they drift 0.2 to 0.7 s on singing). A quiet gap is not always a word boundary: the closure of
   a stop (k, t, p, d) sits inside words like "whis-key".
3. Judge each candidate with the recogniser by vote over three window lengths: the audio before the cut ends on the previous word whole, the audio after starts on the
   cut's own words with no leftover syllable in front. The recogniser is trusted to reject leftovers, not to find the end of a held vowel or an s.
4. End on where the voice really stops (`voice_end`), through a trailing hiss (`sibilant_end`), and if the last word is spelled with a final s and the next word cannot
   bring its own hiss, on to the closing s or z even when it comes after a dip (`final_s`; blues, places, friends).
5. A long phrase clip ends where the sung phrase ends, plus about 0.25 s of ring-out. Do not end it at a hint that falls mid-verse.
6. Cut each chop from the original stem, then time-stretch that chop alone (a neighbour's tail must not smear into it). Shape: 90 Hz high-pass, 5 ms fade in, 35 ms fade out.
7. Check: `check_vocal_edges` on every finished chop (cut mid-sound? ends on a hiss?), `find_final_s_end` on the stem for a word that should end in s, a spectrogram of the last
   second of each chop, and `chop_conflicts` on the plan so no two dry chops sound together. Then ask the human to listen; the ear is the final check.

## Do not

- Do not cut a chop out of a word or a fragment of a line (the person, 2026-10-25: "random words that aren't even full words"). A chop is a whole sung line or the title line through its last word, ending in air or at the next word's onset (`songform.phrase_chops`).
- Do not trust a recogniser's start for a long first word sung straight on from the note before ("'cause" after a held "complain"): `cutrefine.word_start` finds where the pitch leaves the held note. Do not end a cut past the next word's onset, and do not end one before a closing s in either mode (`remixaudio.whole_end`).
- Do not put a chop's first sample on the beat: its first word is rarely on one. Keep the song's beat phase (`remixbuild.chop_phase`).
- Do not start a chop on a pickup word slurred from the note before ("'cause" after a held "complain"): start on the next word, as the person did (`remixaudio.chop_window`).
- Do not stretch a vocal slower than it was sung: it sounds long and drawn out (hip-hop at 0.83x, drum and bass at 0.80x, 2026-10-25).

- Do not move an edge onto the biggest timbre change to fix a leftover syllable: it put the "ky" of "whiskey" back in front of "drowns".
- Do not trust a recogniser reading of a finished 300 ms chop; it hears words that are not there.
- Do not stack an echo tail over another chop's dry part (it sounds muddy), and do not let an echo ring into the next section's pick-up.

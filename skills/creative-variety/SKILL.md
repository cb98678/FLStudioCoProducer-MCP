---
name: creative-variety
description: Use for every remix and every new track, and whenever the person says the results sound the same, asks for variation, creativity, a different take, another version, or ideas from the FL Studio demo songs: choose the form, groove, kit, bass line, chords, arp, instruments, transitions, mix and vocal treatment per song from the option bank the demos taught, so no two remixes share a format.
---

# Creative variety

The person (2026-10-28): "you keep making the same format and same song over and over again and this is not the point of this. I need variation and creativity." Every remix before that had one template: intro, groove, an 8-bar riser build, a drop with eight bars of chop games, the same off-beat bass, the same stab, the same rising arp, the same risers and the same deep pump. This skill is the fix. It works on top of `remix-from-stems` and `track-creation`, never instead of them; their rules (the vocal never slower, whole phrases, whole verses and choruses, editable parts, sandbox only) still hold.

## Where the options come from

Twenty FL Studio 2026 demo songs were studied project by project and render by render (`docs/DEMO_STUDY.md`, one page per song in `docs/demo_study`). What they do became the option bank, `src/coproducer/data/options`, one file per category:

| Category | What it decides | Realized by |
| --- | --- | --- |
| form | sections, which choruses get a build, chop-game tails, a bridge or Mid 8, intro and outro lengths, a gap before the drop, drum drop-outs | the arranger (songform) and the drum plan |
| drums | the grid of every voice per section kind, swing, fills, rolls | the drum plan (voices now include perc and ride) |
| kit | the samples of a demo song's kit, voice by voice | the build (FL factory paths) |
| bass | the bass and sub lines (root, octave, fifth, fifth below, seventh, flat second, holds) | the bass and sub parts |
| chords | the chord part's rhythm and voicing (seventh, add9, sus, open, octaves, minor-major, harp run) | the chord part |
| arp | shape (fall, pedal, tresillo, chromatic, sequence...), rate (12 for triplets), where it plays | the arp part |
| harmony | an 8-bar loop for parts the record gives no chords for | the plan's roots and chord qualities |
| sound | a demo instrument (its channel, as its designer left it) for the stab, arp, bass or sub, and its measured sound | the build imports it; with Serum it is the direction for `match_part_sound` |
| fx | the cues at each moment (into a drop, a build, a break) and transition moves | the FX bed and the production recipe |
| mix | pump depth and source, bus layout, master chain | the production recipe |
| vocal | how many chop games, the vocal stack and sends | the chop games; the stack by hand |
| automation | long filter opens, reverb for breakdowns, throws, wobbles | the production recipe or by hand |

Published records the person brought breakdowns of (Clarity, Red Lights, Another Night, 2026-10-29) added harmony, bass, chord, arp, mix and vocal options, cited under "references" in sources.json; skill `song-blueprints` has what was confirmed, the mix-and-match table and the vocal-led layers recipe (chords.pad_and_spaced_stabs, bass.roll_then_long_drop). Every option names the demo songs it came from and says in words what it does and how to make it in FL. Options with a "manual" note are moves made after the build with the modules (`apply_fx_chain`, `create_send_route`, `add_automation_clip`, `set_plugin_param_by_name`).

## Steps

1. **Brief first.** Write the creative brief as `remix-from-stems` says (its creative-brief reference): the song's mood words with evidence, its energy, sonic space, key, tempo and the hook. The brief's moods and the style are what the choices are scored on.
2. **Choose.** `build_song_plan` with options.style and options.variety. By default variety is on: it reads the remix history (sandbox/variety_history.json), scores every option against the brief, takes points off what the last remixes used (the last one 3 points, the two before 1.5, up to ten back 0.5), draws among the best few from a seed (the plan's name, so a plan is reproducible), and borrows one category from another genre with the same feeling (the surprise). Lock what you or the person decided: options.variety.lock {"drums": "drums.dembow", "sound.arp": "sound.tinke_bell"}. Another seed gives another valid plan for the same song; false keeps the style pack exactly as written. From the shell: `python tools/remix_song.py NAME STYLE --variety-seed S --lock drums=drums.dembow --mood dark`.
3. **Read the choices and argue with them.** The plan holds "variety" (choices, alternatives, why, the surprise), "style_overrides" (the pack fields it sets), "production_overrides", "kit" and "instruments", and a notes line naming every choice. Check each against the brief and the record: a form that fights the song's own form, a groove that fights the vocal's rhythm, a sound that crowds the original's instrumentation. Swap with a lock and draft again; say why in the plan's notes. The engine proposes; the brief decides.
4. **Sounds.** For each part with a sound choice: with Serum 2, run `match_part_sound` with options.direction set to the instrument's measured sound (the plan's instruments entry, "measured"): the generated sound keeps the original part's tone and takes the demo instrument's envelope, gating and width (soundbrief.blend). Without Serum, `build_remix_project` imports the demo instrument itself from its render copy (sandbox/demo_study/render) and moves the part's notes into the instrument's own register. A part with a generated Serum state always keeps it.
5. **Build and produce.** `build_remix_project` (it records the choices in the history when it succeeds) and `apply_production_recipe` with plan_file set to the plan, so the song's transitions, pump and buses are merged into the style's recipe. Then the manual moves the chosen options name, one at a time, each read back.
6. **Say what was chosen.** Tell the person the form, the groove, the bass, the instruments and the surprise in plain words, with the demo song each came from, and what you would try instead (the alternatives). Their reaction is the next lock. `python tools/compare_remixes.py WORK1 WORK2 ...` puts versions side by side (choices, sections, sounds, master loudness) and counts the categories each pair differs in.

## Rules

- Never two remixes with the same form and groove in a row. Check the history: if the choices match the last remix in more than half the categories, draft again with another seed or lock a change.
- The record comes first: its chords stay (harmony keeps the original whenever the record has roots), its tone is matched, its form is respected; the options change how it is played.
- A surprise is a deliberate risk: name it, and give the person the safe alternative.
- Chops stay whole phrases at their own pitch whatever the vocal option says; vocal.chop_instrument is ask-first.
- Options are starting points from twenty songs; the person's references and edits override them. When the person fixes a choice, lock it for that song and, if it is a pattern, add or change the option (with its source) rather than the code.
- Add options from every new reference project (`study-reference-project`): a new groove, bass line or form goes into the bank file with its source, and tests/test_variety.py checks it is valid.

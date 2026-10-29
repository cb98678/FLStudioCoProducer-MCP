# Status

Updated 2026-10-29 (the vocal-led layers recipe and section-long piano rolls; song blueprints from the person's breakdowns; before that, stems by FL Studio's own Extract stems from sample at intake; before that, Newtime and Newtone driven by GUI recipes and modules; a vocal-led remake of Girlish Type Men). Before that, updated 2026-10-28 (Serum 2 wavetables and sampler sounds made from the song's own loops and kit; the first remix study, Sorry against Freejak's remix: seven options, per-pass form functions, two-chord-a-bar re-harmonization, loop and kit extraction; before it the FL demo study: an option bank and a variety engine so remixes stop sharing one format, fifteen style packs; earlier: creative brief, sounds matched to the record, installer). **New session? Start with `HANDOFF.md`, then `ROADMAP.md`.** The dated log below is history.

## Counts

545 modules (L0 13, L1 320, L2 56, L3 42, L4 57, L5 22, L6 35), 206 exposed as tools. About 1770 tests pass in the cloud copy; `coproducer lint`
and `ruff check` are clean. FL's Python API offers 365 functions in the stubs inventory plus the 2025 and 2026 additions; 319 have a generated
L1 op (keystroke-style ui calls and device internals are left out on purpose, `ROADMAP.md`, "FL control"). On FL 26.1.7 all 176 read ops
answered live (`tools/probe_l1.py`, 2026-10-25); the 143 write ops are tested on the fake FL only.

## Proven on the real machine

| Area | How it was checked |
| --- | --- |
| Bridge (loopMIDI, controller script, framing, 108 ops) | Gate 0 and the stress report (`STRESS_REPORT.md`), FL 26.1.7 |
| Command-line render, solo splits, folder renders | Renders on the host; render needs FL closed (`FL_API_FINDINGS.md`) |
| FLP patching: channels, patterns, playlist, markers, automation clips, effect injection, routing, Layers, channel pitch and filter | FL opened and rendered the results; injected effects read back with 0 of 79 parameters different |
| Editable remix build, production recipe, gain staging, section contrast, master | Friends tech-house v12 to v16, approved by ear; the production pass also on the Future House demo with its own production off |
| Whisper word times, Demucs, Basic Pitch, Music Flamingo | Pinned environments on the host (`DEPENDENCIES.md`) |
| Song intake (`build_song_analysis`): RoFormer vocals, beat_this grid, torchcrepe melody, key vote | Friends on the host: 108.504 bpm against 108.478 by hand, downbeat 27.34 s against 27.31, vocal 9.6 dB SDR against the true stem, key A major |
| Five genres end to end (house, techno, dubstep, dnb, trap: plan, build, produce, render, contrast, club master) | Host runs 2026-10-25: every master -8.1 to -8.2 LUFS at -0.54 dBTP, every drop 4.0 to 4.5 LU over its build; not yet heard by the person |
| The full panel passing on every genre | 2026-10-25, all six on the first song: dnb v5, techno v5, dubstep v6, trap v6, house v7, hip-hop v3 (masters in each `sandbox\remix\friends_STYLE_vN\master`). Each: -8.1 to -8.2 LUFS, -0.54 dBTP, loudness range under 8 LU on the master, drops 4.0 to 4.5 LU over builds, no held DC, tempo on the grid, the voice measured audible in the first drop (-6 to -12 LU). The critic, asked the inverse voice question, was right on the voice in 5 of 6 and fully trusted on techno; its snare answers lean yes. Not yet heard by the person |
| Generated FL API read ops | All 176 answered live on FL 26.1.7 (`sandbox\probe_l1.json`) |
| GUI recipes: import audio clip, piano-roll script, dialogs | Run end to end on the host |
| Newtime and Newtone by GUI (fit a vocal to the beat, auto-tune it) | Girlish Type Men on the host (2026-10-29): `add_warp_markers_gui` placed 127 of 127 warp markers within 7 ms (audit pass), `newtime_quantize_save_gui` quantized and saved (marked syllables a median 6.2 ms from their 16ths, 13.6 before), `newtone_tune_save_gui` three times (robotic, middle, smooth, measured apart); `newtime_load_gui` and the whole `quantize_vocal_gui` chain have run only in parts |
| Stems by FL's Extract stems from sample (`extract_stems_gui`) | Girlish Type Men end to end by the module on the host (2026-10-29): four stems in 74 s from opening the project, bit-identical to a hand run, summing back to the mix within -37 dB; vocals 0.96 correlated with RoFormer, drums 0.996 with Demucs |
| Vocal-led layers recipe and section-long piano rolls | Girlish Type Men v6 on the host (2026-10-29): built, produced, rendered, mastered at -8.1 LUFS, -0.3 dBTP, LRA 4.8 LU, panel passed; 61 % of sung beats on chord tones (v5 49 %); not yet heard by the person |
| The FL demo study (20 songs) | Read from sandbox copies; 20 full-mix renders and 146 solo renders measured (142 with sound) (2026-10-28); keys cross-checked against the renders (12 of 20 agree, the rest reported on each page); muted clips and the master pitch found and handled |
| Variety: one song, four remixes, four formats | "the curse of curves" as house (two seeds) and afro house (two seeds), 2026-10-28: every pair differs in 9 or 10 of 11 choice categories and in its sections (`sandbox\remix\curse_compare_v2.md`); each -8.1 LUFS, -0.54 dBTP, panel passed with its contrast judge running, drops 4.2 to 4.4 LU over their builds; both house versions ask the person about drops under 1 LU over the verse before them. Not yet heard by the person |

| Serum 2 tables and sampler sounds from the song | sandbox\loops\sorry_freejak on rtxclub (2026-10-28): bass and music tables read pitch-synchronously, two formula tables, the kit and the hook on the sample oscillator, seven presets written by serum-mcp and rendered headless. The bass table plays G1 on note 31 with its own harmonic levels (0.51, 0.63, 1.0 against 0.55, 0.65, 1.0); the kick on note 60 correlates 0.9994 with the kit kick; the hook keeps its pitch on note 60 and the 16th gate runs at 16ths. Not yet heard by the person |
| Remix study: Sorry against Freejak's remix | Both tracks analysed and measured bar by bar on the host and here (2026-10-28): tempo x1.28 with the vocal's pitch and formants kept, the line map, the form as functions, drums, bass, chords, energy; `docs/remix_studies/sorry_freejak.md`. The seven options it added draft, validate and build together in the test suite. Loops and kits cut from both (drum loops of the remix average to -21 to -30 dB residual). Not yet heard by the person |

## Not proven

| Area | Why |
| --- | --- |
| A song with sounds generated for it | `match_part_sound` generated the stab, arp and sub of the Billie Jean and curse remixes (2026-10-27 and 28) and FL rendered the Serum channels from the command line; most sounds stop short of a full match (each report says what is left), and none has been judged by ear |
| The variety choices by ear | The option bank is measured and valid in tests and the first varied remixes pass the panel; whether a choice suits a song is for the person's ears. In both house versions of the curse the first two drops sit 0.6 to 1.0 LU over the verses before them (the panel asks about it): listen for whether they land |
| Genres by ear | 24 style packs (15 from the demo study, each building in tests, afro house rendered on the host); six of the first seven pass the panel by measurement; none has been heard and approved yet |
| Club loudness by ear | `apply_club_master` reaches -8 LUFS by measurement; the person has not judged a club master yet |
| Serum 2 sound design by ear | serum-mcp installed (2026-10-24); Serum 2 renders headless and a preset rebuilt as a state sounds the same as Serum's own (2026-10-26, `SERUM_MCP.md`); no generated sound has been judged in a mix |
| ACE-Step generation in the pipeline | Installed and pinned by commit; weights not pinned by revision; not used in a remix yet |
| Vision model for GUI grounding | Not chosen; adapter hook only |
| Similarity to reference tracks | `compare_to_references_ml` is built and tested; waits for the person's reference tracks |
| Source song structure | Sung songs: verses and choruses from the vocal (`songform`, checked on Friends against the published form); songs without a clear title line or vocal still fall back to the level map |
| Song-form remix by ear | The rules of 2026-10-25 (whole verses and choruses, original instrumentation, whole-line chops, MIDI chords, vocal never slower) are built and tested; the first techno remix is the test |

## Data you must provide

Targets, genre profiles and invariants ship as templates with `FILL` blanks. The loaders refuse them, so the agent cannot invent targets. One
targets file is filled from published measurements: `targets/club_release.toml` (-8 LUFS +/- 1, at most -0.5 dBTP, crest 6.5 to 11, drop over
build 3 to 5.5 LU; sources in the file). Reference tracks for the similarity judge come from the person.

## Local language model

Measured default: gemma4:12b on Ollama for the brain (Qwen3.5-9B was the pre-measurement recommendation and is the fallback). Reasoning,
sources and the VRAM budget are in `LOCAL_MODELS.md`.

## History (dated log)

### Girlish Type Men as pop dance; Whisper loops, quiet stems, the lead vocal off the pump (2026-10-29)
The person's drum remix of a spoken comic monologue (A minor, 130 bpm, unpublished) as a 3:37 pop dance record at 124 bpm (voice x0.954):
cold-open tag, the opening statement as verse 1, 4-bar pre-chorus lifts with a pitched snare roll and a tape stop, the cleanest refrain
pass as every chorus with post-chorus games, a reverb bridge, the last chorus a whole step up (the voice is spoken, so nothing clashes),
sign-off. `sandbox\remix\gtm_pop_dance_v4`: master -8.07 LUFS, -0.54 dBTP, crest 7.82; drops 3.4 to 4.8 LU over their builds; the
voice 10.3 LU under the first chorus (it was 20.4 in v1); panel passed. Fixed on the way (LESSONS rows 71 to 76): Whisper repetition loops
redone in short windows (`asrclean`); minor-key triads; a quiet vocal stem raised toward -18 dB active; the lead vocal off the pumped music
bus; pop_dance's vocal level. Not yet heard by the person.

### Open Your Heart as tech house; tech house for any song (2026-10-29)
Madonna's "Open Your Heart" (F major, 113.2 bpm) as a tech house club mix at 126 bpm (vocal x1.113, pitch and formants kept), built
from a hand-edited plan (`tools/remix_song.py --plan`): a 16-bar mix-in carried by the record's whispered opening, verse 1 on the groove,
chorus 1 as a riserchorus, a stop bar where the whisper lands drop 1, an instrumental hook drop, chorus 2 sung on drop 2, a breakdown of
the record's own keys and guitar, the climax around the title tag, a 16-bar mix-out. `sandbox\remix\oyh_tech_house_v3`: master -8.08
LUFS, -0.54 dBTP, crest 8.89; drops 3.9 to 4.3 LU over their builds, breaks about 6 LU under the drops; panel passed; tempo on the grid.
Fixed on the way (LESSONS rows 65 to 70): the "tech_house" pack is the Friends engine and ignores the variety bank, so tech house for any
song is now the grammar pack `tech_house_groove`; a hand-given key took another tonic's mode; the sound match stalled when the filter was
already open; the contrast loop read only the smallest drop contrast and lifted whole section kinds. Not yet heard by the person. The stab
still measures darker than the record (0.51x).

### One-command installer, Claude Desktop config found (2026-10-26, night)

- The servers never loaded in Claude Desktop, for two reasons found in its logs: the Store build reads
  `LocalCache\Roaming\Claude\claude_desktop_config.json` inside its package, and while it runs it writes that whole file back from
  memory on every settings change, which dropped the entries added while it ran. `install-desktop` now writes the packaged file, and only
  while Desktop is closed (`--wait`, `--restart`).
- Tested on rtxclub from the release zip into a fresh folder (`C:\cp_fresh1`, `-Models none`): uv, Python 3.11.3, packages, ffmpeg,
  setup, a second run over it (repair), then `install-desktop` into a test config, `check-servers` (fl-bridge 27 tools and 17 skills,
  studio-audio, studio-ml all start), `install-models serum serummcp`, and `doctor`.
- `install.ps1` / `install.cmd`: one command from an unzipped release does the whole install (see `docs/INSTALL.md`). New
  commands: `setup-midi` (loopMIDI ports and FL MIDI settings in the registry, FL closed), `check-servers`, `remix`;
  `doctor` now checks the Desktop registration and the MIDI registry. `tools/make_release.py` builds the zip.

### Mood packs, matched sounds in one flag, git (2026-10-26, evening)
`C:\coproducer` is a git repository (first commit c4c349c). Two style packs for moods the others did not serve: `deep_house` (sad,
romantic, bittersweet) and `nu_disco` (happy, playful, comic), with their production recipes; every pack lists its moods and
`stylepack.for_mood` ranks them in the draft plan. `match_part_sound` runs measure, generate (serum-mcp's own code through
`generate_serum_preset`, model `serummcp`), render and compare for one part, and `tools/remix_song.py --match-sounds` runs it for the
stab, arp and sub. Test remixes: Girls as nu-disco (at its own 139.4 bpm, above the pack's range, by the vocal rule) and Friends in Low
Places as deep house, both with matched sounds; the first round of matching came out dark (LESSONS 62), fixed and rebuilt as v2.

### Creative per song, generated sounds, installer (2026-10-26)
The person: same format every song is not the goal; read each song's mood, sonic space, key, bpm and lyrics and match its tone, then do
something unique; Serum sounds are generated to match the original, not fixed presets. Written down as the creative brief
(`skills/remix-from-stems/references/creative-brief.md`, mood required in song notes). Built: `measure_part_sound` and
`compare_part_sound` (the original part's envelope, brightness, harmonics, noise, width and register; a serum-mcp draft with the measured
harmonics as its wavetable), the Serum 2 channel state layout in FL (`serumstate.py`), Serum 2 played headless through pedalboard
(`render_serum_sound`, model `serum`), and the builder option `serum_states`. On rtxclub a state rebuilt from the "CP - Deep Sub" preset
file rendered the same audio as Serum's own state (difference -73 dB). Installer: `list_skills` and `read_skill` on fl-bridge for a new
chat, `install-desktop --with-serum` and `--claude-code`.

### The person's edit of the techno remix, and a second song (2026-10-26)
Their `friends_techno_produced_2.flp` against the build (`diff_flp_projects`, `anatomy.inserts`, the clip windows located in the vocal by
correlation) became defaults: flanger saved neutral and out of the recipes, the pluck chord sound and their levels, the hook as the couplet
without the slurred pickup, the intro hook, the build's answer and the last build carrying the verse into a stutter, half a second of
clip tail (LESSONS rows 40 to 47). Second song: "The Curse of Curves" (Cute Is What We Aim For, 146 bpm, F major), its form found by
repeats, built as a full house remix at its own tempo with every verse and chorus (`sandbox\remix\curse_house_v2`); the render waits for
the person to close FL.

### Song-form techno remix under the person's rules (2026-10-25, night)
The person's rules: the vocal at its own tempo, faster, or at most 6 % slower with its pitch kept (2026-10-28; was never slower); a research step; whole lines with no word cut, which lines and in what order and role chosen per remix (2026-10-28; was every verse and chorus whole), with the original's instrumentation;
whole-line chops cut through their last sound; a tested reference MIDI for the chords; Serum 2 from their own sounds. Built as `songform`,
`midiref`, `find_song_clues`, `write_song_notes`, `tools/fetch_reference_midi.py`, plus fixes found on the real audio (Whisper window
copies, a stretched first word over a held note, a final s lost in word mode, phrase ends running into the next word, the tempo check
against the pack's bpm). Host: `sandbox\remix\friends_techno_song_v2` at 126 bpm (vocal x1.161), Serum sub, chords and arp cloned from
the approved tech-house v15, the MIDI World file accepted (roots agree on 74% of 72 bars); master -8.18 LUFS, -0.54 dBTP, crest 6.66,
loudness range 5.88; tempo check 93% of beats on the plan's grid; panel passed (critic untrusted at 1 of 3). v1 of the same run had the cut
faults above and is superseded. Not yet: the person's ear on it.

### Any song, six genres, club master, panel (2026-10-25)
New model environments `mir` (beat_this, torchcrepe, MuQ-MuLan) and `sep` (audio-separator with Mel-Band RoFormer), every checkpoint pinned by
hash. New library: `beatgrid`, `melody`, `intake`, `stylepack`, `remixaudio`, `mastering`, `panel`; style packs in `styles/`; production
recipes for techno, dubstep, dnb and trap. New modules: `build_song_analysis`, `separate_stems_hq`, `detect_beats_ml`, `transcribe_vocal_melody`,
`prepare_remix_audio`, `apply_club_master`, `check_remix_panel`, `compare_to_references_ml`; 212 more generated L1 ops. New tools:
`tools/remix_song.py`, `tools/probe_l1.py`. Host: Friends intake and a dubstep remix end to end (numbers above). Not yet: any genre heard by the
person, a second song, the live L1 probe with the corrected FL-side script.

### Import recipe confirmed (2026-10-20)
import_audio_clip_gui ran end to end twice in a row on the real machine: ADD menu, Audio Clip, file button found from the window rect, Open sound dialog, path typed, clip loaded, floating window closed, no dialog left. The recipe is now verified true. Known limits: a stale Audio Clip window from an earlier failed run makes the window lookup ambiguous; the clip is not placed in the playlist automatically yet (done by hand so far), and it adds a new channel per run.

### Editable-first remix build (2026-10-22)
Standing rule recorded in `docs/PRODUCTION_POLICY.md` and the `editable-first` skill: drums as sampler channels plus patterns, synths and bass as plugin channels plus piano-roll notes, audio clips only for vocals, FX, long textures, resamples or the user's own recordings. New library code: `coproducer.flpfile` (FLP reader and patcher, layout in `docs/FLP_FORMAT.md`), `coproducer.oneshots` (drum and FX voices), `coproducer.drumplan` (section-aware drum plan and FX cues), `coproducer.tension` (swells, gated sub, arps, kick-aware truncation), plus `tools/flp_tool.py`. Tests: `tests/test_flpfile.py`, `tests/test_editable_parts.py`, `tests/test_flp_tool.py`. Verified on the DTP project: a patched file round-trips and FL opened and rendered it. Not yet verified by ear: the Trance pluck arp and the Deep patch tonality.

### Vocal pass (2026-10-22)
New library: `coproducer.vocalfx` (high-pass, noise reduction, tone, de-ess, look-ahead compressor, parallel saturation, level kept), `coproducer.vocalclips` (audio clip offsets, onset search, trim and grid snap plan), `Flp.map_playlist`. New tools: `tools/vocal_clean.py`, `tools/vocal_patch.py`, `tools/transcribe_vocals.py`. Tests: `tests/test_vocalfx.py`, `tests/test_vocalclips.py`. Run on the DTP project: 40 vocal channels pointed at cleaned files, 30 clips had a lead-in trimmed, 24 clips moved onto the sixteenth grid, vocal level against the mix rose 2 to 6 dB (build section 6 dB), toms down about 3.7 dB at their hits, riser sweeps rebuilt (`FX_v1.wav`). Final: minus 13.95 LUFS, minus 1.56 dBTP. Not done: word-level re-timing of the long phrases (Lil weed, Libertycaps, Lotsofgoodfungi), and no voice cloning (the main recording is a real person's speech; see `docs/PRODUCTION_POLICY.md`).

### Mix tooling and mix pass (2026-10-22)
New modules: `list_effect_slots`, `set_effect_active_verified`, `set_eq_db_verified`, plus L1 ops for `mixer.getPluginMuteState` and `getPluginMixLevel` and their setters. New library: `coproducer.mixtools`, `coproducer.synthmatch`. New tools: `tools/hit_meter.py`, `tools/mix_compare.py`, `tools/mix_iter.py`, `tools/synth_match.py`, `tools/spec_match.py`. Measured: effect slot state 1 means processing, mixer EQ is about 31 dB per raw unit, a bypassed slot still reads back as verified. DTP mix pass: minus 13.75 LUFS, minus 1.79 dBTP, air minus 13.7 dB (see `docs/WORKED_EXAMPLE_DTP.md`). The new L1 setters and `mix_iter.py` are written and unit tested but not yet run end to end on the live machine.


### Claude Desktop install option (2026-10-22)
`coproducer install-desktop` (`cli/desktop_cmd.py`) merges the servers into `claude_desktop_config.json` with a backup, `--dry-run`, `--remove`, and an opt-in default of three servers (desktop-control needs `--with-desktop-control`). `coproducer setup` asks once at the end (`--desktop` / `--no-desktop`). Tests: `tests/test_desktop_cmd.py` (path per OS, merge keeps other servers, idempotent, bad JSON refused, prompt). A server started with the exact generated command from a different working directory answered `initialize` and `tools/list` over stdio. Not yet verified: Claude Desktop itself listing the servers on your machine.

### Automation clips (2026-10-22)

`coproducer.automation` builds automation clips inside an FLP (points, link to a mixer or plugin parameter, playlist item) and lists or removes
them. Format and value maps are in `docs/FLP_FORMAT.md`, "Automation clips". Render-proven on track volume, master volume, built-in EQ gain and a
Fruity Limiter parameter; unit tests compare the encoder with FL's own bytes. Limits: inject only into a project FL saved itself; plugin slots
above the first are untested.

Three modules expose it (L3, fl-bridge, phase P4): `add_automation_clip` (targets: track volume, pan, stereo separation, built-in EQ gain, frequency and Q, plugin parameter in any slot (slot k is link sub k, read from FL's own saves 2026-10-25); curves: points, ramp or duck; units: knob or dB for a volume), `list_automation_clips`, `remove_automation_clip`. They work on a project inside the sandbox, keep a one-time `<name>.pre_automation.flp`, refuse a project FL did not save itself, and read the clip back after saving. `coproducer.fxbed` plus `tools/fx_bed.py` render an FX bed (impacts, air sweeps, risers) from a cue plan with no baked ducking.

Fix found on the DTP project (2026-10-22): moving a project's existing remote links without their formula text (event 230) made FL's render hang; links now move as pairs (see `docs/FLP_FORMAT.md`). DTP A/B copy `Notorious_DTP_28_auto.flp` renders at the same loudness and within 0.2 dB per band as the current project (see `docs/WORKED_EXAMPLE_DTP.md`, "Automation pass").

Planned: the stem remix pipeline (FL stem separation, vocal chops, instruments to piano roll, drums to channel rack, Newtone, Edison) is laid out step by step with status in `docs/STEM_REMIX_PIPELINE.md`.

### Stem remix: Friends in Low Places, v12 (2026-10-23, save point)

Built entirely from FL's four stems: 124 bpm, A, 104 bars, editable drums, bass, stabs and arp, ten vocal chops (six with echo), three long vocal phrase clips, one FX bed audio clip. The user listened to v12 and approved it. Render: minus 16.4 LUFS integrated, peak minus 2.86 dBFS, no clipped samples. Worked example, numbers and weak spots: `WORKED_EXAMPLE_FRIENDS.md`. How to rebuild it: `HANDOFF.md`. Vocal cutting rules and their history: `VOCAL_CHOP_RECIPE.md`.

New since the DTP work: `coproducer.remixplan` (the arrangement as data, `chop_conflicts`), `coproducer.vocalchops` and `coproducer.cutrefine` (cut points by signal, `final_s` for sung final s and z), `tools/build_techhouse.py`, `tools/techhouse_audio.py`, `tools/refine_cuts.py`, `tools/render_report.py`, `tools/queue_runner.ps1` (host job queue), `tools/gen_file_map.py` (writes `FILE_MAP.md`). New modules (L4, read only, phase P5): `check_vocal_edges`, `find_final_s_end`. New skill reference: `skills/editable-first/references/vocal-chops.md`.

Verified: unit tests for every rule above on synthetic voices; the whole chain ran on the host (Whisper large-v3 on the GPU, FL render through the command line) and the result was heard by the user. Not verified: the recognisers' reading of the weakest cuts (`bluesaway`, `blues` start, `pickup`, the z of `friends`); anything about a second song; Serum 2 (installed, the Serum MCP is audited but not run, see `SERUM_MCP.md`).

Next, in order: Serum 2 sounds for stabs, arp and sub; a designed gabber stab for drop 2; the same pipeline on another song (needs song analysis and automatic chop planning, `STEM_REMIX_PIPELINE.md`); the original-element reminiscence recipe.

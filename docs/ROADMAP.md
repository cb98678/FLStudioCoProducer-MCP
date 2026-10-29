# Roadmap: from one tech-house remix to a full co-producer

Written 2026-10-25 at the person's request to pause and realign: pin every version, review the code for fragility and drift from the plans,
research what we use against current documentation and other MCPs, and list what is missing. Facts from the web are cited at the end; facts from
this repo name the file. Anything not verified says so.

## Remix studies (2026-10-28)

The person is bringing originals with professional remixes. The first (Sorry, Freejak) is done: docs/remix_studies, REMIX_RESEARCH.md
section 13. Built: per-pass form functions, re-harmonization with two chords a bar, the form's standard tempo, loop and kit extraction
and search. Next, in order: the next pairs the person brings (each adds options sourced to it); a vocal clarity check in the panel (house A's
wash); a subtraction check in the panel (a break or stop at least every 16 to 32 bars, Freejak's lesson); a vocal-fit check for a
re-harmonization (the vocal's notes against each chord) so it can be offered, not only locked; rolling and wobbly bass options for house
B's drop.

## Serum 2 wavetables and sampler sounds (2026-10-28)

Built: pitch-synchronous tables from a song's own notes, formula tables, sampler cuts with pitch and loop, serum-mcp spec parts
(skill `serum-wavetables`). Next: one FL load of a project whose Serum channel plays an installed table and a sampled hook, with the
person; check in Serum's UI that a macro used as an aux source scales the pluck (describe_preset does not show it); tables per section
(a table that moves from the verse's bass to the drop's); a vowel table from a held sung note as an instrument timbre (no voice cloning);
`--match-sounds` using a table instead of measured harmonics when the stem holds a clean held note.

## Variety from the FL demo songs (2026-10-28)

The person: every remix had the same format. The twenty FL Studio 2026 demo songs were studied (files, full renders, solo renders of their
main parts) and turned into an option bank, fifteen style packs and a variety engine (`docs/DEMO_STUDY.md`, skill `creative-variety`,
`docs/HANDOFF.md`). Still open: synth parameter values read live through the bridge (`snapshot_project_params` needs FL open with each demo
loaded, with the person's permission), odd-meter bars and tempo changes built by the engine (Secret Agent Rendezvous turns with a 7/4 and a
6/4 bar and drops from 120 to 110 bpm; form.cinematic_cues leaves them as a manual step after the build), tempo-automated demos measured
only at their first tempo, and the person's ears on the first varied remixes.

## Progress since the realignment (2026-10-25, afternoon)

The person gave the go-ahead to build everything below and to download what it needs. Built and checked on the host the same day:

| Piece | What it is | Proven |
| --- | --- | --- |
| Analysis stack | `models/envs/mir` (beat_this 1.1.0, torchcrepe 0.0.24, MuQ 0.1.0 with transformers 4.48.3) and `models/envs/sep` (audio-separator 0.47.1, Mel-Band RoFormer vocals); every checkpoint pinned by hash, Hugging Face snapshots pinned by revision; Demucs checkpoints pinned too | Friends: 108.504 bpm in 4/4 against 108.478 by hand, drum entrance 27.34 s against 27.3085, RoFormer vocal 9.6 dB SDR against the stem the test mix was summed from |
| `build_song_analysis` | One call from a song file to stems, bar grid, words, melody, bass roots, a key vote (bass, melody, mix) and the song's sections, written as the files `build_song_plan` reads | Friends end to end on the host: key A major by bass and mix (the melody alone said B minor and was outvoted) |
| Style packs | `styles/*.json`: house, tech house (the old engine), techno, dubstep, dnb, trap, each with tempo strategy, sections, drum and bass grammar, kit, bass sample, production recipe, targets, sources; skill `genre-styles` | Every pack builds a project from the first song's plan (tests); dubstep built, produced, rendered and mastered on the host |
| `prepare_remix_audio`, `tools/remix_song.py` | The audio prep as a module for any plan and style; one command for the whole pipeline with a report | Dubstep run end to end on the host |
| Contrast loop | Section gains scaled until every drop sits 3 to 5.5 LU over its build, aiming from the measured slope | First pass overshot (1.9 to 9.2 LU at scale 1); fixed to aim from the slope; rerun queued |
| `apply_club_master` | Soft clipper into a look-ahead true-peak limiter to `targets/club_release.toml` (-8 LUFS +/- 1, at most -0.5 dBTP, crest at least 6.5), measured again independently | Dubstep master: -8.09 LUFS, -0.54 dBTP, crest 9.1 |
| `check_remix_panel`, `compare_to_references_ml` | The evaluation panel (src/coproducer/panel.py): dsp and plan judges trusted, the critic graded on questions the style answers, similarity to references against the original as a baseline | Tests; the host run waits for the person's reference tracks |
| FL control | 319 L1 ops from the whole inventory (107 before), keystroke-type ui calls left out on purpose; `tools/probe_l1.py` calls every read op live | First probe ran with the old FL-side script (59 of 176 answered, the rest unknown to it); the new script is installed and the probe is queued again |
| Reference profiles | `build_reference_profile`: the person's reference tracks per genre (`sandbox\\references\\STYLE`) measured into a profile (loudness, crest, loudness range, correlation, third-octave tonal balance with its spread) and a targets file of their own; `apply_club_master` moves the master broadly toward their tonal balance; the panel judges tonal balance and MuQ similarity against them; `remix_song.py --finish` re-masters an earlier run without rendering | Tests; waits for the person's tracks |
| DC guard | `measure_dc_offset` in every measure report and a [dc] limit in the club targets; the master removes DC and cuts a dead tail; the panel flags DC in the mixdown as a recipe fault | House, techno, dnb and trap renders held a DC offset after the song ended and ran 33 s long; the cause was the high-pass sweep resting at cutoff 0, now 0.01 (measured: no held offset, sub within 0.01 dB) |
| Tempo check by grid | `beatgrid.line_tempo` numbers beats by the best-fitting grid instead of counting gaps; `grid_fit` checks a known tempo directly | Three host renders now read 124.001, 139.992 and 174.018 (they read 124.2, 142.9, 190.8) |
| The person's remix rules (late evening) | Vocal at its own tempo or faster (`stylepack.pick_tempo`, validated in `songplan`); research step (`find_song_clues`, `write_song_notes`, no lyrics from the web); song-form arrangement with every verse and chorus whole and the original's instrumentation (`songform`); whole-line chops cut through their last sound (`remixaudio.whole_end`); reference MIDI tested against the record for chords and strum (`midiref`, `tools/fetch_reference_midi.py`); Serum 2 from the person's own sounds | Tests; Friends' form found from its vocal (verse, chorus, solo, verse, chorus, three closing choruses) matches the published account; the MIDI World file is accepted (roots agree on 74% of 72 bars); one techno remix queued as the first test |
| Fixes found on the way | beat tracker tempo through missed beats (a half-time render read 110.7 bpm, 140 after the fix), tracker steadiness flag, render length as a second tempo check, the FL-side install path when the config's data_dir is empty | Tests and host runs |

All six genres pass the panel on the first song (2026-10-25, `STATUS.md`). Still open from section 9: a structure model for songs whose form the vocal does not show (the vocal-based form in `songform` covers sung songs; the level-based map is weak on a country mix), PPQ scaling, non-4/4 sources, Serum 2 palettes per genre, the bridge daemon question, ACE-Step in the pipeline, rock.

## 1. The goal, in the person's words (2026-10-25)

Drop a song in. Split it into stems. Examine every part of it. Make the remix the person asks for: a club mix, dubstep, techno, rock, rap or
anything else. Run it past the local model evaluators and cross-check them against each other. Let local models make what Claude cannot (audio).
Run the whole process end to end until every part is done, and present a remix that sonically matches the most popular club mixes of today.
FL Studio control should be as complete as the software allows.

## 2. Where we stand against that goal

| Stage | What exists | What is missing |
| --- | --- | --- |
| 1. Intake | FL's "Extract stems" through the GUI; `separate_stems` (Demucs `htdemucs`); `copy_project_to_sandbox` | One call that takes an audio file and returns a sandbox project, stems and an analysis file. FL 2026's own "Remix a song" tool is not used. No RoFormer or SCNet separation. |
| 2. Analysis | `estimate_bpm_dsp`, `estimate_key_dsp`, `detect_sections_dsp`, Whisper word times (pinned), downbeat from drum hits, bass roots | A beat and downbeat tracker for songs that drift; a structure model (verse, chorus, bridge); vocal melody to MIDI; chords beyond bass roots; time signatures other than 4/4. |
| 3. Plan | `build_song_plan` drafts a tech-house plan (124 bpm, nine sections, chops from repeated lyrics) | A planner driven by a genre: tempo strategy (keep, half time, double time), section template, drum and bass grammar, harmonic treatment, chop density. `remixplan.py` is tech-house code; `genre_profiles/*.toml` are unfilled templates. |
| 4. Build | `build_remix_project`: sampler drums with patterns, Sytrus or Serum channels with notes, chops, stretched vocal, FX bed, markers, house standard | Sound palettes per genre (Serum 2 presets, FLEX, FL stock fallbacks), 808s, guitars and live-feel drums for rock, generated one-shots. |
| 5. Produce | `apply_production_recipe` with `club_house` (buses, chains, pump, 12 automation moves and 3 synth FX at section changes, section gains) | Recipes for other genres (dubstep half-bar mutes and bass switch-ups, techno rumble and long filters, DnB, trap rolls). |
| 6. Generate | ACE-Step 1.5 (`generate_audio`, `repaint_section`, `generate_cover`), the DSP FX bed, 3x Osc transition synths | ACE-Step is not wired into a remix; no one-shot generation; no search of the person's sample library. |
| 7. Mix | Solo-render gain staging against an approved profile, section contrast, EQ and effect tools, masking measure | Balance profiles per genre measured from references. |
| 8. Master | Maximus on the master against `targets/club_tech_house.toml`; approved v16 at -13.0 LUFS | Today's club loudness (section 7); a clipper stage; targets per genre. |
| 9. Evaluate | DSP measures, `compare_to_reference`, `critique_audio` (Music Flamingo), `critique_audio_dsp` | A panel that cross-checks its voices (section 8); similarity to genre references; pairwise A/B. |
| 10. Present | Render, MP3, `build_ab_package` | One package: club WAV, streaming master, stems, the editable project and a report of what changed with numbers against the references. |

## 3. Code review, 2026-10-25

`ruff check` (rules F, E9, B, PLE) over `src`, `tools`, `modules`, `fl_side` and `tests` started at about 270 findings; 215 were names the generated FL-side
script defines (`_run`, `_check_args`, `device`, `ui`) in L1 op bodies and the FL template, now ignored for those files in `pyproject.toml`. The
rest were fixed. The full suite passes (about 1150 tests).

### Fixed in this pass

| Finding | Severity | Fix |
| --- | --- | --- |
| `render_via_cli` and `render_folder_via_cli` started a command-line render while FL was open. FL hands the job to the running copy and writes nothing (measured 2026-10-18), and `Procs.fl_count` returned 0 when `tasklist` failed, so an unknown state read as "closed". | High | Both refuse while FL runs (`E_PENDING_HUMAN`); an unreadable process list counts as running. Test added. |
| `render_with_restart` closed and reopened FL on its own (autonomy A2), against the standing rule. | High | Now A1: a run asks the person each time; the probe commands, which the person starts by hand, carry that approval. Session approvals may hold a set of modules. |
| A production move that failed part way (a chain that placed two of four effects) left its edits in the project, and an unexpected error stopped the whole pass. | Medium | Each move runs on a snapshot and is rolled back on failure; unexpected errors are logged with their type and the pass goes on. Test added. |
| `Flp.save` wrote in place (an interrupted save could leave half a project) and accepted files the patchers would damage. | Medium | Writes `.part` then replaces; refuses PPQ other than 96 (every tick constant assumes 96) and saves older than FL 21. |
| Music Flamingo loaded the hub's current snapshot instead of the pinned revision. | Medium | Loads the revision `install-models` downloads; a test ties the two. |
| Whisper tools named an unmanaged interpreter (`C:\Python311`). | Low | They name the pinned critique environment and pass the pinned revision (verified on the host). |
| Build backend pinned as a range (`setuptools>=68`). | Low | Exact pin, tested like the other pins. |
| Lint: unused imports and variable, a raw right-to-left control character in a test string, `raise` without `from`, a closure over a loop variable. | Low | Fixed. |
| `HANDOFF.md` and `STATUS.md` were a day stale and said `render_via_cli` kills FL; two skills said a render closes FL. | Low | Rewritten. |

### Open findings

| Finding | Why it matters for "any song" | Proposal |
| --- | --- | --- |
| Every tick constant assumes 4/4 and PPQ 96 (`TICKS_PER_BAR = 384`). `Flp.save` now refuses other PPQs, but FL's own factory templates EDM-House and Electro were saved by FL 20.7 at PPQ 48 (copies in `sandbox\offsong`; the host check refused EDM-House). | A project the person starts from a template, a 3/4 or 6/8 source, or a song with odd bars would be refused or misplaced. | Scale every tick by the file's PPQ; analysis reports the meter and bar lines; the remix grid stays 4/4 and source audio is mapped bar by bar. |
| The event-172 length rule in `flpfile._events` is tuned to FL 26.1.7. | A later FL build could change it; the round-trip check would not notice a wrong but consistent split. | A fixture per FL build and a check of the saving FL version before patching. |
| Each process opens the loopMIDI ports itself. | Untested whether two processes (an MCP server and `call_module`) can share them. `flstudio-mcp` runs one daemon that owns the port and serves clients over TCP. | Probe on the host; if they clash, one bridge daemon. |
| Recipes, plugins and the effect library resolve from the source tree (`parents[2]`). | A non-editable install would not find them. | Package data or a `[paths]` setting. |
| ACE-Step weights download on first use, not pinned by revision; Ollama tags are mutable (we record the id and warn). | Reproducibility. | Pre-download ACE-Step checkpoints at a recorded revision (needs approval, several GB). |
| The audio critic hallucinates. The host run `queue\done\04_critique.out.txt` describes an intro, breakdown, build-up and drop in a 10.01 s clip. | Critic text cannot verify anything. | Section 8. |
| `sectiongain.DEFAULT_ROLE_GAINS` knows only build and break; songs with Verse and Chorus markers get no section gains. | Pop-structured plans. | Kinds per genre in the style pack. |

### Drift from the plans

- The vision's first success criterion (`plan/01-vision-and-spec.md`, S-01) is a techno track returned as dubstep with the same key and a
  melody similarity above the person's threshold. Nothing outside house has been built, and no melody-similarity invariant runs.
- The genre profiles (`genre_profiles/techno.toml`, `dubstep.toml`) still hold `FILL`, so the loaders refuse them, as designed.
- `targets/club_tech_house.toml` asks -11.5 LUFS with true peak at most -2.0 dBTP and crest at least 8, and the person approved -13.0 for
  contrast. Today's club masters measure -7 to -9 LUFS with true peaks often above 0 dBTP (section 7). The targets cannot meet "sonically
  matches today's club mixes" as written.

## 4. FL Studio control

FL's Python API has 365 functions in the stubs inventory we generated from (FL Studio API Stubs 37.0.1, August 2024; the IL-Group repository now
calls itself unmaintained and points to the online manual and Maddy Guthridge's stubs). FL 2025 and 2026 added more, per the manual's change
log: `setPatternLength` and `incrementPatternLength`, swing get and set, clearing a pattern, `movePattern`, tempo as a float and time base and
numerator setters, `device.releaseCC`, showing and focusing the plugin picker, HW_Dirty undo flags, a Graph Editor refresh flag, an "is this FPC
pad empty" call and `duplicateMidiPatternData`. The host reports API level 45.

We wrap 107 of the 365 (29%) plus the 2026 pattern length, swing and clear calls. By module: mixer 33 of 74, channels 20 of 50, patterns 13 of
28, transport 10 of 20, playlist 9 of 41, plugins 8 of 13, arrangement 4 of 9, general 4 of 24, device 2 of 34, ui 4 of 71.

What the missing groups would unlock, in order of value:

| Group | Functions | Unlocks |
| --- | --- | --- |
| Any parameter by REC event | `general.processRECEvent`, `mixer.getEventValue`, `mixer.automateEvent`, `mixer.remoteFindEventValue`, `mixer.getEventIDName` | Read and write almost any parameter live (channel volume, pan, pitch, filter, sends, EQ, plugin knobs) with readback, without a file patch and a reopen. |
| Undo history | `general.undoUp`, `undoDown`, `restoreUndoLevel`, `getUndoHistory*` | Reliable rollback inside the person's open session. |
| Step sequencer and channels | `channels.setGridBit`, `getGridBit`, `setStepParameterByIndex`, `quickQuantize`, `selectChannel`, `showEditor`, `getChannelPitch`, `setChannelPitch` | Drum patterns and quantize live; open a plugin's editor for the person. |
| Patterns | `patterns.clonePattern`, `setPatternColor`, pattern groups | Variations of a pattern live. |
| Mixer odds | `mixer.linkTrackToChannel`, `setSlotColor`, `enableTrackSlots`, `revTrackPolarity`, `swapTrackChannels`, `getTrackPluginId` | Routing and phase checks live. |
| Presets | `plugins.nextPreset`, `prevPreset`, `getPresetCount`, `getName` | Audition presets: step, render a bar, score, keep the best. |
| Browser | `ui.navigateBrowser`, `selectBrowserMenuItem`, `previewBrowserMenuItem`, `getFocusedNodeCaption`, `getFocusedNodeFileType` | Possibly load samples and presets from FL's browser without screenshots (Ableton MCP loads instruments from Live's browser). To probe. |

The API still cannot add plugins, place playlist clips, import audio, save or render (our probes; the other FL MCPs say the same). We do those
through the project file (playlist, automation clips, effect injection, routing) and GUI recipes, which no other FL MCP we found does.

FL 2026 features worth using: "Remix a song" in the Tools menu (stem separation of a playlist track and a remix project at the right tempo), the
Chord Panel in the piano roll (chord detection), Transmitter (splits transient and sustain to separate mixer tracks; All Plugins Edition, so probably not on this Producer Edition), the compressor's sidechain
input (25.2), Fruity Slicer 2, the rebuilt FLEX with a free 200-preset library, Audio Clip Gain. Gopher can now act on a project and write piano
roll scripts; the docs describe it only from its own chat, with no script API.

## 5. Other MCPs: what they do that we do not

| MCP | Notable | Adopt |
| --- | --- | --- |
| `rosasynthesiz/flstudio-mcp` (FL, 67 tools) | "Mix Doctor" proposes fixes one at a time with approval and rollback; full-song peak watching; reference matching; melody to MIDI with CREPE; arrangement export as MIDI; six live MCP resources (project, mixer, transport, channels, patterns, status); a daemon that owns the MIDI port | MCP resources, the port daemon, vocal melody to MIDI, MIDI export |
| `karl-andres/fl-studio-mcp` (FL, 57 tools) | Step-sequencer bits, live note triggering to audition, preset next and previous, playback speed | Step bits, audition, preset cycling |
| `kaupau/flai-mcp` (FL) | SysEx JSON bridge like ours; clone, rename and recolour patterns | `clonePattern` |
| `ahujasid/ableton-mcp` (Ableton) | Loads instruments and effects from the browser; builds arrangements by section | Browser loading (to probe in FL) |
| `xdarkzx/reaper-mcp` (REAPER, 173 tools) | 35 genre style profiles for mix and master; an inventory of installed plugins; a sample library scan (tempo, key and role from file names); chord progression text to voiced MIDI; drum step notation; region checks for silence and clicks | Genre profiles, plugin inventory, sample index, click checks |
| `bonfire-systems/reaper-mcp` (REAPER, 60 tools) | Track templates with their effects and routing; stem renders; an analysis suite | We have equivalents |

Where we are ahead of all of them: editing the project file itself, readback on every write, render and measure loops, the sandbox and autonomy
rules, gain staging from solo renders, section contrast, editable builds from stems and recipes learned from a reference project.

## 6. Models for each job (checked 2026-10-25)

| Job | Now | Best open option found | Recommendation |
| --- | --- | --- | --- |
| Separation | FL's stems; Demucs `htdemucs` | On MVSEP's multisong set, BS-RoFormer models lead for vocals (12.33 dB SDR, MVSEP's own July 2026 model); among open architectures SCNet XL leads bass, drums and other; `htdemucs_ft` is the best Demucs and slow. `python-audio-separator` 0.47.0 runs MDXC and RoFormer checkpoints. | Vocals with a public Mel-Band or BS-RoFormer checkpoint, the rest with `htdemucs_ft`; compare against FL's stems on the same song by bleed and by ear before switching. Check each checkpoint's licence. |
| Beats and downbeats | Onsets of the drum stem | `beat_this` (CPJKU, ISMIR 2024): MIT code and weights, `pip install beat-this`, about 78 MB | Add. |
| Structure | `detect_sections_dsp` | SongFormer (2025): intro, verse, chorus, bridge, inst, outro, silence, pre-chorus; ACC 0.807 against All-In-One's 0.740 on HarmonixSet; code CC-BY-4.0, weights licence not stated | Add SongFormer or All-In-One after checking weights licences. |
| Lyrics and word times | Whisper large-v3, pinned | | Keep. |
| Vocal melody to MIDI | None (Basic Pitch is polyphonic) | RMVPE (vocal pitch in polyphonic music), FCPE, CREPE | Add RMVPE: it keeps the melody when chords change, and it is the melody-similarity check S-01 needs. |
| Chords | Bass roots | No strong open chord model found; Music Flamingo claims chord tracking; FL 2026's Chord Panel detects chords in the piano roll | Roots plus chroma of the instrument stem, checked by ear; probe the Chord Panel. |
| Generation | ACE-Step 1.5 (2B, pinned commit) | ACE-Step 1.5 XL (4B, released 2026-04-02, MIT): repaint, cover, reference-style guidance, Vocal2BGM, multi-track "add layer", LoRA from 8 songs in about an hour on a 3090; about 20 GB without offload | Textures, one-shot banks, parts no synth gives us (a rock guitar riff), a genre bed under the vocal to audition a direction; later a LoRA on the person's approved remixes. |
| Time stretch | Resampling; FL's stretch modes | Rubber Band 4.0.0 with the R3 engine (GPL or commercial) | Vocals moved to 140 or 174; or FL's own clip stretch, which stays editable. |
| Critic | Music Flamingo 2601 | Still the strongest open music critic by its paper (MuChoMusic 74.6 against Qwen3-Omni's 52.1), and it hallucinated on our host run | One voice of several, asked narrow questions with the measured facts in the prompt. |
| Quality score | None | Audiobox Aesthetics: stable scores that a review found do not track human judgement of music | A tiebreaker at most; never a gate. |
| Similarity to references | `compare_to_reference` (spectrum, loudness) | MuQ-MuLan matched perceived similarity best in a 2026 study (72.4% and 96.6% against CLAP's 71.9% and 89.3%) | Add a per-section "sounds like the references" score. |
| Brain | gemma4:12b on Ollama | | Keep. |

On the 3090 (24 GB) the scheduler keeps one model resident: Music Flamingo needs about 16 GB in bf16 and ACE-Step XL about 20 GB without
offload, so the brain unloads for them.

## 7. Today's club sound

### Loudness

- iZotope, April 2025, ten top Billboard Dance/Electronic songs from lossless files: average -8.3 LUFS integrated (range -6.2 to -11.3),
  short-term average -6.1, loudness range average 6.6 LU, true peaks mostly above 0 dBTP (up to +1.5).
- TrackSensei, June 2026, 563 released house and techno masters: median house -8.0 LUFS (middle half -9.0 to -7.1), tech house -8.8,
  peak-time techno -7.7, hard techno -6.9; the median true peak is above 0 dBTP in every style.
- Ours: v16 at -13.0 LUFS integrated, true peak -2.88 dBTP, crest 8.89, about 4 to 5 LU quieter than those releases.

Contrast and loudness can both hold: keep the section gains and drive the master harder through a clipper before the limiter, so the drops sit
near -6 to -7 LUFS short-term. That needs the person's call on a new target. Proposal: a club master at -8 LUFS integrated (+/- 1), true peak at
most -0.5 dBTP on the exported file, drops 3 to 5 LU over their builds, plus a separate streaming master. Then listen.

### Genre recipe cards (starting points; the numbers get checked against references the person picks)

| Genre | Tempo | Drums | Bass and harmony | Arrangement | Source |
| --- | --- | --- | --- | --- | --- |
| House, tech house (built) | 124 to 128 | Four on the floor, clap on 2 and 4, off-beat open hat | Rolling or reese bass, off-beat stabs | 16 and 32 bar phrases, build into drop | this repo |
| Techno | 126 to 132 classic; peak time trending 140 to 146 (an opinion piece reading a December 2025 Beatport chart) | Layered kick with saturation, closed and open hats, rides in the drops, sparse claps | Simple 16th bass sidechained to the kick, a 1 or 2 bar riff with filter LFOs | Long filter automation, noise risers, sub impact before the drop | Beatportal (2024), Midnight Rebels |
| Dubstep | About 140, half time | Kick on 1, snare on 3, sparse hats, fills at phrase ends | Clean mono sub kept apart from mid-bass growls moved by LFOs on filter or wavetable | Something changes every 4 to 8 bars, half-bar mutes, reverb tails cut at the drop, impacts | Point Blank |
| Drum and bass | 174 | Kick on 1 and the "and" of 3, snare on 2 and 4, ghost snares | Sine sub low-passed near 80 Hz, reese from two detuned saws, FM mids | Long intro (about 32 bars), drop near one minute, a second drop with variation | Beatportal (2025) |
| Trap and rap | 140 to 180, felt at half | 808 tuned to the key with a long decay, 16th and 32nd hats with triplets and rolls, snare on 3 | Simple dark bass or the 808 alone, space in the middle for the vocal | Sections made by dropping drums in and out, long intros | TIDAL (2020, older; check against current references) |
| Rock | The song's own tempo or a little faster | Live-feel drums, less quantized | Distorted guitars and bass guitar (generated, or the person's plugins) | Verse and chorus form kept | not researched yet |

A rap mix of a sung song can mean an instrumental beat under the original vocal or a new verse. We will not clone a real singer's voice
(`PRODUCTION_POLICY.md`); a new verse would be recorded by the person.

## 8. Checks and balances

1. Numbers come only from DSP on a render (V3). A model never reports a number.
2. Each judgement has independent voices: DSP against the genre references (loudness, band balance, crest, stereo, section contrast, pump
   depth); embedding similarity to the references per section; the audio critic asked narrow yes-or-no questions about a short excerpt, given
   the measured facts, twice on different excerpts. When they agree, act; when they disagree, ask the person.
3. A critic statement that contradicts a fact is discarded (a 10 s clip has no intro, breakdown and drop).
4. Pairwise beats absolute: "which of A and B has the tighter low end", not "rate this 1 to 10".
5. A loop stops after a set number of passes, or as soon as a change moves the measure the wrong way, and asks.
6. The person is the V1 gate at three points: the plan (genre, chops), the first full render, the master.

## 9. Build order (proposed)

1. **Any song, house first.** `intake_song`: copy to the sandbox, separate (FL's "Remix a song" through the GUI, or RoFormer plus Demucs),
   `beat_this`, a structure model, Whisper words, RMVPE vocal melody, key and meter, all in one analysis file. Then a second song end to end.
2. **Genre system.** Style packs: the genre profiles filled from cited numbers and the person's reference tracks; the arranger driven by the
   pack (section template, drum and bass grammar, harmonic rhythm, chop density, tempo strategy); production recipes and sound palettes per
   genre; targets per genre measured from references. Dubstep and techno first (S-01), then DnB and trap.
3. **Evaluation panel.** Reference similarity, the critic with facts in the prompt, an aggregator that asks on disagreement.
4. **FL control breadth.** Generate the remaining L1 ops in tiers (read-only first), the REC-event write path with readback, undo-history
   rollback, a browser-loading probe, MCP resources, the bridge daemon if the ports clash.
5. **Club master.** Clipper plus limiter with contrast kept; club and streaming exports; stems; the report.
6. **End to end.** A `remix_song(song, genre)` plan template in the orchestrator that runs unattended between the V1 gates.

## 10. What the person can help with

1. A second song (WAV or MP3), ideally a pop hit you would play out.
2. Three to five reference tracks for each genre you want first, lossless if you own them. We measure them for targets and similarity.
3. The club loudness target (proposal in section 7).
4. The genre order (proposal: a second house song, then dubstep and techno).
5. Your Serum 2 presets by role for each genre, and a list of the third-party plugins you own.
6. Approval of downloads, each with its exact size shown before anything is fetched: `beat_this`, a structure model and its weights, a
   RoFormer checkpoint, MuQ-MuLan, Rubber Band, ACE-Step XL weights.
7. Listening at the V1 gates.
8. What a "rap mix" should be: a beat under the original vocal, or a verse you record.

## Sources

- FL Studio change log (beta manual, What's New): https://www.image-line.com/fl-studio-learning/fl-studio-beta-online-manual/html/WhatsNew.htm
- FL Studio 2026 release page: https://www.image-line.com/fl-studio/release/2026
- FL Studio 2026.1.4 release thread: https://forum.image-line.com/viewtopic.php?p=2070063
- FL Studio API Stubs on PyPI: https://pypi.org/project/FL-Studio-API-Stubs and the repository: https://github.com/IL-Group/FL-Studio-API-Stubs
- Maddy Guthridge's stubs: https://github.com/MaddyGuthridge/FL-Studio-API-Stubs
- flstudio-mcp: https://github.com/rosasynthesiz/flstudio-mcp
- fl-studio-mcp (karl-andres): https://mcpservers.org/servers/karl-andres/fl-studio-mcp
- flai-mcp: https://glama.ai/mcp/servers/kaupau/flai-mcp
- Ableton MCP: https://mcpservers.org/servers/ahujasid/ableton-mcp
- ReaperMCP (xdarkzx): https://pypi.org/project/xdarkzx-reaper-mcp/0.6.3/
- reaper-mcp (bonfire-systems): https://github.com/bonfire-systems/reaper-mcp
- MVSEP algorithms and scores: https://mvsep.com/en/algorithms
- python-audio-separator releases: https://github.com/nomadkaraoke/python-audio-separator/releases
- beat_this: https://github.com/CPJKU/beat_this
- SongFormer paper: https://arxiv.org/html/2510.02797v2 and code: https://github.com/aslp-lab/songformer
- ACE-Step 1.5 README: https://github.com/ACE-Step/ACE-Step-1.5
- Music Flamingo: https://research.nvidia.com/labs/adlr/MF
- Audiobox Aesthetics review: https://cyanite.ai/blog/meta-audiobox-aesthetics-review/
- Music similarity with pretrained embeddings (2026): https://arxiv.org/html/2601.19109v1
- RMVPE: https://arxiv.org/pdf/2306.15412
- Rubber Band news: https://breakfastquay.com/news.html
- iZotope dance and electronic loudness analysis (2025): https://www.izotope.com/en/learn/dance-electronic-analysis
- TrackSensei, 563 techno and house tracks (2026): https://tracksensei.com/blog/we-analyzed-563-techno-house-tracks
- Beatportal peak-time techno guide (2024): https://www.beatportal.com/articles/783088-step-by-step-guide-to-producing-techno-peak-time-driving-in-the-style-of-layton-giordani-eli-brown-and-adam-beyer
- Midnight Rebels, techno tempos: https://midnightrebels.com/140-bpm-is-the-new-128-why-techno-is-getting-faster/
- Point Blank, dubstep drop: https://www.pointblankmusicschool.com/blog/how-to-create-a-dubstep-drop-from-scratch/
- Beatportal drum and bass guide (2025): https://www.beatportal.com/articles/818379-step-by-step-guide-to-producing-drum-and-bass-like-sub-focus-a-m-c-and-delta-heavy
- TIDAL, what makes trap trap (2020): https://tidal.com/magazine/article/what-makes-trap-trap/1-72722

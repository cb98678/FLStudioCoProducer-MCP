# Handoff: start here

Rewritten 2026-10-25 after the realignment review. Read this, then `ROADMAP.md` (what is missing and the order to build it), then `STATUS.md`
(what is proven), `FILE_MAP.md` (every file in one line) and `LESSONS_TO_RECIPES.md`.

## What this project is

A clean-room, local-first AI co-producer for FL Studio: MCP servers, about 530 modules, recipes, skills and a Python layer. **The product is the
modules, recipes and skills that remix any song the person drops in** (stems, analysis, a genre plan, an editable FL project, production, mix,
master, evaluation). "Friends in Low Places" is only the regression test: tuning that one project is not progress. The person had to say this
twice (2026-10-25). After every change or listening note, put the general version in a module, recipe, skill rule, measure or test, or log it as
song specific in `LESSONS_TO_RECIPES.md`.

The person is Mark ("Meeps"), a principal engineer who produces as a hobby. Windows 11 machine "rtxclub": RTX 3090 (24 GB), FL Studio 2026
Producer Edition v26.1.7 build 5654 (API level 45, embedded Python 3.12.1), Serum 1.368 and Serum 2 2.1.5.

## Where the work stands (2026-10-29, evening)

- **Girlish Type Men, vocal-led layers** (`sandbox\remix\gtm_vocal_v6`, waiting for the person's ear). The person's recipe: synths follow
  the voice's chords, long pads under spaced-out stabs, a bass that rolls and then stretches out in the drops, piano rolls up to 16 bars.
  `voiceharmony.section_loops`, chords.pad_and_spaced_stabs (a Pad part), bass.roll_then_long_drop, the plan's pattern_bars. Skill
  `song-blueprints` has the recipe and the person's three song breakdowns (Clarity, Red Lights, Another Night) as checked facts and
  options (`LESSONS_TO_RECIPES.md` rows 95 to 100).

- **Stems by FL Studio** (the person: FL already splits stems, use it). Intake now runs FL's clip menu entry Extract stems from sample:
  `prepare_stems_project` writes a bench project (the song on track 1, the data folder pointed at the work folder, FLP event 202) and
  `extract_stems_gui` opens it, runs the recipe `extract_stems_gui` and copies vocals, drums, bass and other into `songs\NAME\stems\fl`.
  `tools/remix_song.py --separator fl` is the default; `--separator models` keeps RoFormer and Demucs. FL stays open afterwards, so ask
  before the render closes it. Verified end to end on Girlish Type Men (74 s); the recipe finds the clip, menu entry and button by picture
  (`LESSONS_TO_RECIPES.md` rows 87 to 93).

- **Girlish Type Men, vocal-led remake** (`sandbox\remix\gtm_vocal_v5`, waiting for the person's ear). The person: remake the bass and
  synths from the voice, everything in one key, auto-tune it, fit it to the beat with Newtime and Newtone, a bit faster (130 bpm, the voice
  at its own speed). The vocal chain lives in `sandbox\songs\girlish_type_men\gui`: padded to the grid, slowed 442/441 onto Newtime's
  grid (`LESSONS_TO_RECIPES.md` row 79), 127 warp markers, quantized, sped back, tuned three ways, spliced by section
  (`tools/splice_takes.py`) into `vocals_tuned_130.wav`. Plan: `edit_plan.py` there (v4's form, new variety locks, the harmony from the
  voice). Modules: `detect_warp_markers`, `add_warp_markers_gui`, `quantize_vocal_gui`, `apply_vocal_tuning_gui`, `prepare_rate_copy`;
  recipes `newtime_load_gui` (draft), `newtime_quantize_save_gui`, `newtone_tune_save_gui`.

## Where the work stands (2026-10-29)

- **Open Your Heart, tech house** (`sandbox\remix\oyh_tech_house_v3`, waiting for the person's ear). Tech house for a new song is the
  grammar pack `tech_house_groove`, never "tech_house" (the Friends engine). An edited plan goes through the one command with `--plan`.
  The contrast loop lifts builds and quiet sections one by one (`contrast.section_lifts`, `shortfall_each`). Ruff is not in the host venv.
- **Girlish Type Men, pop dance** (`sandbox\remix\gtm_pop_dance_v4`, waiting for the person's ear). Intake now redoes Whisper loops
  (`asrclean`); the long vocal is raised when quiet (`remixaudio.voice_lift_db`) and no longer rides the music bus pump (`mixroute.LEAD_ROLES`).

## Where the work stands (2026-10-28)

- **Serum 2 wavetables and sampler sounds from the song** (the person, 2026-10-28 evening: "make skills on how to use the MCP Serum 2
  for Wave tables ... extract sounds or vocal or even drum sounds and basses and use them in the song"). Skill `serum-wavetables`;
  `src/coproducer/wavetables.py` (pitch-synchronous tables: every harmonic fitted over whole periods and rebuilt at 2048 samples, phase
  aligned; Serum formula tables; the table file with Serum's clm chunk; the sampler plan) and `serumspec.py` (pluck, 16th chop, in-synth
  duck, four macros, dirt, room as serum-mcp spec parts); MCP tools build_wavetable and prepare_sampler_sound; tools/serum_tables.py for a
  whole loops folder. Proved on rtxclub with sandbox\loops\sorry_freejak: seven presets in Presets\User\sandbox\sorry_freejak, tables in
  Tables\User\sandbox\sorry_freejak, headless renders measured (`docs/SERUM_MCP.md`, "Wavetables and the sampler"). The person's
  attachment (a "Tech House Dual-Server Remix Engine" text for flmcp) is checked in skills/serum-wavetables/references/attachment-review.md:
  its sub and lead formulas are wrong as written (x runs -1 to 1, so a sine is sin(pi*x)), sample_center_pan does not centre a vocal,
  drive and compressor gain are not serum-mcp mod destinations, Serum 2 has no Tube mode. Not yet heard by the person.
- **Remix studies, the first one done** (the person brought "Sorry" and Freejak's remix, 2026-10-28: "examine them carefully and see what
  they did ... make skills and recipes that let you do this in FL studio"). `docs/remix_studies/sorry_freejak.md` reads the whole of both
  tracks bar by bar; `docs/REMIX_RESEARCH.md` section 13 says what it changed. Built from it: seven options sourced to the study
  (sources.json "remixes"), the arranger turning each pass's function (form engine verse_as, chorus_as, drop_after, tail_break), harmony
  loops with two chords a bar that can re-harmonize the whole song (locked only), the form's tempo "standard", the loop and kit cutter
  (`src/coproducer/loopkit.py`, `loopsets.py`; MCP tools extract_song_loops and find_matching_loops; tools/extract_loops.py,
  tools/find_loops.py; skill `loops-and-kits`) and the FL steps for every move (skills/remix-craft/references/fl-howto.md). Loops and kits
  of both tracks: sandbox\loops\sorry and sandbox\loops\sorry_freejak. The person said more pairs are coming.
- Still open from the 14:04 notes: hard rolling and wobbly bass under curse house B's drop, the house A reverb wash (a vocal clarity
  check), the afro versions. The two rules the person was asked about are answered (2026-10-28): lines whole but chosen per remix, yes;
  slower, "yes but not too slow and preserve pitch" (at most 6 %).

- **Variety, from the FL demo songs** (the person, 2026-10-28: "you keep making the same format and same song over and over again"). The
  twenty demo songs that ship with FL Studio 2026 were read from their files, rendered (full mixes and 146 eight to sixteen bar solos of
  their main parts, sandbox copies only) and measured: `docs/DEMO_STUDY.md` and one page per song in `docs/demo_study/`; the scripts
  that made them, in order, are in `tools/demo_study/` (README). What they do
  became an option bank (`src/coproducer/data/options/`: forms, grooves, kits, bass lines, chord treatments, arps, harmony loops,
  instruments, transitions, mix moves, automation, vocal treatments; each option cites its demo song) and fifteen new style packs
  (afro house, afrobeats, reggaeton, trance, melodic techno, liquid drum and bass, future bass, UK drill, lo-fi, trip hop, pop dance,
  future house, big room, electro industrial, cinematic).
- **The variety engine** (`src/coproducer/variety.py`, skill `creative-variety`): `build_song_plan` picks one option per category for the
  song's genre, mood and energy, avoids what the last remixes used (`sandbox/variety_history.json`, written by `build_remix_project`),
  borrows one surprise from another genre with the same mood, and writes the choices with their reasons and alternatives into the plan.
  `tools/remix_song.py` takes `--variety-seed`, `--lock CATEGORY=OPTION`, `--mood` and `--no-variety`.
- **The engine grew to play them**: triplet grids, perc and ride voices, chord voicings (seventh, add9, sus, open, octaves, minmaj, scale
  runs), nine arp shapes, new bass characters (fifth below, fourth, minor seventh, flat second, octave down, pedal), form policies (which
  choruses build, bridges, tails, a gap before the drop, drum drop-outs), transition cues (sub drop, reverse cymbal, noise wash), demo kits
  and demo instruments imported into the remix in their own register, and a sound direction (the original's tone with the demo
  instrument's envelope and width) for `match_part_sound`.
- **Readers fixed on the way**: playlist clips muted in FL (item flag 0x2000) no longer count as playing (`Flp.item_muted`,
  `pattern_clips`, `audio_clips`, `projmusic.song_notes`); the master pitch knob (`Flp.main_pitch`, event 80) moves the key and chords
  the notes sound in; `render_folder_via_cli` reports `silent` only for a render with nothing in it (`mostly_silent` and
  `silent_fraction` for sparse parts); the contrast loop stops when the section-gain map cannot move a drop the way it must go
  (`contrast.blocked`) or every floor lift is at its cap, instead of rendering four more times, and lifts builds that sit too far
  under their drops (`contrast.build_lift`: two afro house remixes went from 8.5 and 11 LU to 4.3); locked sounds count toward the
  number of demo instruments, so locking a remix's choices rebuilds it; the panel's section-contrast judge runs again (it passed
  `measure_section_levels` no tempo, so it had measured nothing); `tools/compare_remixes.py` puts versions side by side; the panel asks the
  person (it does not fail) when a drop sits under 1 LU over the verse or groove before it; a remix's bass part is found whatever it is
  called (an 808 alone is the bass, and the bass part takes the map's reese section gains), and an imported demo instrument whose own
  name says another role is named "Stab - ..." so routing, pumps and section gains still find it.
- **Five genre production recipes from the demos**: `recipes/production/trance.json`, `afro_house.json`, `lofi.json`, `cinematic.json`,
  `latin_pop.json` (used by the trance, afro house, lo-fi, cinematic and reggaeton packs).

## Where the work stood (2026-10-26)

- **A new chat starts with `list_skills`** on `coproducer-fl-bridge` (then `read_skill co-producer-protocol` and the task's skill): the
  skills, docs and style packs are served read only, because a Claude Desktop chat has no copy of this folder.
- **Creative per song**: the brief (`skills/remix-from-stems/references/creative-brief.md`) is written before the plan; `write_song_notes`
  requires the song's mood with its evidence, and the draft plan carries `brief` for the decisions and the surprise.
- **Sounds matched to the record**: `measure_part_sound` (the original part's envelope, brightness, harmonics, width, register and a
  serum-mcp draft), serum-mcp `generate_preset`, `render_serum_sound` (Serum 2 headless through pedalboard, no FL), `compare_part_sound`,
  then `build_remix_project` option `serum_states` writes the state into a Serum 2 channel (`docs/SERUM_MCP.md`). Proved offline on
  2026-10-26 (a rebuilt state renders the same audio as Serum's own); the first FL load of such a project is still to be checked with the
  person present.
- **One-command installer** (`install.ps1`, `install.cmd`, `docs/INSTALL.md`): from an unzipped release it installs its own uv, Python,
  packages, ffmpeg, loopMIDI with the ports and FL's MIDI settings (`coproducer setup-midi`), the models, and the Claude Desktop
  registration, then starts each server the way Desktop will (`coproducer check-servers`) and runs `coproducer doctor`. Build the zip with
  `python tools/make_release.py` (an allowlist of top-level entries; nothing of this machine goes in). Pins are checked against the
  dependency lock by `tests/test_installer.py`.
- **Claude Desktop from the Microsoft Store reads its own config** in `%LOCALAPPDATA%\Packages\Claude_<id>\LocalCache\Roaming\Claude`, not
  `%APPDATA%\Claude`. And while it runs it rewrites that whole file from memory on any settings change, so entries written while it
  runs are lost (that is why the servers never loaded on rtxclub). `coproducer install-desktop` writes the file Desktop reads, only while
  Desktop is closed (`--wait` waits for you to quit it, `--restart` opens it again).
- **One flag for matched sounds**: `tools/remix_song.py ... --match-sounds` runs `match_part_sound` for the stab, arp and sub before the
  build. **Two mood packs**: `deep_house` (sad, romantic, bittersweet) and `nu_disco` (happy, playful, comic); every pack lists its moods
  and `stylepack.for_mood` ranks them for a song's brief.

## Where the work stood (2026-10-25, evening)

- **Any song, any of six genres, one command**: `python tools/remix_song.py NAME STYLE --song FILE` (or `--analysis FOLDER` to reuse an
  intake). The chain is modules: `build_song_analysis` (stems with RoFormer vocals plus Demucs, beat_this bar grid, Whisper words, torchcrepe
  melody, bass roots, key vote, source sections) -> `build_song_plan` (style pack sections and tempo) -> `prepare_remix_audio` (stretched and
  pitched vocal, the style's kit and bass sample) -> `build_remix_project` -> `apply_production_recipe` -> `render_via_cli` -> contrast loop
  (`measure_section_levels`, `apply_section_gains`) -> `apply_club_master` (-8 LUFS, at most -0.5 dBTP) -> `check_remix_panel`.
- **The person's remix rules (2026-10-25, late; two changed 2026-10-28)**: the vocal at its own tempo, faster, or at most 6 % slower with
  its pitch kept (`stylepack.pick_tempo`, MAX_SLOWDOWN; was never slower); lines stay whole and no word is cut, but which lines, in what order
  and in what role is each remix's choice (was every verse and chorus whole, in order); a research
  step names the song and writes its form and favourite parts with sources (`find_song_clues`, `write_song_notes`, never lyrics from the
  web); the plan keeps every verse and chorus whole in the song's own order with the original's instrumentation stem in the intro and solo
  (`songform`), chops are whole sung lines cut through their last sound (`remixaudio.whole_end`); a reference MIDI (MIDI World,
  `tools/fetch_reference_midi.py`) is tested against the record and gives the chord synth the song's chords and strum as clean triads
  (`midiref`); synths are Serum 2 from the person's own sounds (`--serum`). First test: one techno remix of Friends.
- **Genres are data**: `styles/*.json` (house, tech_house, techno, dubstep, dnb, trap, hiphop), skill `genre-styles`. Tech house keeps the legacy
  engine so the Friends regression build stays byte-identical; the others use the grammar engine in `stylepack.py`.
- **Evaluation panel**: `check_remix_panel` (dsp and plan judges trusted, the critic graded first on questions the plan answers),
  `compare_to_references_ml` (MuQ-MuLan similarity against the original as a baseline). The person is gathering reference tracks for it.
- **FL control**: 319 generated L1 ops cover the whole inventory except keystroke-style ui calls; `tools/probe_l1.py --launch` checks every
  read op live (all 176 answered on FL 26.1.7, 2026-10-25).
- Regression baselines on the host: `sandbox\techhouse\FriendsInLowPlaces_TechHouse_v15.flp` (approved by ear) and `..._v16_contrast.flp`.
- First song-form remix under the new rules: `sandbox\remix\friends_techno_song_v2` (techno, panel passed, waiting for the person's ear).
  Serum 2 sounds come from `sandbox\serum\serum_sounds.flp`, a copy of v15.
- Open work, in order, is `ROADMAP.md` section "Progress" plus section 9.

## Standing rules

- **Creative per song.** Read the song's mood, sonic space, key, bpm and lyrics; choose the style, palette, arrangement moves and one surprise for that song, with reasons (`skills/remix-from-stems/references/creative-brief.md`). Never ship the last song's format unchanged. Synth sounds are generated with the Serum 2 MCP to match the original's parts, then given a twist; the person's presets are references (2026-10-26).
- **Fix the recipe, not the clip.** Change the rule that made a bad result, rerun it everywhere, report what changed. Never hand-patch one file.
- **Editable first.** Drums are sampler channels plus patterns, synths and bass are plugin channels plus notes. Audio only for vocals,
  risers and FX, long textures, impacts, resamples (`PRODUCTION_POLICY.md`, skill `editable-first`).
- **Never kill FL, close a project, or render without asking.** FL's command line renders only while FL is closed. `render_via_cli` and
  `render_folder_via_cli` refuse while FL runs (or when the process list cannot be read); `render_with_restart` closes and reopens FL and is
  A1, so a run asks each time. Queue jobs that render also check `tasklist` first and stop with `FL_IS_RUNNING_NOT_RENDERING`.
- The person's own edits are the baseline: they save a copy when they hand-fix something; diff it (`diff_flp_projects`), never build over it.
- **Ask before any download or install**, with the source and size. Read third-party code before running it.
- **Say what could not be verified.** Ears are the final check; say when something was checked only by measurement.
- **Documents**: no em dashes (the linter and tests enforce it in module text and skills), cite sources with links, use the latest docs.
- Pin every version (`DEPENDENCIES.md`, generated). Direct, rigorous answers; push back on a bad idea.

## Where things live

| Place | What |
| --- | --- |
| Cloud container `/home/claude/coproducer` | The repo you edit and test (`python3 -m pytest`, about 1600 tests, and `ruff check`). No FL, no GPU. |
| Host `C:\coproducer` | The same repo, `.venv` (host packages from `requirements.lock`), the model environments `models\envs\{demucs,basicpitch,critique,mir,sep}` (frozen in `models\locks\`), the ACE-Step clone, and the data. Whisper and Music Flamingo run in `models\envs\critique` at pinned revisions. |
| `C:\coproducer\sandbox\` | Host only: working projects, stems, renders, the job queue. Never write the person's originals; outputs go under a folder named `sandbox`. |

### Getting code to the host and running jobs

1. **Deploy**: tar the files changed since the last update (`cp_updateNN.tar`, skip `__pycache__`, `.pytest_cache`, `.hypothesis`), copy it to
   `C:\coproducer\sandbox\deploy\` with `device_commit_files`, then queue `python sandbox\deploy\extract_new.py sandbox\deploy\cp_updateNN.tar`
   (it skips unchanged files, makes a read-only file writable, and lists any file it could not write). Extract in numeric order. Last
   deployed: `cp_update127` (2026-10-26). `docs\DEPENDENCIES.md`, `requirements.lock` and `src\coproducer\data\deps.lock.json` are
   read-only on the host: `attrib -R` before `coproducer deps --freeze`, `+R` after.
   **Then commit**: `C:\coproducer` is a git repository since 2026-10-26 (branch main; `.gitignore` keeps sandbox, models, venvs and runs
   out). After each deploy that works, queue `git add -A` and `git commit` with a message saying what changed and the attribution lines.
2. **Queue**: `tools/queue_runner.ps1` (the person keeps it running) runs `*.cmd` files in `C:\coproducer\sandbox\queue\` oldest file first
   (by creation time, not name: on 2026-10-25 two older jobs ran before a newer deploy job whose name sorted first. Re-creating a job under
   the same name within about 15 s keeps its old creation time (NTFS tunneling), so to put a deploy ahead of waiting jobs, move them to
   `queue\hold\` and write them back under new names)
   and writes `done\NAME.out.txt` and `NAME.exit.txt`. Write the job as `.tmp`, convert to CRLF, rename to `.cmd`. Jobs are serial. Give
   every job a new name (the last used were `zz_z*`, up to `zz_zu_*`; next `zz_zv_...`); an old name reruns stale output.
3. **Look at host files** with `device_stage_files` (they appear under `/mnt/user-data/uploads/C:--coproducer/...`). Editing a staged file and
   committing it back may not refresh; edit on the host with the device shell instead.

## Rebuild a remix

Module route (the product), any song with FL's four stems:

```
build_song_plan      -> plans\NAME.json (review the chops with the person: V1)
build_remix_project  -> sandbox\...\NAME_vNN.flp (editable parts, section markers, house standard)
apply_production_recipe (recipe club_house) -> ..._produced.flp
render_via_cli (FL closed) -> measure_section_levels, then apply_section_gains (contrast loop)
split_part_projects + render_folder_via_cli + measure_part_levels + compare_part_levels -> gain staging
mastering against targets\club_tech_house.toml with a reference track
```

Legacy Friends route (regression only): `tools\refine_cuts.py` (in `models\envs\critique`), `tools\techhouse_audio.py`,
`tools\build_techhouse.py`, then `render_via_cli`; examples in `sandbox\queue\done\z_ub_v12.cmd` and following.

Renders of the Future House demo must use `FutureHouse_render_noTP.flp` (the Transient Processor is a trial plugin here and stalls FL).

## Gotchas that cost time before

- Installer lessons (2026-10-26): a release built from a denylist swept up a 14 GB savepoint zip and 10 GB of ACE-Step checkpoints at the
  top of `C:\coproducer` (now an allowlist, and savepoints go to `sandbox\savepoints`); ACE-Step put its checkpoints in the server's current
  folder because no `ACESTEP_HOME` was set (the worker factory sets it to the clone now); `uv venv` refuses an existing environment, so every
  install command passes `--allow-existing`; Windows PowerShell 5.1 drops an empty argument to a program, so the CPU torch index is passed
  as `--torch-index=`; the whole Whisper repo is 25 GB (fp32, .bin and Flax copies), so snapshots take only the files a worker loads.

- When the person's computer sleeps, the running job is killed (exit 1073807364) and the queue resumes on wake; rerun that job.

- Whisper word times drift 0.2 to 0.7 s on singing and it completes truncated words; use it to reject syllables, never as a cut point.
- A quiet gap in a vocal is not always a word boundary; a final s can sit 0.3 s after the vowel dies.
- Computer-use access to FL lapses after about 30 minutes idle; `computer_open_application` on FL starts a second instance (never use it).
- `coproducer gen` regenerates the skill catalogs and the FL-side script; `python tools/gen_file_map.py` regenerates `FILE_MAP.md`. Tests fail
  until both are current.
- After changing anything the FL side runs (L1 ops, `fl_prelude.py`), run `coproducer gen`, deploy, then install the script with
  `python -c "from pathlib import Path; from coproducer.cli.setup_cmd import install_fl_side; print(install_fl_side(Path('.')))"`
  and restart FL (or reload the script in MIDI settings). An empty `[fl] data_dir` once sent it to `C:\coproducer\Settings`, where FL never
  looks, and the live probe then saw 117 unknown ops (fixed 2026-10-25).
- Only inject effects and clips into a project FL saved itself; `Flp.save` refuses PPQ other than 96 and saves older than FL 21.
- FL holds a knob at a clip's last value, and a plugin plays as saved before its first clip (`REFERENCE_COVERAGE.md`).

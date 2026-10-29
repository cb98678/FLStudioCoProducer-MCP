"""Remix a song into a style, end to end, through the registered modules (the same calls a run makes, ceiling A2, sandbox only).

    python tools/remix_song.py NAME STYLE [--song FILE [--separator fl|models] | --analysis sandbox\\songs\\NAME [--vocals VOCALS.wav]] [--title "hook line"]
                               [--base BASE.flp] [--sytrus SYTRUS.flp] [--stems-dir DIR] [--no-render] [--work sandbox\\remix\\NAME_STYLE]
                               [--critic] [--reference REF.wav ...] [--original SONG.wav] [--references-dir DIR] [--finish]
                               [--serum SOUNDS.flp] [--serum-preset stab="PRESET NAME" ...] [--serum-state stab=FILE ...]
                               [--match-sounds [--match-to PART=vocals|other|bass|FILE|none ...]] [--every-part] [--variety-seed S]
                               [--lock CATEGORY=OPTION ...] [--mood WORD ...] [--no-variety]
                               [--plan EDITED_PLAN.json]

Steps, each a module: extract_stems_gui (FL Studio's own stem split, unless --separator models), build_song_analysis (grid, words, melody, key vote), build_song_plan (style pack: tempo, sections, parts),
prepare_remix_audio (stretched vocal, chops, kit, bass sample, FX bed), with --match-sounds match_part_sound for each synth part (a
Serum 2 sound generated, heard and compared against the original's part), build_remix_project (editable parts), apply_production_recipe (the style's
moves), then, only while FL Studio is closed, render_via_cli, build_measure_report and measure_section_levels; the contrast loop
(apply_section_gains scaled and rendered again until each drop sits 3 to 5.5 LU over its build and no intro, groove, break or outro sits
further under the drops than the targets' section floor), apply_club_master to the style's targets (with an
MP3 to listen to), two tempo checks (the beat tracker on the render when its beats are steady, and the render's length against the plan), and
check_remix_panel on the master. --critic adds the audio critic to the panel (it loads a 16 GB model; passing the flag is the approval), and
--reference adds the similarity judge (with --original as its baseline). Reference tracks the person drops in sandbox\\references\\STYLE (or
--references-dir) are measured once by build_reference_profile: the master then takes its loudness, crest and tonal balance from them
(targets.toml and profile.json in that folder), and the panel judges the master against them. --finish redoes only those last steps
on the earlier run in --work, so new references need no new render. Every step's result goes into WORK\\remix_report.json; the first
failure stops the run and is reported. The base project is an FL-saved stem project (its channels are replaced) and the Sytrus project supplies the fallback patches.
"""
from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import soundfile as sf  # noqa: E402

from coproducer import beatgrid, contrast, sectiongain, stylepack, variety  # noqa: E402
from coproducer.servers.common import make_session  # noqa: E402

HOME = Path(__file__).resolve().parents[1]
AUDIO = {".wav", ".flac", ".mp3", ".aif", ".aiff", ".ogg", ".m4a", ".aac"}


def first(*paths: Path) -> str:
    """The first of the paths that exists (this machine's own project), else the last (the installed template)."""
    return str(next((p for p in paths if p.is_file()), paths[-1]))


def serum_ready(carrier: str) -> bool:
    """Serum 2, its headless host and serum-mcp's generator are all installed, and a project with a Serum 2 channel exists to carry sounds."""
    import os

    from coproducer.config import load_config
    envs = load_config(HOME).get("envs", {})
    vst = os.environ.get("SERUM2_VST3") or r"C:\Program Files\Common Files\VST3\Serum2.vst3\Contents\x86_64-win\Serum2.vst3"
    return bool(envs.get("serum") and envs.get("serummcp") and Path(carrier).is_file() and Path(vst).exists())


def fl_input_wav(src: Path, folder: Path) -> Path | None:
    """The song as a 44.1 kHz WAV for FL's stem extraction, decoded the way build_song_analysis decodes it (so the stems line up with song.wav)."""
    import shutil
    import subprocess
    folder.mkdir(parents=True, exist_ok=True)
    dst = folder / "fl_input.wav"
    if src.suffix.lower() == ".wav":
        shutil.copyfile(src, dst)
        return dst
    ff = shutil.which("ffmpeg")
    done = subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-ar", "44100", "-c:a", "pcm_s16le", str(dst)],
                          capture_output=True, check=False) if ff else None
    return dst if done is not None and done.returncode == 0 and dst.is_file() else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name")
    ap.add_argument("style", choices=stylepack.names())
    ap.add_argument("--song", default="")
    ap.add_argument("--analysis", default="", help="a folder from an earlier build_song_analysis (vocal_words.json, drum_hits.json, stem_notes.json, song_analysis.json)")
    ap.add_argument("--stems-dir", default="")
    ap.add_argument("--separator", choices=("fl", "models"), default="fl", help="who splits a new song into stems: FL Studio's own Extract stems "
                    "from sample (default, needs FL closed or on a saved sandbox project) or the local RoFormer and Demucs models")
    ap.add_argument("--vocals", default="", help="the vocal stem, when --analysis came from older tools (no song_analysis.json)")
    ap.add_argument("--title", default="")
    ap.add_argument("--base", default=first(HOME / "sandbox" / "stemstest" / "stemstest.flp", HOME / "sandbox" / "templates" / "base_project.flp"))
    ap.add_argument("--sytrus", default=first(HOME / "sandbox" / "DTP_work" / "Notorious_DTP_28_auto.flp", HOME / "sandbox" / "templates" / "sytrus_patches.flp"))
    ap.add_argument("--work", default="")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--critic", action="store_true", help="ask the audio critic too (A1: the flag is the approval)")
    ap.add_argument("--reference", action="append", default=[], help="a reference track for the similarity judge (repeatable)")
    ap.add_argument("--original", default="", help="the source song, the similarity judge's baseline")
    ap.add_argument("--serum", default=first(HOME / "sandbox" / "serum" / "serum_sounds.flp", HOME / "sandbox" / "templates" / "serum_carrier.flp"),
                    help="a project with Serum 2 channels holding the sounds to use, matched by preset name (default sandbox\\serum\\serum_sounds.flp)")
    ap.add_argument("--serum-preset", action="append", default=[], help="PART=PRESET NAME for sub, stab (the chord synth) or arp (repeatable)")
    ap.add_argument("--serum-state", action="append", default=[], help="PART=FILE: a generated sound's Serum 2 channel state (render_serum_sound) for sub, stab or arp (repeatable)")
    ap.add_argument("--match-sounds", action="store_true", help="generate each synth part's Serum 2 sound to match the original (match_part_sound: "
                    "the stab and arp from the other stem, the sub from the bass stem); the default whenever Serum 2 and its two model "
                    "environments are installed (the person's rule, 2026-10-26)")
    ap.add_argument("--match-to", action="append", default=[], help="PART=SOURCE for --match-sounds: the stem a part's sound is matched to "
                    "(vocals, other, bass, a file, or none to keep the plan's library sound); default stab and arp to other, sub to bass (repeatable)")
    ap.add_argument("--library-sounds", action="store_true", help="use the Serum project's presets by name instead of generating sounds")
    ap.add_argument("--key-pc", type=int, default=None, help="the song's key as a pitch class (0 C .. 11 B) when the key vote is wrong")
    ap.add_argument("--every-part", action="store_true", help="keep every verse and every chorus of the song (default: the first two of each)")
    ap.add_argument("--finish", action="store_true", help="re-master and re-judge the earlier run in --work without building or rendering")
    ap.add_argument("--variety-seed", default=None, help="another seed gives another valid set of choices (form, groove, kit, bass, sounds...) for the same song")
    ap.add_argument("--lock", action="append", default=[], help="CATEGORY=OPTION_ID (or sound.ROLE=OPTION_ID) to keep a choice, e.g. drums=drums.dembow (repeatable)")
    ap.add_argument("--mood", action="append", default=[], help="a mood word for the brief when the research notes have none (repeatable)")
    ap.add_argument("--no-variety", action="store_true", help="the style pack exactly as written (no variety choices)")
    ap.add_argument("--references-dir", default="", help="reference tracks for this style (default sandbox\\references\\STYLE)")
    ap.add_argument("--plan", default="", help="a song plan already drafted by build_song_plan and edited by hand for this remix's concept (skill remix-craft: "
                    "form, kept lines, roles); it is validated, copied to WORK\\plan.json and used instead of drafting a new one")
    a = ap.parse_args()
    if not a.match_sounds and not a.library_sounds and serum_ready(a.serum):
        a.match_sounds = True
        print("sounds: generating each synth part's Serum 2 sound to match the song (--library-sounds to use presets by name)")
    s = make_session(HOME, "remix_" + a.name, "fl-bridge", "A2")
    call = s.registry.call
    work = Path(a.work or HOME / "sandbox" / "remix" / ("%s_%s" % (a.name, a.style)))
    work.mkdir(parents=True, exist_ok=True)
    report: dict = {"name": a.name, "style": a.style, "steps": []}

    def step(label: str, module: str, **kw):
        r = call(module, **kw)
        row = {"step": label, "module": module, "ok": r.ok, "verified": r.meta.get("verified")}
        row.update({"value": r.value} if r.ok else {"error": r.error.code, "message": r.error.message})
        report["steps"].append(row)
        (work / "remix_report.json").write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
        print("%-14s %-26s %s" % (label, module, "ok" if r.ok else "%s: %s" % (r.error.code, r.error.message)), flush=True)
        return r

    plan = work / "plan.json"

    def finish(wav: str) -> int:
        """References, master, MP3, tempo checks and the panel on a finished mixdown (also the whole of --finish)."""
        pack = stylepack.load(a.style)
        targets, profile, refs = str(HOME / pack["targets"]), "", list(a.reference)
        rdir = Path(a.references_dir or HOME / "sandbox" / "references" / a.style)
        found = sorted(f for f in rdir.glob("*") if f.suffix.lower() in AUDIO) if rdir.is_dir() else []
        if found:  # the person's references set this master's loudness, crest and tonal balance; re-measured when a file is newer than the profile
            prof, tgt = rdir / "profile.json", rdir / "targets.toml"
            if not prof.is_file() or not tgt.is_file() or max(f.stat().st_mtime for f in found) > prof.stat().st_mtime:
                step("references", "build_reference_profile", paths=[str(f) for f in found], out_file=str(prof), targets_out=str(tgt), base_targets=targets)
            if prof.is_file() and tgt.is_file():
                targets, profile, refs = str(tgt), str(prof), refs + [str(f) for f in found]
        report["references"] = {"folder": str(rdir), "files": [f.name for f in found], "targets": targets, "profile": profile or None}
        m = step("master", "apply_club_master", path=wav, targets_file=targets, out_path=str(work / "master" / ("%s_%s_club.wav" % (a.name, a.style))),
                 **({"profile": profile} if profile else {}))
        if m.ok:
            mp3 = Path(m.value["out"]).with_suffix(".mp3")
            import subprocess
            subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", m.value["out"], "-b:a", "320k", str(mp3)], check=False)
            report["listen"] = str(mp3) if mp3.is_file() else None
        t = step("tempo check", "detect_beats_ml", path=wav)
        pl = json.loads(plan.read_text(encoding="utf-8"))
        bpm = float(pl.get("bpm") or pack["tempo"]["bpm"])  # the plan's tempo: pick_tempo moves it off the pack's bpm to keep the vocal from slowing
        bars = pl["sections"][-1]["end"]
        want_s = bars * 240.0 / bpm
        got_s = round(sf.info(wav).duration, 2)
        check = {"plan_bpm": bpm, "bars": bars, "expected_s": round(want_s, 2), "render_s": got_s}
        if t.ok:  # two independent checks: the tracked beats and bars against the plan's grid, and the render's length against the plan's bars
            fb, fd = beatgrid.grid_fit(t.value["beats"], 60.0 / bpm), beatgrid.grid_fit(t.value["downbeats"], 240.0 / bpm)
            check.update(render_bpm=t.value["bpm"], tempo_from=t.value.get("tempo_from"), beats_on_grid=fb["share"], bars_on_grid=fd["share"],
                         tracker_ok=max(fb["share"], fd["share"]) >= 0.8)  # a half-time beat still sits on the beat grid
        check["length_ok"] = 0 <= got_s - want_s < 8.0  # the raw render; a longer one has a tail that never went silent (DC, see measure_dc_offset)
        report["tempo_check"] = check
        print("tempo check", check)
        if m.ok:
            s.approved_now = "check_remix_panel"  # the person ran this tool; --critic is their yes to the 16 GB model
            p = step("panel", "check_remix_panel", path=m.value["out"], plan_file=str(plan), targets_file=targets, mixdown=wav, references=refs,
                     options={"critic": a.critic, **({"profile": profile} if profile else {}),
                              **({"original": a.original or a.song} if (a.original or a.song) else {})})
            s.approved_now = None
            if p.ok:
                report["panel"] = {k: p.value[k] for k in ("passed", "problems", "ask_person", "notes")}
                print("panel", "passed" if p.value["passed"] else "problems: " + ", ".join(x["item"] for x in p.value["problems"]))
                if p.value["ask_person"]:
                    print("ask the person:", ", ".join(x["item"] for x in p.value["ask_person"]))
        (work / "remix_report.json").write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
        return 0

    if a.finish:  # re-master and judge an earlier run of this name and style: no build, no render (after adding reference tracks, say)
        old = json.loads((work / "remix_report.json").read_text(encoding="utf-8"))
        report = {**old, "steps": old["steps"] + [{"step": "finish", "module": "-", "ok": True}]}
        return finish(old["mixdown"])
    folder = Path(a.analysis) if a.analysis else None
    if folder is None:
        if not a.song:
            sys.exit("give --song FILE or --analysis FOLDER")
        if a.separator == "fl" and not a.stems_dir:  # FL Studio's own Extract stems from sample (the person, 2026-10-29), not a local model
            here = HOME / "sandbox" / "songs" / a.name
            wav = fl_input_wav(Path(a.song), here)
            if wav is None:
                sys.exit("could not make a WAV of %s for FL (is ffmpeg on PATH?)" % a.song)
            r = step("stems", "extract_stems_gui", path=str(wav), out_dir=str(here / "stems" / "fl"))
            if not r.ok:
                print("FL's stem extraction needs FL closed or showing a saved sandbox project; --separator models uses the local models instead")
                return 1
            a.stems_dir = str(here / "stems" / "fl")
        r = step("analysis", "build_song_analysis", input_path=a.song, name=a.name, title=a.title, **({"stems_dir": a.stems_dir} if a.stems_dir else {}))
        if not r.ok:
            return 1
        folder = Path(r.value["files"]["analysis"]).parent
        stems = r.value["stems"]
        vocals = stems["vocals"]
        other = stems.get("other", "")
    else:
        info = json.loads((folder / "song_analysis.json").read_text(encoding="utf-8")) if (folder / "song_analysis.json").is_file() else {}
        stems = info.get("stems", {})
        vocals = a.vocals or stems.get("vocals") or str(Path(a.stems_dir or folder) / "vocals.wav")
        other = stems.get("other", "")
    notes = folder / "song_notes.json"  # the research step's findings (skill remix-from-stems, step 1b): identity, form, favourite parts
    midis = [str(f) for f in sorted((folder / "reference_midi").glob("*.mid*"))] if (folder / "reference_midi").is_dir() else []
    if a.plan:  # the concept was written into the plan by hand (sections, kept lines, chop roles): validate it and build from it
        from coproducer import songplan
        edited = songplan.load(a.plan)
        bad = songplan.validate(edited)
        report["steps"].append({"step": "plan", "module": "edited plan", "ok": not bad, "value": {"from": a.plan, "problems": bad}})
        if bad:
            print("plan problems:", "; ".join(bad))
            return 1
        songplan.save(edited, plan)
        print("%-14s %-26s %s" % ("plan", "edited plan", "ok " + a.plan), flush=True)
    else:
        r = step("plan", "build_song_plan", words_file=str(folder / "vocal_words.json"), hits_file=str(folder / "drum_hits.json"), out_plan=str(plan),
                 name="%s_%s" % (a.name, a.style), title=a.title,
                 options={"style": a.style, "bass_file": str(folder / "stem_notes.json"), **({"vocals_file": vocals} if Path(vocals).is_file() else {}),
                          **({"notes_file": str(notes)} if notes.is_file() else {}), **({"midi_files": midis} if midis else {}),
                          **({"every_part": True} if a.every_part else {}), **({"key_pc": a.key_pc} if a.key_pc is not None else {}),
                          **({"other_file": other} if other and Path(other).is_file() else {}),
                          "variety": False if a.no_variety else {**({"seed": a.variety_seed} if a.variety_seed else {}),
                                                                 **({"lock": dict(x.split("=", 1) for x in a.lock)} if a.lock else {}),
                                                                 **({"moods": a.mood} if a.mood else {})}})
        if not r.ok:
            return 1
    r = step("audio", "prepare_remix_audio", plan_file=str(plan), vocals_path=vocals, out_dir=str(work / "audio"),
             **({"other_path": other} if other and Path(other).is_file() else {}))
    if not r.ok:
        return 1
    built = work / ("%s_%s.flp" % (a.name, a.style))
    states = dict(x.split("=", 1) for x in a.serum_state)
    if a.match_sounds:  # each synth part's own sound, matched to the record (skill sound-design-recipes, "Choosing the sound")
        pack = stylepack.load(a.style)
        plan_d = json.loads(plan.read_text(encoding="utf-8"))
        if plan_d.get("style_overrides"):  # the song's own options (a chords option with a pad layer adds the pad part)
            pack = variety.apply_overrides(pack, plan_d["style_overrides"])
        key = plan_d["key_pc"]
        def plays(role: str) -> bool:  # a grammar pack without a role's patterns gets no channel for it; the tech-house engine plays all three
            return pack["engine"] != "grammar" or bool(pack.get(role))
        wanted = [("stab", "stab", "other", plays("chords")), ("arp", "arp", "other", plays("arp")), ("sub", "sub", "bass", plays("sub")),
                  ("pad", "pad", "other", pack["engine"] == "grammar" and bool(pack.get("pad")))]
        report["sounds"] = {}
        match_to = dict(x.split("=", 1) for x in a.match_to)
        for part, role, stem_key, used in wanted:
            src = match_to.get(part, stem_key)
            stem = "" if src == "none" else vocals if src == "vocals" else stems.get(src, src)
            if not used or part in states or not stem or not Path(stem).is_file():
                continue
            name = ("CP - %s %s" % (a.name.replace("_", " ").title(), part.title()))[:64]
            inst = (json.loads(plan.read_text(encoding="utf-8")).get("instruments") or {}).get(part) or {}
            if part == "pad" and not inst and (pack.get("pad") or {}).get("sound"):   # a pad takes a pad's envelope and width, not the stem's notes'
                o = variety.find(variety.load_bank(), pack["pad"]["sound"])
                inst = {"label": o["label"], "measured": o.get("measured")}
            direction = inst.get("measured")
            m = step("sound " + part, "match_part_sound", stem=stem, role=role, name=name, out_dir=str(work / "sounds"),
                     subfolder="sandbox/" + a.name, options={"key_pc": int(key), **({"template_project": a.serum} if Path(a.serum).is_file() else {}),
                                                             **({"direction": direction} if direction else {})})
            if m.ok:
                states[part] = m.value["state"]
                report["sounds"][part] = {k: m.value[k] for k in ("preset", "wav", "best", "match", "words")}
                report["sounds"][part]["left"] = next(r["adjust"] for r in m.value["rounds"] if r.get("round") == m.value["best"])
                report["sounds"][part]["direction"] = inst.get("label") if direction else None   # the demo instrument whose envelope and width it took
    synth = {}
    if a.serum and Path(a.serum).is_file():  # Serum 2 channels: generated sounds ride on them, the rest are the person's presets; Sytrus only when there is none
        synth = {"serum_project": a.serum, **({"serum_presets": dict(x.split("=", 1) for x in a.serum_preset)} if a.serum_preset else {}),
                 **({"serum_states": states} if states else {})}
    elif states:
        print("generated Serum sounds need a project with a Serum 2 channel to ride on (--serum); building without them")
    r = step("build", "build_remix_project", base_project=a.base, sytrus_project=a.sytrus, audio_dir=str(work / "audio"), out_project=str(built), plan_file=str(plan),
             **({"options": synth} if synth else {}))
    if not r.ok:
        return 1
    pack = stylepack.load(a.style)
    produced = work / ("%s_%s_produced.flp" % (a.name, a.style))
    key = json.loads(plan.read_text(encoding="utf-8"))["key_pc"]
    r = step("produce", "apply_production_recipe", project=str(built), out_project=str(produced), recipe=pack["production_recipe"],
             key="C C# D D# E F F# G G# A A# B".split()[key], plan_file=str(plan))
    if not r.ok:
        return 1
    if a.no_render:
        return 0
    r = step("render", "render_via_cli", project=str(produced), out_dir=str(work / "render"), timeout_s=1200)
    if not r.ok:
        return 1
    wav = r.value["path"]
    step("measure", "build_measure_report", path=wav)
    sec = step("sections", "measure_section_levels", path=wav, project=str(produced))
    final = produced
    lo, hi = pack.get("contrast_lu", [3.0, 5.5])

    def worst(res) -> float | None:
        return contrast.drop_over_build(res.value["contrast"] if res.ok else [])

    tgt = tomllib.loads((HOME / pack["targets"]).read_text(encoding="utf-8"))
    floor_lu = float(tgt.get("contrast", {}).get("section_floor_under_drop_lu", 0) or 0)
    lra_max = float(tgt.get("loudness", {}).get("loudness_range_lu", {}).get("max", 0) or 0)

    def trial_lra(mix: str) -> float | None:
        """The loudness range of a trial master of this mixdown (the master compresses the range by a song-dependent amount)."""
        t = call("apply_club_master", path=mix, targets_file=str(HOME / pack["targets"]), out_path=str(work / "trial" / "trial_master.wav"))
        m = call("measure_loudness_range", path=t.value["out"]) if t.ok else None
        return m.value["lra_lu"] if m is not None and m.ok else None
    kinds = [t["name"] for t in json.loads(plan.read_text(encoding="utf-8"))["sections"]]
    hist = [(0.0, worst(sec))]  # (scale, contrast): contrast moves about linearly with the scale of the section-gain map
    need = contrast.shortfall_each(sec.value["sections"] if sec.ok else [], floor_lu)
    scale, raise_db = 0.0, {}
    lra_log: list = []
    lift_turns = 0
    each: dict = {}   # per-build lifts by section name, for drops that sit too far over their own build while the others are in range
    for turn in range(5):  # drops lo..hi LU over their builds, no intro, groove, break or outro further than floor_lu under them, LRA in range
        w = hist[-1][1]
        contrast_ok = w is None or lo <= w <= hi or contrast.stuck(hist) or contrast.blocked(hist, lo, hi)  # report it, do not keep rendering
        lift = contrast.build_lift(hist, lo, hi, raise_db.get("build", 0.0)) if lift_turns < 2 else 0.0
        if lift >= 0.5:  # the drops sit too far over quiet builds and the map only adds contrast: bring the builds up instead
            need, lift_turns = {**need, "build": lift}, lift_turns + 1
        more = contrast.section_lifts(sec.value["contrast"] if sec.ok else [], lo, hi, each) if lift < 0.5 else each
        if contrast_ok and not need and more == each and lra_max:
            lra = trial_lra(wav)
            lra_log.append({"turn": turn, "floor_lu": floor_lu, "trial_master_lra_lu": lra})
            if lra is not None and lra > lra_max and floor_lu > 3.0:  # the floor is a proxy; the master's range is the test
                floor_lu = round(max(3.0, floor_lu - (lra - lra_max + 0.5)), 2)
                need = contrast.shortfall_each(sec.value["sections"] if sec.ok else [], floor_lu)
        if contrast_ok and not need and more == each:
            break
        if not contrast_ok:
            scale = contrast.next_scale(hist, lo, hi)
        lifted = contrast.add_lifts(raise_db, need)
        if contrast_ok and lifted == raise_db and more == each:  # every lift the floor asks for is already at its cap: another render changes nothing
            break
        raise_db, each = lifted, more
        by_kind = {k: v for k, v in raise_db.items() if k in contrast.FLOOR_KINDS + ("build",)}   # build_lift's kind-wide lift
        by_name = {k: round(v + each.get(k, 0.0), 2) for k, v in raise_db.items() if k not in by_kind}
        by_name.update({k: v for k, v in each.items() if k not in by_name})   # floor lifts and per-build lifts, section by section
        role_map = contrast.with_section_lifts(contrast.role_map(sectiongain.DEFAULT_ROLE_GAINS, scale, by_kind, kinds), by_name, kinds)
        gained = work / ("%s_%s_contrast%d.flp" % (a.name, a.style, turn + 1))
        g = step("contrast %d" % (turn + 1), "apply_section_gains", project=str(produced), out_project=str(gained), by_role=role_map or {"scale": 0.0})
        if not g.ok:
            break
        r = step("render %d" % (turn + 1), "render_via_cli", project=str(gained), out_dir=str(work / ("render_c%d" % (turn + 1))), timeout_s=1200)
        if not r.ok:
            break
        wav, final = r.value["path"], gained
        sec = step("sections %d" % (turn + 1), "measure_section_levels", path=wav, project=str(gained))
        hist.append((scale, worst(sec)))
        need = contrast.shortfall_each(sec.value["sections"] if sec.ok else [], floor_lu)
    report["section_raise_db"] = raise_db
    report["section_lifts_db"] = each
    report["contrast_stuck"] = contrast.stuck(hist) or contrast.blocked(hist, lo, hi)
    report["lra_turns"] = lra_log
    report["contrast_history"] = hist
    report["final_project"], report["mixdown"] = str(final), wav
    return finish(wav)

if __name__ == "__main__":
    raise SystemExit(main())

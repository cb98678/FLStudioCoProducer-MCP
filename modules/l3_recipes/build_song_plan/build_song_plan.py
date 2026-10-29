from __future__ import annotations

from pathlib import Path

import json

import soundfile as sf

from coproducer import call, midiref, songanalysis, songform, songplan, vocalchops
from coproducer.result import Result, fail, ok
from coproducer.services import get_service

OPTIONS = ("bpm", "key_pc", "bass_file", "origin_s", "style", "vocals_file", "notes_file", "arrangement", "midi_files", "every_part", "other_file",
           "variety", "mode")


def build_song_plan(words_file: str, hits_file: str, out_plan: str, name: str, title: str = "", options: dict | None = None) -> Result:
    """Write a draft song plan JSON into the sandbox from a song's Whisper word times (vocal_words.json) and drum hits (drum_hits.json).

    The title line is the hook. options: style (a styles/NAME.json pack; the arrangement then follows the song's own form: full verses and
    choruses, the original's instrumentation, whole-phrase chops), vocals_file (the vocal stem: where nobody sings), notes_file (song_notes.json
    from the research step), midi_files (reference MIDI files: each is tested against the record and the best accepted one gives the chords and
    strum), other_file (the harmony stem: the chord roots come from it when the bass stem holds no bass), every_part (true: every verse and every chorus of the song, not the first two of each), arrangement ("chops" for the older template), bpm, key_pc, bass_file (stem_notes.json), origin_s. Errors: E_ARG, E_IO.
    """
    opt = options or {}
    bad = [k for k in opt if k not in OPTIONS]
    if bad:
        return fail("E_ARG", "unknown options: %s" % ", ".join(bad))
    chk = call("check_sandbox_path", path=out_plan, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    try:
        words, hits = json.load(open(words_file, encoding="utf-8")), json.load(open(hits_file, encoding="utf-8"))
        bass = json.load(open(opt["bass_file"], encoding="utf-8"))["bass"] if opt.get("bass_file") else {}
        key_pc = opt.get("key_pc", bass.get("key", {}).get("tonic_pc"))
        if key_pc is None:
            return fail("E_ARG", "give options.key_pc or options.bass_file so the plan has a key")
        down = songanalysis.find_downbeat(songanalysis.hit_rows(hits["hits"]), hits["bpm"], hits["offset_s"])
        if hits.get("from_grid"):  # written by build_song_analysis: the beat tracker's bar line where the drums enter beats the hit heuristic
            down = {**down, "origin_s": hits["origin_s"], "source": "beat_this"}
        origin = opt.get("origin_s", down["origin_s"])
        bass, from_harmony = _bass_or_harmony(bass, opt.get("other_file", ""), float(hits["bpm"]), origin, int(key_pc))
        act = None
        if opt.get("vocals_file"):
            x, rate = sf.read(opt["vocals_file"], dtype="float32", always_2d=True)
            act = [(p["start"], p["end"]) for p in vocalchops.phrases(x.mean(axis=1), rate)]
        first = round((bass["bar0_s"] - origin) / (240.0 / hits["bpm"])) if "bar0_s" in bass else -12
        notes = json.load(open(opt["notes_file"], encoding="utf-8")) if opt.get("notes_file") else None
        midi, tried = _pick_midi(opt.get("midi_files") or [], bass, first, int(key_pc), float(hits["bpm"]))
        var, mode = _variety_opts(opt), opt.get("mode") or _mode_for(bass.get("key") or {}, int(key_pc))
        plan = songanalysis.draft_plan(name, songanalysis.tokens(words["words"]), source_bpm=hits["bpm"], key_pc=key_pc, origin_s=origin,
                                       roots=bass.get("roots_per_bar"), title=title, bpm=opt.get("bpm"), style=opt.get("style", ""),
                                       arrangement=opt.get("arrangement", ""), activity=act, roots_first_bar=first, research=notes, midi=midi,
                                       every_part=bool(opt.get("every_part")), variety=var, mode=mode if mode in ("major", "minor") else "")
        _after_draft(plan, from_harmony, tried, x.mean(axis=1) if act is not None else None, rate if act is not None else 0)
        problems = songplan.validate(plan)
        songplan.save(plan, out_plan)
    except (OSError, ValueError, KeyError) as e:
        return fail("E_IO" if isinstance(e, OSError) else "E_ARG", "%s: %s" % (type(e).__name__, e))
    again = songplan.load(out_plan)
    return ok({"plan": out_plan, "problems": problems, "notes": plan["notes"], "hook": plan["chops"]["hook"], "chops": sorted(plan["chops"]),
               "downbeat": down, "variety": (plan.get("variety") or {}).get("choices"), "sounds": (plan.get("variety") or {}).get("sounds")}, verified=again == json.loads(json.dumps(plan)) and not problems)   # tuples come back as lists


def _mode_for(bass_key: dict, key_pc: int) -> str:
    """The mode of key_pc from the bass stem's key vote: its own mode when the tonics agree, the relative mode when key_pc is its relative
    major or minor, else "" (unknown). A key_pc given by hand once took the bass vote's mode for another tonic: Open Your Heart's bass voted
    G minor, the person's key is F major, and the plan said F minor (2026-10-29)."""
    t, m = bass_key.get("tonic_pc"), bass_key.get("mode") or ""
    if t is None or m not in ("major", "minor"):
        return ""
    if int(t) % 12 == key_pc % 12:
        return m
    if m == "minor" and (int(t) + 3) % 12 == key_pc % 12:
        return "major"
    if m == "major" and (int(t) + 9) % 12 == key_pc % 12:
        return "minor"
    return ""


def _variety_opts(opt: dict):
    """The variety option with the sandbox's remix history filled in (so this plan differs from the last remixes), or False."""
    var = opt.get("variety", {})
    if isinstance(var, dict) and "history" not in var:
        from coproducer import variety
        var = {**var, "history": variety.load_history(Path(get_service("sandbox_root")) / "variety_history.json")}
    return var


def _after_draft(plan: dict, from_harmony: bool, tried: list, mono, rate: int) -> None:
    if from_harmony:
        plan["notes"].append("the record has no bass line: the chord roots come from the harmony stem (each bar's chroma against the key's triads)")
    if tried:
        plan["midi_candidates"] = tried
    if mono is not None and plan.get("slots"):  # place the chop games on the lengths the cuts will really have (a held last note runs on)
        plan["chop_events"] = _games_on_real_lengths(plan, mono, rate)


def _bass_or_harmony(bass: dict, other_file: str, bpm: float, origin: float, key_pc: int) -> tuple[dict, bool]:
    """The bass facts, or, when the bass stem holds no bass ("Girls": a drum machine, a vibraphone riff and a sung bass voice), roots from
    the harmony stem's chroma on the same bar layout (12 bars before the origin)."""
    heard = [r for r in bass.get("roots_per_bar") or [] if r]
    if len(heard) >= 0.3 * max(1, len(bass.get("roots_per_bar") or [])) or not other_file:
        return bass, False
    xo, ro = sf.read(other_file, dtype="float32", always_2d=True)
    bar_s = 240.0 / bpm
    n = int((len(xo) / ro - origin) / bar_s) + 13
    return {**bass, "roots_per_bar": songform.harmony_roots(xo, ro, origin, bar_s, -12, n, key_pc), "bar0_s": origin - 12 * bar_s}, True


def _games_on_real_lengths(plan: dict, mono, rate: int) -> list:
    from coproducer import remixaudio, stylepack
    gp = vocalchops.gaps(mono, rate)
    stretch = stylepack.stretch_of(plan["bpm"], plan.get("vocal_multiple", 1.0), plan["source_bpm"])
    secs = {}
    for name, spec in plan["chops"].items():
        o0, o1 = remixaudio.chop_window(mono, rate, gp, spec)
        secs[name] = o1 - o0
    slots = {k: [tuple(x) if isinstance(x, list) else x for x in v] for k, v in plan["slots"].items()}
    return songform.chop_games(slots, plan["chops"], lambda n: secs[n] / stretch / (240.0 / plan["bpm"]))


def _pick_midi(files: list, bass: dict, first_bar: int, key_pc: int, source_bpm: float) -> tuple:
    """The best accepted reference MIDI as {"file", "fit", "qualities", "strum"} (or None), and every file's test result."""
    roots = songform.scale_roots(bass.get("roots_per_bar") or [], key_pc)
    audio = {first_bar + i: r for i, r in enumerate(roots)}
    tried, best = [], None
    for f in files:
        try:
            m = midiref.read(f)
        except (OSError, ValueError, EOFError) as e:
            tried.append({"file": f, "accepted": False, "why": "unreadable: %s" % e})
            continue
        fit = midiref.fit(m, audio, key_pc, source_bpm) if audio else {"accepted": False, "why": "no bass roots from the record to test against"}
        tried.append({"file": f, **fit})
        if fit["accepted"] and (best is None or fit["root_match"] > best["fit"]["root_match"]):
            bb = fit.get("bar_beats")
            best = {"file": f, "fit": fit, "qualities": midiref.chord_qualities(m, fit["transpose"], bar_beats=bb), "strum": midiref.strum(m, bar_beats=bb)}
    return best, tried

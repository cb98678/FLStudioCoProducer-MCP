from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from coproducer import call, intake
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def _wav(src: Path, dst: Path) -> Path | None:
    """The song as a 44.1 kHz WAV in the sandbox (ffmpeg converts MP3, FLAC, M4A); None when ffmpeg is missing or fails."""
    if src.suffix.lower() == ".wav":
        shutil.copyfile(src, dst)
        return dst
    ff = shutil.which("ffmpeg")
    if not ff:
        return None
    done = subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-ar", "44100", "-c:a", "pcm_s16le", str(dst)], capture_output=True, check=False)
    return dst if done.returncode == 0 and dst.is_file() else None


def build_song_analysis(input_path: str, name: str, title: str = "", quality: str = "high", stems_dir: str = "") -> Result:
    """Everything a remix plan needs from one song, into sandbox/songs/NAME: the song as WAV, four stems (stems_dir with vocals, drums, bass
    and other.wav, as FL's own extract_stems_gui writes them; without it RoFormer vocals and Demucs for the rest), the bar grid (beat_this),
    the words (Whisper), the sung melody (torchcrepe), the drum entrance, the bass key and roots per bar, a vote of three key estimates and the
    song's own sections. Writes vocal_words.json, drum_hits.json, stem_notes.json and song_analysis.json for build_song_plan. A split key vote
    or a drifting tempo is reported in "ask". Errors: E_SANDBOX_VIOLATION, E_NOT_FOUND, E_IO (conversion), E_MODEL, E_NOT_VERIFIED.
    """
    src = Path(input_path)
    if not src.is_file():
        return fail("E_NOT_FOUND", "no audio file at %s" % src.name)
    folder = Path(str(get_service("sandbox_root"))) / "songs" / name
    chk = call("check_sandbox_path", path=str(folder), sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    folder.mkdir(parents=True, exist_ok=True)
    mix = _wav(src, folder / "song.wav")
    if mix is None:
        return fail("E_IO", "could not convert %s to WAV (is ffmpeg on PATH?)" % src.name)
    if stems_dir:
        given = {k: Path(stems_dir) / (k + ".wav") for k in ("vocals", "drums", "bass", "other")}
        stems = {k: str(f) for k, f in given.items() if f.is_file()}
        if not all(k in stems for k in ("vocals", "drums", "bass")):
            return fail("E_NOT_FOUND", "stems_dir needs vocals.wav, drums.wav and bass.wav (other.wav too when it has one)")
    else:
        sep = call("separate_stems_hq", input_path=str(mix), out_dir=str(folder / "stems"), quality=quality)
        if not sep.ok:
            return sep
        stems = sep.value["stems"]
    grid = call("detect_beats_ml", path=str(mix))
    words = call("run_model_op", model="whisper", op="words", timeout_s=1800, args={"path": stems["vocals"]})
    tune = call("transcribe_vocal_melody", path=stems["vocals"])
    mixkey = call("estimate_key_dsp", path=str(mix))
    for r in (grid, words):
        if not r.ok:
            return r
    wv, cleanup = _clean_words(words.value, stems["vocals"])
    g = grid.value
    hits = intake.drum_hits(stems["drums"], g)
    bass = intake.bass_facts(stems["bass"], g, hits["origin_s"])
    vote = intake.key_vote(bass["key"], tune.value["key"] if tune.ok else None, mixkey.value if mixkey.ok else None)
    sections = intake.source_sections(str(mix), g, wv["words"], title)
    ask = ([vote["why"]] if vote["ask"] else []) + (["the tempo drifts up to %.1f%%: a tempo map is needed" % g["max_drift_pct"]] if g["drifting"] else []) \
        + (["the meter is %d/4: the remix grid is 4/4" % g["meter"]] if g["meter"] != 4 else [])
    analysis = {"name": name, "title": title, "song": str(mix), "stems": stems, "grid": {k: v for k, v in g.items() if k not in ("beats", "downbeats")},
                "origin_s": hits["origin_s"], "key": vote, "melody": {"count": tune.value["count"], "range": tune.value["range"], "key": tune.value["key"]} if tune.ok else None,
                "mix_key": mixkey.value if mixkey.ok else None, "sections": sections, "words": len(wv["words"]), "ask": ask, **({"asr_cleanup": cleanup} if cleanup else {})}
    paths = intake.write_files(folder, wv, hits, {**bass, "key": {**(bass["key"] or {}), "tonic_pc": vote["tonic_pc"]}}, analysis)
    return ok({**analysis, "files": paths}, verified=bool(wv["words"]) and g["bar_count"] >= 8)


def _clean_words(value: dict, vocals: str) -> tuple[dict, dict | None]:
    """Whisper's words with its repetition loops redone window by window on the vocal's phrases (asrclean); (words, report or None)."""
    spans, wins = intake.loop_windows(value["words"], vocals)
    if not spans:
        return value, None
    redo = call("run_model_op", model="whisper", op="words", timeout_s=1800, args={"path": vocals, "windows": wins}) if wins else None
    new, rep = intake.splice_words(value, spans, redo.value["words"] if redo is not None and redo.ok else [])
    rep["windows"] = len(wins)
    if redo is not None and not redo.ok:
        rep["redo_error"] = "%s: %s" % (redo.error.code, redo.error.message)
    return new, rep

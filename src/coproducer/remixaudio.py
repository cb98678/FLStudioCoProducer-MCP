"""Make the audio a remix build reads, for the plan loaded into remixplan: the vocal stem stretched to the remix tempo (times the plan's vocal
multiple), the vocal chop one-shots and echo versions, the style's drum kit and bass sample, and the FX bed. Behind tools/techhouse_audio.py and
the module prepare_remix_audio. Needs ffmpeg with the rubberband filter (the full build). Writes only under a folder named sandbox.

Files: vocals_<bpm>.wav, CP_Chop_<name>.wav (and _echo), CP_Kick.wav and the rest of the kit, CP_Reese.wav (the style's bass sample, always A1 on
sampler key 60), FX_bed.wav and techhouse_audio.json (stretch ratio, measured delay of the stretched file, chop and clip spans, levels, style).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

from . import chopfx, cutrefine, fxbed, oneshots, remixplan, vocalchops


class AudioError(RuntimeError):
    """ffmpeg missing or failing, or a path outside the sandbox."""


def stretch(src: str, dst: Path, tempo: float, pitch: float) -> None:
    ff = shutil.which("ffmpeg")
    if not ff:
        raise AudioError("ffmpeg not found on PATH (the full build carries the rubberband filter)")
    if abs(tempo - 1.0) < 1e-6 and abs(pitch - 1.0) < 1e-6:     # the voice at its own speed and pitch: copied, not run through rubberband
        af = "anull"
    else:
        af = "rubberband=tempo=%.6f:pitch=%.6f:formant=preserved:transients=mixed:pitchq=quality" % (tempo, pitch)
    p = subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error", "-i", src, "-af", af, "-c:a", "pcm_s16le", str(dst)], capture_output=True, text=True)
    if p.returncode:
        raise AudioError("ffmpeg failed: " + p.stderr[-600:])


def measured_delay(orig: np.ndarray, st: np.ndarray, rate: int, ratio: float) -> float:
    """Seconds the stretched file's phrases come later than orig_time / ratio (mean over the phrase starts that both files have)."""
    a = vocalchops.phrases(orig.mean(axis=1), rate)
    b = vocalchops.phrases(st.mean(axis=1), rate)
    diffs = []
    for p in a:
        t = p["start"] / ratio
        q = min(b, key=lambda r: abs(r["start"] - t), default=None)
        if q is not None and abs(q["start"] - t) < 0.3:
            diffs.append(q["start"] - t)
    return float(np.median(diffs)) if diffs else 0.0


def snap(x: np.ndarray, rate: int, gp: list[tuple[float, float]], hint0: float, hint1: float, mode: str) -> tuple[float, float]:
    """Cut points in original-stem seconds: the start on a syllable onset near hint0, the end per vocalchops.snap_end (word onset or end of phrase)."""
    lo, hi = max(0.0, hint0 - 1.0), min(len(x) / rate, hint1 + 1.5)
    ons = vocalchops.onsets(x, rate, lo, hi, min_gap=0.05)
    s = vocalchops.snap_start(ons, hint0)
    e = vocalchops.snap_end(ons, gp, hint1, mode)
    return s, max(e, s + 0.15)


VOICE_TARGET_DB = -18.0  # active level a quiet vocal stem is raised to (the stems the person's balances were set on sit at -16 to -18)
VOICE_PEAK_DB = -1.0     # the lift never takes the stretched stem's peak past this


def active_level_db(x: np.ndarray, rate: int, window_s: float = 0.05, within_db: float = 20.0) -> float:
    """The level of the voice where it speaks or sings: the power mean of the 50 ms windows within 20 dB of the 95th percentile window, so
    the silences between lines do not count."""
    m = x.mean(axis=1) if x.ndim > 1 else x
    hop = max(1, int(rate * window_s))
    n = len(m) // hop
    if n == 0:
        return -120.0
    db = 20 * np.log10(np.sqrt((m[: n * hop].reshape(n, hop) ** 2).mean(axis=1)) + 1e-9)
    act = db[db > np.percentile(db, 95) - within_db]
    return float(10 * np.log10(np.mean(10 ** (act / 10)) + 1e-12))


def voice_lift_db(x: np.ndarray, rate: int, target_db: float = VOICE_TARGET_DB, peak_db: float = VOICE_PEAK_DB) -> float:
    """dB to raise a quiet vocal stem toward target_db, never lowering one and never past peak_db. Girlish Type Men's spoken voice sat at
    -29.9 dB active and measured 20.4 LU under the mix in the first drop, buried, while a stem at -18.4 sat 7.8 LU under (2026-10-29)."""
    room = peak_db - 20 * np.log10(float(np.max(np.abs(x))) + 1e-12)
    return round(max(0.0, min(target_db - active_level_db(x, rate), room)), 2)


CLIP_TAIL_S = 0.5  # remix seconds of decay kept after a whole verse or chorus when no word follows soon (the person's edit, 2026-10-26)


def next_onset(x: np.ndarray, rate: int, t: float, reach: float = 0.25) -> float:
    """The syllable onset in the audio nearest a recogniser's word start t (within reach), else t."""
    ons = [o for o in vocalchops.onsets(x, rate, max(0.0, t - reach - 0.1), t + reach + 0.1, min_gap=0.05) if abs(o - t) <= reach]
    return min(ons, key=lambda o: abs(o - t)) if ons else t


def whole_end(x: np.ndarray, rate: int, e: float, mode: str, last_word: str = "", next_t: float | None = None, hint: float | None = None) -> float:
    """Carry a cut's end through its last word, and never into the next one.

    Phrase end: to where the voice really stops (a held vowel, cutrefine.voice_end). Either mode: through a closing s or z (cutrefine.final_s);
    an onset finder takes the hiss of "places" for the next word's onset, so a word-mode cut before "where" lost the s (2026-10-25). With the
    next sung word's time, the end stops at that word's onset in the audio: a legato line has no gap, and a phrase-mode snap that looks for
    one ran on into "oh i've" after "oasis". `hint` (the recogniser's end of the last word) is where the search starts again then."""
    limit = None
    if next_t is not None:
        limit = next_onset(x, rate, next_t) - 0.01
        if e > limit and hint is not None:
            e = min(hint, limit)
    e2 = e
    if mode == "phrase":
        e2 = max(e2, cutrefine.voice_end(x, rate, max(0.0, e - 0.05)))
    if last_word.endswith(("s", "z")):
        e2 = max(e2, cutrefine.final_s(x, rate, e))
    if limit is None:
        return min(e2, e + 0.8)
    if limit - e2 > 0.05 and _sounding(x, rate, e2, limit, e):
        e2 = limit  # the last word is held on into the next one (a dip inside the note is not its end): keep it all
    return min(e2, limit)


def _sounding(x: np.ndarray, rate: int, a: float, b: float, ref_t: float, within_db: float = 18.0) -> bool:
    """True when the voice never stops from a to b: no 30 ms window there falls more than within_db under the loudest of the half second
    before ref_t. A held note that dips stays above it; the silence after a final s ("places", then a breath) does not."""
    seg, ref = x[int(a * rate):int(b * rate)], x[max(0, int((ref_t - 0.5) * rate)):int(ref_t * rate)]
    if len(seg) < int(0.03 * rate) or len(ref) < int(0.03 * rate):
        return False
    top = float(vocalchops.envelope_db(ref, rate, 0.03)[0].max())
    return float(vocalchops.envelope_db(seg, rate, 0.03)[0].min()) > top - within_db


def next_start(x: np.ndarray, rate: int, t0: float | None, t1: float | None, word: str = "") -> float | None:
    """The next sung word's real start: the recogniser's, unless it stretched that word back over a held note (cutrefine.word_start)."""
    if t0 is None:
        return None
    return cutrefine.word_start(x, rate, t0, t1, word=word) if t1 is not None else t0


def chop_window(mono: np.ndarray, rate: int, gp: list, spec: dict) -> tuple[float, float]:
    """A chop's cut in the original vocal (seconds): snapped to the syllables, its start moved past a recogniser's stretched first word
    and past a pickup slurred from the note before, its end carried through the last word and never into the next one. The plan uses it
    too, so chop games are placed on the lengths the cuts will have."""
    o0, o1 = snap(mono, rate, gp, spec["start"], spec["end"], spec["end_mode"])
    if spec.get("first_t1"):
        o0 = max(o0, cutrefine.word_start(mono, rate, spec["start"], spec["first_t1"], word=(spec.get("words") or " ").split()[0]))
    if spec.get("after_pickup") and cutrefine.sung_into(mono, rate, spec["start"]):
        o0 = max(o0, next_onset(mono, rate, spec["after_pickup"]) - 0.02)  # a pickup slurred from the note before stays off the chop
    o1 = whole_end(mono, rate, o1, spec["end_mode"], (spec.get("words") or "").split()[-1:][0] if spec.get("words") else "",
                   next_t=next_start(mono, rate, spec.get("next_t0"), spec.get("next_t1"), spec.get("next", "")), hint=spec["end"])
    return o0, max(o1, o0 + 0.15)


def stretch_segment(seg: np.ndarray, rate: int, ratio: float, pitch: float, tmp: Path, pad_s: float = 0.04) -> np.ndarray:
    """Time-stretch one cut on its own, so no neighbouring word can smear into it (stretching the whole stem first let the tail of "-key" leak into the front of "drowns").

    The cut is padded with silence, stretched, and the padding is trimmed again.
    """
    pad = np.zeros((int(pad_s * rate), seg.shape[1]), dtype=seg.dtype)
    src, dst = tmp / "seg_in.wav", tmp / "seg_out.wav"
    sf.write(str(src), np.concatenate([pad, seg, pad]), rate, subtype="FLOAT")
    stretch(str(src), dst, ratio, pitch)
    y, _ = sf.read(str(dst), dtype="float32", always_2d=True)
    lead = int(pad_s / ratio * rate)
    return y[lead : lead + int(len(seg) / ratio) + int(0.01 * rate)]


def shape(seg: np.ndarray, rate: int) -> np.ndarray:
    """High-pass at 90 Hz, 5 ms fade in, 35 ms fade out, peak at -2 dBFS."""
    hp = butter(2, 90, btype="high", fs=rate, output="sos")
    seg = sosfilt(hp, seg, axis=0)
    k_in, k_out = int(0.005 * rate), int(0.035 * rate)
    seg[:k_in] *= np.linspace(0, 1, k_in)[:, None]
    seg[-k_out:] *= np.linspace(1, 0, k_out)[:, None]
    return seg * (10 ** (-2.0 / 20) / (np.max(np.abs(seg)) + 1e-9))


def prepare(outdir: str | Path, vocals: str, cuts: str = "", pitch: float | None = None, log: Callable[..., None] = print, stems: dict | None = None) -> dict:
    """Write every audio file of the remix into outdir and return the info that techhouse_audio.json holds. pitch is the rubberband pitch ratio
    (a tuning correction measured for the stem); None takes the plan's (remixplan.PITCH_RATIO, 1.0 unless the plan says otherwise). stems
    gives the other stems the plan's long clips play ({"other": path}: the original's guitars and keys), stretched the same way as the vocal."""
    out = Path(outdir)
    pitch = remixplan.PITCH_RATIO if pitch is None else pitch
    if "sandbox" not in [p.lower() for p in out.resolve().parts]:
        raise AudioError("refusing to write %s: output must be under a folder named sandbox" % out)
    out.mkdir(parents=True, exist_ok=True)
    ratio = remixplan.STRETCH
    stretched = out / ("vocals_%d.wav" % round(remixplan.BPM))
    stretch(vocals, stretched, ratio, pitch)
    orig, rate = sf.read(vocals, dtype="float32", always_2d=True)
    st, rate2 = sf.read(str(stretched), dtype="float32", always_2d=True)
    if rate != rate2:
        raise AudioError("the stretched vocal came back at %d Hz, not %d" % (rate2, rate))
    lift = voice_lift_db(st, rate)
    if lift >= 0.5:   # a quiet stem plays at the level the person's balances were set on (the chops are peak-normalized already)
        st = st * 10 ** (lift / 20)
        sf.write(str(stretched), st, rate, subtype="PCM_16")
        log("vocal stem raised %.1f dB to an active level of %.1f dB" % (lift, active_level_db(st, rate)))
    delay = measured_delay(orig, st, rate, ratio)
    log("stretched %.2fs -> %.2fs, expected %.2fs, delay %.1f ms" % (len(orig) / rate, len(st) / rate, len(orig) / rate / ratio, delay * 1000))

    mono = orig.mean(axis=1)
    gp = vocalchops.gaps(mono, rate)
    cuts = json.loads(Path(cuts).read_text(encoding="utf-8")) if cuts else {"chops": {}, "clips": []}
    tmp = out / "tmp_seg"
    tmp.mkdir(exist_ok=True)
    chops = {}
    for name, spec in remixplan.CHOPS.items():
        c = cuts["chops"].get(name)
        o0, o1 = (c["start"], c["end"]) if c else chop_window(mono, rate, gp, spec)
        rep = vocalchops.cut_report(mono, rate, o0, o1)
        inner = [(max(g0, o0) - o0, min(g1, o1) - o0) for g0, g1 in gp if g1 > o0 and g0 < o1 and g0 > o0 + 0.05 and g1 < o1 - 0.05]
        seg = orig[int(o0 * rate) : int(o1 * rate)].copy()
        k = int(0.004 * rate)
        seg[:k] *= np.linspace(0, 1, k)[:, None]
        seg[-k:] *= np.linspace(1, 0, k)[:, None]
        if spec.get("max_gap") and inner:
            seg = vocalchops.squeeze_gaps(seg, rate, inner, spec["max_gap"] * ratio)
        x = shape(stretch_segment(seg, rate, ratio, pitch, tmp), rate)
        path = out / ("CP_Chop_%s.wav" % name)
        sf.write(str(path), x, rate, subtype="PCM_16")
        info_c = {"file": path.name, "orig_start_s": round(o0, 3), "orig_end_s": round(o1, 3), "dur_s": round(len(x) / rate, 3), "hint": [spec["start"], spec["end"], spec["end_mode"]], "words": spec.get("words"), "check": rep,
                  "asr_start_ok": c["start_ok"] if c else None, "asr_end_ok": c["end_ok"] if c else None}
        chops[name] = info_c
        log("chop %-10s orig %8.3f-%8.3f  %.2fs  %-22s asr start/end: %s/%s" % (name, o0, o1, len(x) / rate, spec.get("words", ""), info_c["asr_start_ok"], info_c["asr_end_ok"]))
        if name in remixplan.ECHOED:
            e = chopfx.echo(x, rate, remixplan.BPM)
            e *= 10 ** (-2.0 / 20) / (np.max(np.abs(e)) + 1e-9)
            sf.write(str(out / ("CP_Chop_%s_echo.wav" % name)), e, rate, subtype="PCM_16")
            chops[name + "_echo"] = {"file": "CP_Chop_%s_echo.wav" % name, "dur_s": round(len(e) / rate, 3)}
    shutil.rmtree(tmp, ignore_errors=True)
    clips = []
    for n, (remix_bar, orig_bar, h0, h1, label, mode, *rest) in enumerate(remixplan.VOCAL_CLIPS):
        stem = rest[0] if rest else "vocals"
        c = cuts["clips"][n] if n < len(cuts["clips"]) else None
        if mode == "bars":  # an instrumental span: exactly the source bar lines, short fades in the build
            o0, o1 = max(0.0, h0), h1
        else:
            o0, o1 = (c["start"], c["end"]) if c else snap(mono, rate, gp, h0, h1, mode)
            if not c and n < len(remixplan.CLIP_WORDS):
                cw = remixplan.CLIP_WORDS[n]
                if cw.get("head_t1"):
                    o0 = max(o0, cutrefine.word_start(mono, rate, h0, cw["head_t1"], word=(cw.get("head") or " ").split()[0]))
                nt = next_start(mono, rate, cw.get("next_t0"), cw.get("next_t1"), cw.get("next_w", ""))
                o1 = whole_end(mono, rate, o1, mode, (cw.get("tail") or "").split()[-1:][0] if cw.get("tail") else "", next_t=nt, hint=h1)
                if mode == "phrase" and (nt is None or nt - o1 > 1.0):  # the decay after the last word, as the person lengthened the clips
                    o1 = o1 + CLIP_TAIL_S * ratio if nt is None else min(o1 + CLIP_TAIL_S * ratio, nt - 0.05)
                o1 = max(o1, o0 + 0.15)
        clips.append({"label": label, "stem": stem, "orig_start_s": round(o0, 3), "orig_end_s": round(o1, 3), "hint": [h0, h1, mode],
                      "check": vocalchops.cut_report(mono, rate, o0, o1) if stem == "vocals" else None,
                      "asr_start_ok": c["start_ok"] if c else None, "asr_end_ok": c["end_ok"] if c else None})
        log("clip %-24s %-6s orig %8.3f-%8.3f (hint %.2f-%.2f)" % (label, stem, o0, o1, h0, h1))
    need = {c["stem"] for c in clips} - {"vocals"}
    for stem in sorted(need):
        src = (stems or {}).get(stem)
        if not src or not Path(src).is_file():
            raise AudioError("the plan plays the %s stem but no %s file was given" % (stem, stem))
        stretch(src, out / ("%s_%d.wav" % (stem, round(remixplan.BPM))), ratio, pitch)
        log("stretched the %s stem" % stem)

    style = remixplan.STYLE or {}
    oneshots.write_kit(out, style.get("kit"))
    if style.get("kick_sub_shelf"):  # a style's kick with less sub (house: the person's pick by ear)
        oneshots.shelve(out / "CP_Kick.wav", float(style["kick_sub_shelf"]["hz"]), float(style["kick_sub_shelf"]["db"]))
    oneshots.write_wav(out / "CP_Reese.wav", oneshots.voice(style["bass_sample"]) if style.get("bass_sample") else oneshots.reese_pluck(), peak_db=-1.0)

    bed = fxbed.render_bed(remixplan.fx_cues(), remixplan.BPM, remixplan.TOTAL_BARS * 4 + 8)
    peak = float(np.max(np.abs(bed)))
    if peak > 0.9:
        bed *= 0.9 / peak
    sf.write(str(out / "FX_bed.wav"), bed.astype(np.float32), fxbed.SR, subtype="PCM_16")

    info = {"stretch": ratio, "pitch": pitch, "delay_s": delay, "bpm": remixplan.BPM, "rate": rate, "chops": chops, "clips": clips,
            "fx_peak_db": round(20 * np.log10(peak + 1e-12), 1), "vocal_seconds": round(len(st) / rate, 3), "vocal_lift_db": lift if lift >= 0.5 else 0.0}
    info["style"] = style.get("name", "tech_house")
    (out / "techhouse_audio.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    log("wrote", out, "files", len(os.listdir(out)))
    return info



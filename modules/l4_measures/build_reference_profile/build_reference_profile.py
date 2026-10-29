from __future__ import annotations

import json
import shutil
import statistics
import subprocess
import tomllib
from pathlib import Path

from coproducer import call, dsp, tonal
from coproducer.result import Result, fail, ok
from coproducer.services import get_service

SOUNDFILE_TYPES = {".wav", ".flac", ".mp3", ".aif", ".aiff", ".ogg"}


def _readable(src: Path, scratch: Path) -> str | None:
    """The file itself when soundfile reads it, else a WAV decoded by ffmpeg into scratch (m4a, aac and the like)."""
    if src.suffix.lower() in SOUNDFILE_TYPES:
        return str(src)
    ff = shutil.which("ffmpeg")
    dst = scratch / (src.stem + ".wav")
    if ff and not dst.is_file():
        scratch.mkdir(parents=True, exist_ok=True)
        subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-ar", "44100", str(dst)], capture_output=True, check=False)
    return str(dst) if dst.is_file() else None


def _span(rows: list, key: str) -> dict:
    v = [r[key] for r in rows if isinstance(r.get(key), (int, float))]
    return {"median": round(statistics.median(v), 2), "min": round(min(v), 2), "max": round(max(v), 2)} if v else {}


def build_reference_profile(paths: list, out_file: str, targets_out: str = "", base_targets: str = "targets/club_release.toml") -> Result:
    """Measure each reference track and write a profile JSON: per-track loudness, true peak, crest, loudness range, correlation, band levels,
    and the tonal profile (mean and spread per third-octave band). With targets_out, also write a targets TOML measured from them: base_targets
    with loudness at the references' median, crest and loudness-range windows around theirs; the true-peak ceiling stays the base's.
    Errors: E_SANDBOX_VIOLATION, E_NOT_FOUND, E_IO (a file neither soundfile nor ffmpeg can read).
    """
    root = str(get_service("sandbox_root"))
    for p in [out_file] + ([targets_out] if targets_out else []):
        chk = call("check_sandbox_path", path=p, sandbox_root=root)
        if not chk.ok:
            return chk
    out = Path(call("check_sandbox_path", path=out_file, sandbox_root=root).value["resolved"])
    missing = [p for p in paths if not Path(p).is_file()]
    if missing:
        return fail("E_NOT_FOUND", "no file at %s" % ", ".join(Path(m).name for m in missing))
    rows, levels = [], []
    for p in paths:
        src = _readable(Path(p), out.parent / "decoded")
        rep = call("build_measure_report", path=src) if src else None
        if rep is None or not rep.ok:
            return fail("E_IO", "cannot read %s" % Path(p).name)
        x, rate = dsp.load_audio(src)
        bands = tonal.band_levels(x, rate)
        levels.append(bands)
        v = rep.value
        rows.append({"file": str(p), "lufs": v["loudness"]["lufs"], "true_peak_dbtp": v["true_peak"]["true_peak_dbtp"], "crest_db": v["crest"]["crest_db"],
                     "lra_lu": v.get("range", {}).get("lra_lu"), "correlation": v.get("correlation", {}).get("correlation"), "bands_db": bands})
    summary = {k: _span(rows, k) for k in ("lufs", "true_peak_dbtp", "crest_db", "lra_lu", "correlation")}
    prof = {"name": out.stem, "tracks": rows, "tonal": tonal.profile(levels), "summary": summary}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(prof, indent=1), encoding="utf-8")
    written = {"profile": str(out)}
    if targets_out:
        written["targets"] = _write_targets(Path(base_targets), Path(call("check_sandbox_path", path=targets_out, sandbox_root=root).value["resolved"]), out, summary)
    return ok({**written, "summary": summary, "tracks": len(rows)}, verified=Path(out).is_file())


def _write_targets(base: Path, dst: Path, profile: Path, s: dict) -> str:
    t = tomllib.loads(base.read_text(encoding="utf-8"))
    t["meta"] = {"name": dst.stem, "source": "measured from %d reference tracks the person chose (%s), on top of %s" % (len(json.loads(profile.read_text(encoding="utf-8"))["tracks"]), profile.name, base.name)}
    t.setdefault("loudness", {})["integrated_lufs"] = s["lufs"]["median"]
    if s.get("crest_db"):
        t.setdefault("dynamics", {})["crest_factor_db"] = {"min": round(max(5.5, s["crest_db"]["min"] - 0.5), 1), "max": round(s["crest_db"]["max"] + 1.0, 1)}
    if s.get("lra_lu"):
        t["loudness"]["loudness_range_lu"] = {"min": round(max(1.0, s["lra_lu"]["min"] - 1.0), 1), "max": round(s["lra_lu"]["max"] + 1.0, 1)}
    t.setdefault("spectrum", {})["reference_profile"] = str(profile)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(_toml(t), encoding="utf-8")
    return str(dst)


def _toml(d: dict) -> str:
    def val(v):
        if isinstance(v, dict):
            return "{ %s }" % ", ".join("%s = %s" % (k, val(x)) for k, x in v.items())
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return repr(v)
        if isinstance(v, list):
            return "[%s]" % ", ".join(val(x) for x in v)
        return json.dumps(str(v))
    return "\n".join("[%s]\n%s\n" % (sec, "\n".join("%s = %s" % (k, val(v)) for k, v in body.items())) for sec, body in d.items() if isinstance(body, dict))

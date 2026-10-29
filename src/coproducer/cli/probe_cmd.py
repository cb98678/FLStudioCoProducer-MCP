"""coproducer probe: the Gate 0 checks that need a real machine. Pure functions take their dependencies as arguments."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from . import detect

SIZES = (64, 200, 240, 256, 512, 1024, 2048, 4096)


def install_fl(home: Path, data_dir: Path, mutating: bool) -> str:
    """Copy the in-FL probe into its own Hardware folder, with the MUTATING flag set as asked."""
    src = (home / "probes" / "device_probe.py").read_text(encoding="utf-8")
    src = re.sub(r"^MUTATING = \w+", "MUTATING = %s" % mutating, src, count=1, flags=re.M)
    dst = Path(data_dir) / "Settings" / "Hardware" / "coproducer-probe" / "device_coproducer_probe.py"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src, encoding="utf-8", newline="\n")
    return str(dst)


def collect_report(client, mutating: bool = False, timeout_s: float = 20.0, probe_args: dict | None = None) -> dict:
    """Ask the running bridge script to run every probe and return the report in the same shape the old file had."""
    listed = client.request("bridge_probe", {"mutating": mutating}, timeout_s=timeout_s)
    if not listed.ok:
        return {"_error": listed.error.message}
    report = {}
    for name in listed.value:
        got = client.request("bridge_probe", {"name": name, "mutating": mutating, "args": (probe_args or {}).get(name, {})}, writes=mutating, timeout_s=timeout_s)
        if not got.ok:
            report[name] = {"ok": False, "error": got.error.message}
        else:
            report[name] = {"ok": True, "value": got.value}
    report["_meta"] = {"mutating": mutating}
    return report


def report_path(data_dir: Path) -> Path:
    return Path(data_dir) / "Settings" / "Hardware" / "coproducer-probe" / "probe_report.json"


def inventory_diff(real: dict, planned: dict) -> dict:
    """Compare the callables FL reports with the functions the plan's stub inventory lists (keys like 'mixer.getTrackVolume')."""
    want = set(planned)
    have = {"%s.%s" % (m, n) for m, names in real.items() for n in (names or [])}
    scoped = {k for k in want if k.split(".")[0] in real and real[k.split(".")[0]] is not None}
    return {"planned_but_missing": sorted(scoped - have), "present_but_unplanned": sorted(k for k in have if k.split(".")[0] in {w.split(".")[0] for w in want} and k not in want),
            "modules_not_importable": sorted(m for m, v in real.items() if v is None)}


def summarize_report(report: dict, planned: dict) -> str:
    lines = []
    for name, row in sorted(report.items()):
        if name.startswith("_") or name == "inventory":
            continue
        lines.append("%-14s %s" % (name, "ok " + json.dumps(row["value"])[:300] if row["ok"] else "FAILED " + row["error"]))
    inv = report.get("inventory", {})
    if inv.get("ok"):
        d = inventory_diff(inv["value"], planned)
        lines.append("inventory      %d planned functions missing, %d present but unplanned, modules not importable: %s" % (
            len(d["planned_but_missing"]), len(d["present_but_unplanned"]), d["modules_not_importable"] or "none"))
        lines += ["  missing: " + ", ".join(d["planned_but_missing"][:40])] if d["planned_but_missing"] else []
    lines.append("writes tested  %s" % report.get("_meta", {}).get("mutating"))
    return "\n".join(lines)


def ping(client, runs: int = 5) -> dict:
    """G0-1: ping through the real ports; passes when every round trip answers inside 2 seconds."""
    times = []
    for _ in range(runs):
        t = time.monotonic()
        r = client.ping(timeout_s=2.0)
        if not r.ok:
            return {"passed": False, "message": r.error.message}
        times.append(round((time.monotonic() - t) * 1000, 1))
    return {"passed": True, "ms": times, "info": r.value}


def throughput(client, sizes=SIZES) -> dict:
    """G0-6: send requests whose op name is `size` characters long. FL answers 'unknown op <name>', so the reply proves the bytes arrived intact."""
    good, bad = [], []
    for n in sizes:
        name = ("echo_" + "x" * n)[:n]
        r = client.request(name, {}, timeout_s=3.0)
        echoed = (not r.ok) and r.error.code == "E_NOT_FOUND" and name in r.error.message
        (good if echoed else bad).append(n)
    return {"passed": not bad, "intact": good, "failed": bad, "safe_frame_size": max(good) if good else None}


def render(call, project: Path, out_dir: Path) -> dict:
    """G0-5: render a saved sandbox copy through the FL command line and report loudness."""
    r = call("render_via_cli", project=str(project), out_dir=str(out_dir))
    if not r.ok:
        return {"passed": False, "message": "%s %s" % (r.error.code, r.error.message)}
    lufs = call("measure_integrated_loudness", path=r.value["path"])
    return {"passed": lufs.ok, "wav": r.value["path"], "loudness": lufs.value if lufs.ok else lufs.error.message}


def desktop(call) -> dict:
    """G2-5 precheck: can the tool see FL Studio, its scale and a screenshot?"""
    ready = call("check_desktop_ready")
    if not ready.ok:
        return {"passed": False, "message": "%s %s" % (ready.error.code, ready.error.message)}
    shot = call("take_screenshot", out_path=str(Path("sandbox") / "screens" / "probe.png"))
    return {"passed": shot.ok, "window": ready.value, "screenshot": shot.value["path"] if shot.ok else shot.error.message}


def where_is_data(cfg: dict) -> Path:
    return Path(cfg["fl"].get("data_dir") or detect.fl_data_dir())


def _tone_scale(path: str) -> str:
    """Eight half-second notes of a C major scale as a mono WAV."""
    import numpy as np
    from ..synth import RATE, sine, to_wav
    freqs = (261.63, 293.66, 329.63, 349.23, 392.0, 440.0, 493.88, 523.25)
    return to_wav(path, np.concatenate([sine(f, 0.5, 0.5) for f in freqs]), RATE)


def _mixture(path: str) -> str:
    """Two bars of drums over a chord, stereo."""
    import numpy as np
    from ..synth import RATE, chord, drum_loop, to_wav
    d = drum_loop(140.0, 2)
    c = chord([220.0, 277.18, 329.63], d.shape[0] / RATE)[: d.shape[0]]
    return to_wav(path, 0.5 * d + 0.3 * np.pad(c, ((0, d.shape[0] - c.shape[0]), (0, 0))), RATE)


def models(call, work: Path) -> dict:
    """G0-10: the smoke test of each installed model, through the real tools. A missing environment shows as skipped, not failed."""
    work.mkdir(parents=True, exist_ok=True)
    mix, scale = _mixture(str(work / "mixture.wav")), _tone_scale(str(work / "scale.wav"))
    runs = {"demucs": lambda: call("separate_stems", input_path=mix, out_dir=str(work / "stems"), stems=4),
            "basicpitch": lambda: call("transcribe_to_midi", input_path=scale),
            "acestep": lambda: call("generate_audio", prompt="short test loop", out_dir=str(work / "gen"), duration_s=10.0),
            "flamingo": lambda: call("critique_audio", path=mix)}
    out = {}
    for name, run in runs.items():
        r = run()
        skipped = not r.ok and (r.error.code == "E_UNSUPPORTED_API" or (r.error.code == "E_MODEL" and "environment" in r.error.message))
        status = "skipped" if skipped else ("failed" if not r.ok else ("fallback" if r.meta.get("fallback") else "passed"))
        out[name] = {"status": status, "detail": r.error.message if not r.ok else (r.meta.get("model_error_detail") or "ok")}
    notes = call("transcribe_to_midi", input_path=scale)
    if notes.ok:
        out["basicpitch"]["notes"] = notes.value["count"]
        out["basicpitch"]["status"] = "passed" if abs(notes.value["count"] - 8) <= 1 else "failed"
    out["passed"] = all(v["status"] != "failed" for v in out.values() if isinstance(v, dict))
    return out


_TEMPO_TOOL = [{"type": "function", "function": {"name": "set_tempo", "description": "Set the project tempo in beats per minute.",
                "parameters": {"type": "object", "properties": {"bpm": {"type": "number"}}, "required": ["bpm"]}}}]


def brain(call) -> dict:
    """G0-11: one plain reply and one tool call from the local LLM in config [llm]. Reports time, tokens and what came back."""
    out = {}
    for name, kwargs in (("plain", {"prompt": "Reply with the single word: ready"}),
                         ("tool_call", {"prompt": "Set the tempo to 128 BPM.", "tools": _TEMPO_TOOL})):
        t = time.monotonic()
        r = call("call_agent_llm", max_tokens=2048, **kwargs)
        row = {"seconds": round(time.monotonic() - t, 1)}
        if not r.ok:
            row.update(status="failed", detail="%s %s" % (r.error.code, r.error.message))
        else:
            msg = r.value["message"]
            calls = msg.get("tool_calls") or []
            row.update(status="passed", finish=r.value["finish_reason"], tokens=r.value["usage"], text=(msg.get("content") or "")[:120],
                       thinking=bool(msg.get("reasoning") or msg.get("reasoning_content")), tool_calls=[c.get("function") for c in calls])
            if name == "tool_call":
                row["status"] = "passed" if calls and calls[0]["function"]["name"] == "set_tempo" else "failed"
        out[name] = row
    out["passed"] = all(v["status"] == "passed" for v in out.values())
    return out


_LOOP_TOOLS = [
    {"type": "function", "function": {"name": "set_tempo", "description": "Propose a new project tempo in BPM.",
                                       "parameters": {"type": "object", "properties": {"bpm": {"type": "number"}}, "required": ["bpm"]}}},
    {"type": "function", "function": {"name": "adjust_master_gain", "description": "Propose a change of the master level in dB (negative is quieter).",
                                       "parameters": {"type": "object", "properties": {"db": {"type": "number"}}, "required": ["db"]}}},
    {"type": "function", "function": {"name": "adjust_eq_band", "description": "Propose an EQ change on one band: low, mid or high, in dB.",
                                       "parameters": {"type": "object", "properties": {"band": {"type": "string", "enum": ["low", "mid", "high"]}, "db": {"type": "number"}},
                                                      "required": ["band", "db"]}}},
]
_LOOP_SYSTEM = ("You are a mixing assistant. You get measurements of a short audio loop and a target. "
                "Call the tools for the changes you would make, or reply 'no change' in words if none is needed. Proposals only.")


def check_proposal(fn: dict, tools: list) -> dict:
    """Check one tool call from the LLM against the tool's own JSON schema. Local models do not always respect an enum."""
    import jsonschema
    schema = next((t["function"]["parameters"] for t in tools if t["function"]["name"] == fn.get("name")), None)
    if schema is None:
        return {**fn, "valid": False, "problem": "no such tool"}
    try:
        jsonschema.validate(json.loads(fn.get("arguments") or "{}"), schema)
    except (ValueError, jsonschema.ValidationError) as e:
        return {**fn, "valid": False, "problem": str(getattr(e, "message", e))[:160]}
    return {**fn, "valid": True}


def _listener_notes(value: dict) -> str:
    """The critique text, from the model or from the rule-based fallback."""
    return value.get("text") or "\n".join("[%s] %s" % (o.get("severity"), o.get("message")) for o in value.get("observations", []))


def loop(call, work: Path, prompt: str = "driving techno loop, dark, punchy kick, rolling bassline", bpm: float = 128.0, duration_s: float = 10.0) -> dict:
    """G0-12: generate a loop, measure it, check the tempo it came back with, and let the local LLM propose changes. Nothing is applied."""
    out, t0 = {"steps": {}}, time.monotonic()

    def done(name: str, r, **extra) -> bool:
        out["steps"][name] = {"ok": r.ok, "seconds": round(time.monotonic() - t0, 1), **({"error": "%s %s" % (r.error.code, r.error.message)} if not r.ok else {}), **extra}
        return r.ok

    gen = call("generate_audio", prompt=prompt, out_dir=str(Path(work) / "gen"), duration_s=duration_s, bpm=bpm)
    if not done("generate", gen):
        return {**out, "passed": False}
    path = gen.value["paths"][0]
    out["audio"], out["requested_bpm"] = path, bpm
    rep, tempo, key = call("build_measure_report", path=path), call("estimate_bpm_dsp", path=path, hint_bpm=bpm), call("estimate_key_dsp", path=path)
    done("measure", rep)
    done("tempo", tempo, requested=bpm, measured=tempo.value["bpm"] if tempo.ok else None, matched_hint=tempo.value.get("matched_hint") if tempo.ok else None, candidates=tempo.value["candidates"][:4] if tempo.ok else None)
    done("key", key, value=key.value if key.ok else None)
    if not rep.ok:
        return {**out, "passed": False}
    out["report"] = rep.value
    t0 = time.monotonic()
    heard = call("critique_audio", path=path)
    done("listen", heard, source=heard.value.get("source") if heard.ok else None)
    notes = _listener_notes(heard.value) if heard.ok else ""
    out["listener_notes"] = notes
    ask = "Target: about -14 LUFS integrated, true peak below -1 dBTP, balanced spectrum.\nMeasurements:\n" + json.dumps(rep.value)[:3500]
    if notes:
        ask += "\nListener notes (an audio model's opinion, not measured; the measurements win when they disagree):\n" + notes[:1200]
    t0 = time.monotonic()
    brain_reply = call("call_agent_llm", prompt=ask, system=_LOOP_SYSTEM, tools=_LOOP_TOOLS, max_tokens=2048)
    if done("brain", brain_reply):
        msg = brain_reply.value["message"]
        out["proposals"] = [check_proposal(c.get("function") or {}, _LOOP_TOOLS) for c in (msg.get("tool_calls") or [])]
        out["brain_text"] = (msg.get("content") or "")[:400]
    out["passed"] = all(v["ok"] for v in out["steps"].values())
    return out


_GAIN_TOOL = [{"type": "function", "function": {"name": "adjust_master_gain", "description": "Change the master fader by this many dB (positive is louder). Between -24 and 24.",
                                                  "parameters": {"type": "object", "properties": {"db": {"type": "number", "minimum": -24, "maximum": 24}}, "required": ["db"]}}}]
_APPLY_SYSTEM = ("You are a mixing assistant. You get the measurements of a render of a work in progress, and a target. "
                 "Call adjust_master_gain with the change you would make.")


def gain_direction_ok(want_db: float, measured_lufs: float, target_lufs: float = -14.0, dead_zone: float = 0.5) -> bool:
    """A louder change is only fine when the audio is below the target, and the other way round. Near the target either direction is accepted.

    Local models get the sign wrong (measured 2026-10-19: -0.5 dB proposed for -15.81 LUFS against -14), so code checks it.
    """
    need = target_lufs - measured_lufs
    return abs(need) <= dead_zone or (want_db > 0) == (need > 0)


def _lufs(report: dict):
    return report.get("loudness", {}).get("lufs")


def apply(call, project: Path, work: Path) -> dict:
    """G0-13: render (FL is closed and reopened for each render), ask the local LLM for a master gain change, apply it in FL, save, render again, and check the audio moved by that amount.

    Works on a sandbox copy only. The master fader is put back afterwards and the project saved again.
    """
    work, out, applied = Path(work), {"steps": {}}, None

    def rec(name: str, r, **extra) -> bool:
        out["steps"][name] = {"ok": r.ok, **({"error": "%s %s" % (r.error.code, r.error.message)} if not r.ok else {}), **extra}
        return r.ok

    def render_and_measure(tag: str):
        r = call("render_with_restart", project=str(project), out_dir=str(work / tag))
        if not rec("render_" + tag, r, **({"bridge_back_s": r.value["bridge_back_s"]} if r.ok else {})):
            return None
        m = call("build_measure_report", path=r.value["path"])
        return m.value if rec("measure_" + tag, m, lufs=_lufs(m.value) if m.ok else None) else None

    before = render_and_measure("before")
    if before is None:
        return {**out, "passed": False}
    cur = call("op_mixer_get_track_volume", index=0, mode=1)
    if not rec("read_master", cur, db=cur.value if cur.ok else None):
        return {**out, "passed": False}
    ask = "Target: about -14 LUFS integrated, true peak below -1 dBTP. The master fader is at %.2f dB.\nMeasurements:\n%s" % (cur.value, json.dumps(before)[:3500])
    reply = call("call_agent_llm", prompt=ask, system=_APPLY_SYSTEM, tools=_GAIN_TOOL, max_tokens=2048)
    rec("brain", reply)
    calls = [check_proposal(c.get("function") or {}, _GAIN_TOOL) for c in (reply.value["message"].get("tool_calls") or [])] if reply.ok else []
    out["proposals"] = calls
    good = [c for c in calls if c["valid"]]
    if not good:
        out["steps"]["proposal"] = {"ok": False, "error": "the model made no valid adjust_master_gain call"}
        return {**out, "passed": False}
    want = float(json.loads(good[0]["arguments"])["db"])
    if _lufs(before) is not None and not gain_direction_ok(want, _lufs(before)):
        out["steps"]["proposal"] = {"ok": False, "error": "the model proposed %+.1f dB for audio at %.1f LUFS against a -14 target: wrong direction, not applied" % (want, _lufs(before))}
        return {**out, "passed": False}
    trim = call("apply_gain_trim", index=0, delta_db=want, max_delta_db=6.0)
    if not rec("apply", trim, **({"result": trim.value} if trim.ok else {})):
        return {**out, "passed": False}
    applied = trim.value["applied_delta_db"]
    try:
        if not rec("save", call("save_sandbox_project", project=str(project))):
            return {**out, "passed": False}
        after = render_and_measure("after")
        if after is None:
            return {**out, "passed": False}
        moved = _lufs(after) - _lufs(before)
        out["loudness"] = {"before": _lufs(before), "after": _lufs(after), "moved_lu": round(moved, 2), "applied_db": round(applied, 2)}
        out["closes_the_loop"] = abs(moved - applied) <= 1.0
    finally:
        back = call("set_track_volume_db_verified", index=0, db=cur.value)
        rec("restore_fader", back)
        rec("restore_save", call("save_sandbox_project", project=str(project)))
    out["passed"] = bool(out.get("closes_the_loop")) and all(v["ok"] for v in out["steps"].values())
    return out


def critique(call, path: Path, focus: str = "") -> dict:
    """G0-14: the audio critique of one file through the real tool. Reports the source (model or dsp), the time and the text."""
    t = time.monotonic()
    r = call("critique_audio", path=str(path), focus=focus)
    if not r.ok:
        return {"passed": False, "error": "%s %s" % (r.error.code, r.error.message)}
    return {"passed": r.value["source"] == "model", "source": r.value["source"], "seconds": round(time.monotonic() - t, 1),
            "fallback": r.meta.get("model_error_detail"), "text": _listener_notes(r.value)}


def listen(call, project: Path, work: Path, bpm: float = 128.0) -> dict:
    """G0-15: render the saved sandbox project (FL is closed and reopened), then measure it, check tempo and key, and let the audio model and the brain react.

    Nothing is changed in the project. Proposals are listed, with the direction check on any gain change.
    """
    out = {"steps": {}}

    def rec(name: str, r, **extra) -> bool:
        out["steps"][name] = {"ok": r.ok, **({"error": "%s %s" % (r.error.code, r.error.message)} if not r.ok else {}), **extra}
        return r.ok

    r = call("render_with_restart", project=str(project), out_dir=str(Path(work) / "render"))
    if not rec("render", r):
        return {**out, "passed": False}
    path = r.value["path"]
    out["audio"] = path
    rep, tempo, key = call("build_measure_report", path=path), call("estimate_bpm_dsp", path=path, hint_bpm=bpm), call("estimate_key_dsp", path=path)
    rec("measure", rep)
    rec("tempo", tempo, measured=tempo.value["bpm"] if tempo.ok else None)
    rec("key", key, value=key.value if key.ok else None)
    if not rep.ok:
        return {**out, "passed": False}
    out["report"] = rep.value
    heard = call("critique_audio", path=path)
    rec("listen", heard, source=heard.value.get("source") if heard.ok else None)
    notes = _listener_notes(heard.value) if heard.ok else ""
    out["listener_notes"] = notes
    ask = "Target: about -14 LUFS integrated, true peak below -1 dBTP, balanced spectrum.\nMeasurements:\n" + json.dumps(rep.value)[:3500]
    if notes:
        ask += "\nListener notes (an audio model's opinion, not measured; the measurements win when they disagree):\n" + notes[:1200]
    reply = call("call_agent_llm", prompt=ask, system=_LOOP_SYSTEM, tools=_LOOP_TOOLS, max_tokens=2048)
    if rec("brain", reply):
        lufs = _lufs(rep.value)
        props = [check_proposal(c.get("function") or {}, _LOOP_TOOLS) for c in (reply.value["message"].get("tool_calls") or [])]
        for pr in props:
            if pr["valid"] and pr["name"] == "adjust_master_gain" and lufs is not None:
                pr["direction_ok"] = gain_direction_ok(float(json.loads(pr["arguments"])["db"]), lufs)
        out["proposals"] = props
    out["passed"] = all(v["ok"] for v in out["steps"].values())
    return out

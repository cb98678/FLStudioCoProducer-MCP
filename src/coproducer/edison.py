"""Edison script (.pyscript) generators. No FL Studio needed to build or test them.

Edison runs Python scripts from Documents\\Image-Line\\FL Studio\\Settings\\Audio scripts (Tools > Scripting). The API used here is the one in the
installed Reference.txt (FL 2026 v26.1.7): `from enveditor import *`, the globals Editor, EditorSample and Utils, ScriptDialog, and the Sample
methods AddRegion, AmpFromTo, MSToSamples, SamplesToMS. Docs: https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/plugins/editortool_run.htm
Scripts here avoid per-sample Python loops (slow); regions and range calls only.
"""
from __future__ import annotations

import itertools
import re

HEADER = "from enveditor import *\n"
_NAME = re.compile(r"^[A-Za-z0-9 _.-]{1,60}$")


def script_filename(title: str) -> str:
    if not _NAME.match(title):
        raise ValueError("script title must be 1 to 60 letters, digits, space, dot, dash or underscore")
    return title + ".pyscript"


def probe_script(out_name: str = "coproducer_probe.json") -> str:
    """A script that writes what Edison sees (length, channels, rate, selection, regions) as JSON to out_name, a bare file name.
    Edison's Python can only write under its Audio scripts folder (the working directory); paths elsewhere raise SystemError. Changes nothing in the sample."""
    if not re.match(r"^[A-Za-z0-9_.-]{1,60}$", out_name):
        raise ValueError("out_name must be a bare file name, Edison can only write beside its scripts")
    return HEADER + '''import json

info = {
  "length": EditorSample.Length,
  "channels": EditorSample.NumChans,
  "sample_rate": EditorSample.SampleRate,
  "selection_start": Editor.SelectionStartS,
  "selection_end": Editor.SelectionEndS,
  "region_count": EditorSample.RegionCount,
  "regions": [],
}
for i in range(EditorSample.RegionCount):
  r = EditorSample.GetRegion(i)
  info["regions"].append({"name": r.Name, "start": r.SampleStart, "end": r.SampleEnd})
f = open(%r, "w")
f.write(json.dumps(info))
f.close()
Utils.ShowMessage("coproducer probe wrote " + %r)
''' % (out_name, out_name)  # noqa: UP031 (script text holds braces)


def regions_script(times_ms: list[float], prefix: str = "chop", end_ms: float | None = None) -> str:
    """A script that adds one region per slice. times_ms are the slice starts in milliseconds from the start of the sample, ascending; each
    region ends where the next begins (the last at end_ms, or the end of the sample)."""
    if len(times_ms) < 1 or any(b <= a for a, b in itertools.pairwise(times_ms)) or times_ms[0] < 0:
        raise ValueError("times_ms must be ascending and not negative")
    if not re.match(r"^[A-Za-z0-9_ -]{1,30}$", prefix):
        raise ValueError("bad region prefix")
    return HEADER + '''times = %r
end_ms = %r
prefix = %r

last = EditorSample.Length - 1
for i in range(len(times)):
  a = round(EditorSample.MSToSamples(times[i]))
  if i + 1 < len(times):
    b = round(EditorSample.MSToSamples(times[i + 1])) - 1
  elif end_ms is not None:
    b = round(EditorSample.MSToSamples(end_ms)) - 1
  else:
    b = last
  a = max(0, min(a, last))
  b = max(a + 1, min(b, last))
  EditorSample.AddRegion(prefix + " " + str(i + 1), a, b)
Utils.ShowMessage("added " + str(len(times)) + " regions")
''' % ([float(t) for t in times_ms], end_ms, prefix)  # noqa: UP031


def gain_script(db: float) -> str:
    """A script that amplifies the selection by db (Sample.AmpFromTo takes a linear factor)."""
    if not -60.0 <= db <= 24.0:
        raise ValueError("gain must be between -60 and 24 dB")
    return HEADER + '''x1 = Editor.SelectionStartS
x2 = Editor.SelectionEndS
EditorSample.AmpFromTo(x1, x2, %r)
''' % (10 ** (db / 20.0))


JOB_FILE = "coproducer_job.json"
RESULT_FILE = "coproducer_result.json"
OPS = {
    "grid": ("bpm", "step_beats"),
    "regions": ("times_ms",),
    "gain": ("db",),
    "normalize": (),
    "fade_in": ("ms",),
    "fade_out": ("ms",),
    "reverse": (),
    "silence": (),
    "delete": (),
    "insert_silence": ("from_ms", "to_ms"),
    "trim": ("from_ms", "to_ms"),
    "trim_to_bars": ("bpm", "bars"),
    "fit_length": ("bpm", "bars"),
    "mono": (),
}


def check_job(ops: list[dict]) -> list[dict]:
    """Validate a job (a list of op dicts) for the runner script and return it. Raises ValueError naming the first problem.
    Positions are milliseconds, durations in beats or bars at the job's bpm. Ranges default to the whole sample; from_ms/to_ms narrow it,
    "selection": true uses the Edison selection."""
    if not isinstance(ops, list) or not ops:
        raise ValueError("job must be a non-empty list of ops")
    for i, op in enumerate(ops):
        if not isinstance(op, dict) or op.get("op") not in OPS:
            raise ValueError(f"op {i}: unknown op, expected one of {sorted(OPS)}")
        for key in OPS[op["op"]]:
            if key not in op:
                raise ValueError(f"op {i} ({op['op']}): missing {key}")
        for key in ("bpm", "step_beats", "bars", "ms", "offset_ms"):
            if key in op and (not isinstance(op[key], int | float) or op[key] < 0 or (key != "offset_ms" and op[key] == 0)):
                raise ValueError(f"op {i} ({op['op']}): {key} must be a positive number")
        if op["op"] == "regions":
            regions_script(op["times_ms"], op.get("prefix", "chop"))  # reuses its time and prefix checks
        if "prefix" in op and not re.match(r"^[A-Za-z0-9_ -]{1,30}$", str(op["prefix"])):
            raise ValueError(f"op {i}: bad region prefix")
        if op["op"] == "gain" and not -60.0 <= op["db"] <= 24.0:
            raise ValueError(f"op {i}: gain must be between -60 and 24 dB")
    return ops


def runner_script() -> str:
    """The one fixed script that runs a job: reads coproducer_job.json from its own folder, applies the ops in order and writes
    coproducer_result.json. Install it once; change the job file to change what it does."""
    return HEADER + '''import json

f = open(%r, "r")
job = json.loads(f.read())
f.close()

S = EditorSample
rate = S.SampleRate
log = []


def ms(t):
  return int(round(S.MSToSamples(t)))


def span(op):
  last = S.Length - 1
  if op.get("selection"):
    a, b = Editor.SelectionStartS, Editor.SelectionEndS
  else:
    a = ms(op["from_ms"]) if "from_ms" in op else 0
    b = ms(op["to_ms"]) - 1 if "to_ms" in op else last
  a = max(0, min(a, last))
  b = max(a, min(b, last))
  return a, b


def beat_ms(op):
  return 60000.0 / op["bpm"]


def ramp(a, b, up, steps=48):
  n = b - a + 1
  steps = max(1, min(steps, n))
  for k in range(steps):
    x1 = a + (n * k) // steps
    x2 = a + (n * (k + 1)) // steps - 1
    if x2 < x1:
      continue
    g = (k + 0.5) / steps
    S.AmpFromTo(x1, x2, g if up else 1.0 - g)


def run(op):
  name = op["op"]
  if name == "grid":
    step = beat_ms(op) * op["step_beats"]
    t = op.get("offset_ms", 0.0)
    end = S.SamplesToMS(S.Length)
    count = op.get("count", 100000)
    n = 0
    while t < end - 1 and n < count:
      a = ms(t)
      b = min(ms(t + step) - 1, S.Length - 1)
      if b > a:
        S.AddRegion(op.get("prefix", "beat") + " " + str(n + 1), a, b)
        n += 1
      t += step
    return "regions " + str(n)
  if name == "regions":
    ts = op["times_ms"]
    for i in range(len(ts)):
      a = ms(ts[i])
      b = ms(ts[i + 1]) - 1 if i + 1 < len(ts) else S.Length - 1
      a = max(0, min(a, S.Length - 1))
      b = max(a + 1, min(b, S.Length - 1))
      S.AddRegion(op.get("prefix", "chop") + " " + str(i + 1), a, b)
    return "regions " + str(len(ts))
  if name == "insert_silence":
    a = ms(op["from_ms"])
    S.InsertSilence(a, max(a, ms(op["to_ms"]) - 1))
    return "inserted"
  if name == "trim_to_bars":
    a = ms(op.get("offset_ms", 0.0))
    b = a + ms(beat_ms(op) * 4 * op["bars"]) - 1
    S.TrimFromTo(a, min(b, S.Length - 1))
    return "trimmed"
  if name == "fit_length":
    want = ms(beat_ms(op) * 4 * op["bars"])
    have = S.Length
    if have < want:
      S.InsertSilence(have, want - 1)
    elif have > want:
      S.DeleteFromTo(want, have - 1)
    return "fit " + str(have) + " -> " + str(S.Length)
  if name == "mono":
    S.ConvertToMono(0)
    return "mono"
  a, b = span(op)
  if name == "trim":
    S.TrimFromTo(a, b)
  elif name == "gain":
    S.AmpFromTo(a, b, 10 ** (op["db"] / 20.0))
  elif name == "normalize":
    S.NormalizeFromTo(a, b, op.get("level", 1.0), op.get("only_if_above", False))
  elif name == "fade_in":
    ramp(a, min(b, a + ms(op["ms"])), True)
  elif name == "fade_out":
    ramp(max(a, b - ms(op["ms"])), b, False)
  elif name == "reverse":
    S.ReverseFromTo(a, b)
  elif name == "silence":
    S.SilenceFromTo(a, b)
  elif name == "delete":
    S.DeleteFromTo(a, b)
  return name + " " + str(a) + ".." + str(b)


before = S.Length
for i in range(len(job)):
  try:
    log.append({"i": i, "ok": True, "note": run(job[i])})
  except BaseException as e:
    log.append({"i": i, "ok": False, "error": type(e).__name__ + " " + str(e)[:80]})
    break

regions = []
for i in range(S.RegionCount):
  r = S.GetRegion(i)
  regions.append({"name": r.Name, "start": r.SampleStart, "end": r.SampleEnd})
out = {"before": before, "after": S.Length, "rate": rate, "channels": S.NumChans, "log": log, "regions": regions}
f = open(%r, "w")
f.write(json.dumps(out))
f.close()
Utils.ShowMessage("coproducer run: " + str(len(log)) + " ops, length " + str(before) + " -> " + str(S.Length))
''' % (JOB_FILE, RESULT_FILE)  # noqa: UP031 (script text holds braces)

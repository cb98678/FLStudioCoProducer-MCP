"""Serum 2 tables, sampler sounds and preset specs from a song's loops and kit (skill serum-wavetables; MCP tools build_wavetable and
prepare_sampler_sound, then serum-mcp generate_preset).

    python tools/serum_tables.py --loops sandbox\\loops\\NAME --section drop_a [--out sandbox\\wavetables\\NAME] [--name NAME]
        [--frames 16] [--install-tables [TABLES_DIR]]

--loops is an extract_song_loops folder (patterns.json, bass, music, kit and vocal cuts). From the section's bass loop: a table read from
its longest held note, pitch-synchronously (wavetables.cycles), and the bass's measured envelope and roll-off (soundbrief.describe).
From the music loop: a table when it holds a clear pitch. Two formula tables: a phase-modulated sub (a sine that grows odd harmonics with
the table position) and a lead that morphs from a sine to its 3rd and 5th harmonics. The kit's one-shots and the vocal hook are planned
for Serum's sample oscillator (wavetables.sampler_plan): the hook plays whole, at its own pitch, on note 60. For each sound a serum-mcp
PresetSpec (spec_ROLE.json) built from those readings with serumspec's moves, ready for generate_preset. Writes under OUT, which must
sit under a folder named sandbox; the loops are only read. README.md says what each file is and what is left to judge by ear.

--install-tables also copies the tables into Serum's Tables folder (default Documents\\Xfer\\Serum 2 Presets\\Tables), subfolder
User\\sandbox\\NAME, and the specs name them there (osc wavetable), so Serum plays them exactly; without it the specs use serum-mcp's
sample_source, which fades the first and last 64 samples of every frame (edge_loss_db says how much that changes each table).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "src"))
from coproducer import serumspec, soundbrief, wavetables  # noqa: E402

SUB = "sin(pi*x + y*sin(2*pi*x))"
PUMPED_ATTACK_S = 0.04
LEAD = "(1-y)*sin(pi*x) + y*(0.6*sin(3*pi*x) + 0.4*sin(5*pi*x))"


def _loop(folder: Path, part: str, name: str, section: str) -> Path | None:
    hits = sorted((folder / part).glob("%s_%s_*bar_*bpm.wav" % (name, section)), key=lambda p: -int(p.name.split("_")[-2][:-3]))
    return hits[0] if hits else None


def _table(src: Path, out: Path, frames: int, fmax: float) -> dict:
    x, rate = soundbrief.load_slice(str(src))
    t = wavetables.cycles(wavetables.mono(x), rate, frames, 30.0, fmax)
    wavetables.write_table(out, t["frames"])
    return {"path": str(out), "from": src.name, **{k: v for k, v in t.items() if k != "frames"}}


def _formula(expr: str, out: Path, frames: int) -> dict:
    t = wavetables.formula(expr, frames)
    t["frames"] = wavetables.turn_quiet(t["frames"])
    wavetables.write_table(out, t["frames"])
    return {"path": str(out), "formula": expr, "edge_loss_db": round(wavetables.edge_loss_db(t["frames"]), 1), "first": t["first"], "last": t["last"]}


def _sampler(src: Path, role: str) -> dict:
    x, rate = soundbrief.load_slice(str(src))
    return {"from": src.name, **wavetables.sampler_plan(x, rate, role, str(src.resolve()))}


def _osc(made: dict, key: str, frames: int, installed: dict) -> dict:
    return serumspec.table_ref(installed[key]) if key in installed else serumspec.table_osc(made[key]["path"], frames)


def specs(name: str, made: dict, bass_sound: dict | None, frames: int, installed: dict | None = None) -> dict:
    """serum-mcp PresetSpecs for every sound made, each from its own readings. installed: role -> path under Serum's Tables."""
    out, inst = {}, installed or {}
    label = name.replace("_", " ").title()
    if "bass" in made:
        base = soundbrief.starting_point(bass_sound or {}, "bass")["spec"]
        amp_env, dec = {"envelopes": {0: base["envelopes"][0]}}, float(min(0.4, max(0.08, (bass_sound or {}).get("decay_s") or 0.22)))
        if ((bass_sound or {}).get("attack_s") or 0.0) > PUMPED_ATTACK_S:      # a slow swell on a bass stem is the mix's sidechain pump
            amp_env, dec = serumspec.amp(0.003, 0.3, 0.8, 0.04), 0.18
            made["bass"]["remark"] = ("measured attack %.0f ms is the record's pump (sidechain ducking), not the synth: the spec holds the "
                                    "note and leaves the pump to FL's sidechain" % (1000 * bass_sound["attack_s"]))
        parts = [serumspec.pluck(0.001, dec, 35.0), serumspec.macros(0, 50.0, 1, 40.0)]
        out["bass"] = serumspec.assemble("CP - %s Bass Table" % label, "The record's own bass cycles as a table, plucked on its measured decay",
                                         [_osc(made, "bass", frames, inst)], base.get("filters"), parts, amp_env)
    out["sub"] = serumspec.assemble("CP - %s PM Sub" % label, "Phase-modulated sine sub: Macro 1 grows odd harmonics for small speakers",
                                    [_osc(made, "sub", frames, inst)], None, [serumspec.macros(0, 40.0, None, 0, None, 0, None, 0)],
                                    serumspec.amp(0.001, 0.3, 1.0, 0.04))
    parts = [serumspec.pluck(0.001, 0.2, 45.0), serumspec.dirt("kTapeSat", 45.0), serumspec.room(20.0)]      # dirt before the room
    rev, dist = serumspec.fx_index_after(parts, "FXReverb"), serumspec.fx_index_after(parts, "FXDistortion")
    parts += [serumspec.duck(rev, lfo=0), serumspec.macros(0, 70.0, 1, 40.0, rev, 30.0, dist, 60.0)]
    out["lead"] = serumspec.assemble("CP - %s Morph Stab" % label, "Sine to 3rd and 5th harmonics on Macro 1, plucked, room and dirt on macros",
                                     [_osc(made, "lead", frames, inst)], [{"type": "lowpass_24", "cutoff": 0.55, "resonance": 15.0}], parts,
                                     serumspec.amp(0.001, 0.5, 0.2, 0.15))
    if "music" in made:
        out["music"] = serumspec.assemble("CP - %s Music Table" % label, "The record's own chord or riff cycles as a table, Macro 1 moves through it",
                                          [_osc(made, "music", frames, inst)], [{"type": "lowpass_24", "cutoff": 0.8, "resonance": 5.0}],
                                          [serumspec.macros(0, 80.0, None, 0, None, 0, None, 0)], serumspec.amp(0.005, 0.6, 0.6, 0.2))
    if "hook" in made:
        parts = [serumspec.chop(16), serumspec.room(20.0)]
        rev = serumspec.fx_index_after(parts, "FXReverb")
        parts += [serumspec.duck(rev, lfo=1), serumspec.macros(None, 0, None, 0, rev, 30.0, None, 0)]
        out["hook"] = serumspec.assemble("CP - %s Hook Chop" % label, "The hook whole at its own pitch on note 60, a 16th gate, a small ducked room",
                                         [made["hook"]["oscillator"]], None, parts, serumspec.amp(0.001, 1.0, 1.0, 0.05))
    for k in ("kick", "clap", "hat"):
        if k in made:
            out[k] = serumspec.assemble("CP - %s %s" % (label, k.title()), "The record's %s averaged from its hits, on the sample oscillator" % k,
                                        [made[k]["oscillator"]], None, [], serumspec.amp(0.0005, 2.0, 1.0, 0.02))
    return out


def readme(name: str, section: str, made: dict, skipped: dict) -> str:
    rows = ["# Serum tables and sampler sounds: %s (%s)" % (name, section), "",
            "Tables are 2048-sample frames (Serum's format); `edge_loss_db` is how much serum-mcp's 64-sample edge fade changes them when its",
            "`sample_source` slices the file (each frame is turned so its wrap is the quietest place). Sampler sounds play at their own pitch",
            "on MIDI note 60 (FL's C5). Specs are serum-mcp PresetSpecs: generate them into Presets/User/sandbox/%s, render them, judge by ear." % name, "",
            "| Sound | From | Reading |", "| --- | --- | --- |"]
    for k, v in made.items():
        if "formula" in v:
            what = "formula `%s`, edge loss %.0f dB" % (v["formula"], v["edge_loss_db"])
        elif "f0_hz" in v:
            what = "%s (%+.0f cents) %.1f Hz, %s to %s s, edge loss %.0f dB" % (v["note"], v["cents"], v["f0_hz"], v["from_s"], v["to_s"], v["edge_loss_db"])
        else:
            what = "%.2f s, peak %.1f dBFS, rms %.1f dBFS%s%s" % (v["seconds"], v["peak_dbfs"], v["rms_dbfs"],
                                                                  ", pitch %s" % v["pitch_note"] if v.get("pitch_note") else "",
                                                                  "; " + "; ".join(v["warnings"]) if v.get("warnings") else "")
        rows.append("| %s | %s | %s%s |" % (k, v.get("from", ""), what, "; " + v["remark"] if v.get("remark") else ""))
    for k, why in skipped.items():
        rows.append("| %s | skipped | %s |" % (k, why))
    return "\n".join(rows) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--loops", required=True)
    ap.add_argument("--section", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--name", default="")
    ap.add_argument("--frames", type=int, default=16)
    ap.add_argument("--install-tables", nargs="?", const="auto", default="")
    a = ap.parse_args()
    folder = Path(a.loops)
    pat = json.loads((folder / "patterns.json").read_text(encoding="utf-8"))
    name = a.name or pat.get("name") or folder.name
    out = Path(a.out) if a.out else HOME / "sandbox" / "wavetables" / name
    if "sandbox" not in [p.lower() for p in out.resolve().parts]:
        sys.exit("refusing to write %s: output must be under a folder named sandbox" % out)
    made, skipped, bass_sound = {}, {}, None
    for part, fmax in (("bass", 400.0), ("music", 1500.0)):
        src = _loop(folder, part, name, a.section)
        if not src:
            skipped[part] = "no %s loop for section %s" % (part, a.section)
            continue
        try:
            made[part] = _table(src, out / ("%s_%s_%s.wav" % (name, part, a.section)), a.frames, fmax)
        except (wavetables.TableError, ValueError) as e:
            skipped[part] = str(e)
        if part == "bass":
            x, rate = soundbrief.load_slice(str(src))
            bass_sound = soundbrief.describe(x, rate)
    made["sub"] = _formula(SUB, out / ("%s_pm_sub.wav" % name), a.frames)
    made["lead"] = _formula(LEAD, out / ("%s_morph_stab.wav" % name), a.frames)
    for k, v in (pat.get("kit") or {}).items():
        f = folder / "kit" / Path(v.get("file", "")).name
        if f.is_file():
            made[k] = _sampler(f, "drum")
    hooks = sorted((folder / "vocal").glob("*.wav"))
    if hooks:
        made["hook"] = _sampler(hooks[0], "vocal")
    installed = {}
    if a.install_tables:
        tables = Path.home() / "Documents" / "Xfer" / "Serum 2 Presets" / "Tables" if a.install_tables == "auto" else Path(a.install_tables)
        if not tables.is_dir():
            sys.exit("no Serum Tables folder at %s" % tables)
        for k in ("bass", "music", "sub", "lead"):
            if k in made:
                dest = tables / "User" / "sandbox" / name / Path(made[k]["path"]).name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(made[k]["path"], dest)
                installed[k] = "User/sandbox/%s/%s" % (name, dest.name)
                made[k]["installed"] = str(dest)
    sp = specs(name, made, bass_sound, a.frames, installed)
    out.mkdir(parents=True, exist_ok=True)
    for k, s in sp.items():
        (out / ("spec_%s.json" % k)).write_text(json.dumps(s, indent=1), encoding="utf-8")
    (out / "tables.json").write_text(json.dumps({"name": name, "section": a.section, "made": made, "skipped": skipped,
                                                 "bass_sound": {k: bass_sound.get(k) for k in ("attack_s", "decay_s", "sustain", "words")} if bass_sound else None},
                                                indent=1, default=str), encoding="utf-8")
    text = readme(name, a.section, made, skipped)
    (out / "README.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

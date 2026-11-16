"""Make an original track (no source song) in a style, end to end, through the registered modules (ceiling A2, sandbox only).

    python tools/original_track.py NAME STYLE --key F --mode minor [--bpm 140] [--sections intro=16,build=8,drop=16,...]
                                   [--chords Fm,Db,Ab,Eb] [--part bass=FILE.mid ...] [--omit stab ...] [--serum-state reese=FILE ...]
                                   [--serum-preset pad="PRESET NAME" ...] [--serum SOUNDS.flp] [--base BASE.flp] [--sytrus SYTRUS.flp]
                                   [--work DIR] [--title "..."] [--note "..." ...] [--variety-seed S] [--no-render]

Steps, each a module: build_song_plan with options.instrumental (the style pack's sections and tempo, or the given ones; the key; a harmony
loop from chord names; the parts written for the track as MIDI files, in true MIDI: bass, sub, keys, pad, lead; the parts to leave out),
prepare_remix_audio with no vocal (the kit, the bass sample, the FX bed), build_remix_project (the pack's drums as sampler channels and
patterns, every part as a channel with 16-bar piano rolls, Serum 2 channels carrying the sounds made for the track: --serum-state
reese=FILE puts a Serum 2 bass on the bass channel) and apply_production_recipe. Then, unless --no-render and only while FL Studio is
closed, tools/remix_song.py --from-produced does the rest: the render, the contrast loop, the club master, the tempo checks and the panel.
Skill track-creation; the first track was "Ironclad" (dubstep, F minor, 2026-11-07).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coproducer import stylepack  # noqa: E402
from coproducer.servers.common import make_session  # noqa: E402

HOME = Path(__file__).resolve().parents[1]
_PC = {n: i for i, n in enumerate("C C# D D# E F F# G G# A A# B".split())} | {"Db": 1, "Eb": 3, "Gb": 6, "Ab": 8, "Bb": 10}


def first(*paths: Path) -> str:
    return str(next((p for p in paths if p.is_file()), paths[-1]))


def pairs(items: list[str], label: str, many: bool = False) -> dict:
    """KEY=VALUE items as a dict; with many, a key given more than once collects a list."""
    out: dict = {}
    for x in items:
        if "=" not in x:
            sys.exit("%s wants KEY=VALUE, got %r" % (label, x))
        k, v = x.split("=", 1)
        k, v = k.strip(), v.strip().strip('"')
        if many:
            out.setdefault(k, []).append(v)
        else:
            out[k] = v
    return out


def sections_arg(text: str) -> list | None:
    """intro=16,build=8,drop=16 -> [["intro", 16], ...]; empty means the pack's own."""
    if not text:
        return None
    out = []
    for item in text.split(","):
        kind, n = item.split("=", 1)
        out.append([kind.strip(), int(n)])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("name")
    ap.add_argument("style", choices=stylepack.names())
    ap.add_argument("--key", required=True, help="the key's tonic: C, C#, Db ... B")
    ap.add_argument("--mode", choices=("major", "minor"), default="minor")
    ap.add_argument("--bpm", type=float, default=None, help="default: the pack's tempo")
    ap.add_argument("--sections", default="", help="kind=bars,... (intro, groove, break, build, drop, outro); default the pack's")
    ap.add_argument("--chords", default="", help="four chord names (two bars each) or eight (one bar each), e.g. Fm,Db,Ab,Eb")
    ap.add_argument("--part", action="append", default=[], help="ROLE=MIDI file[@BAR] (bass, sub, keys, pad, lead; the file placed from that 0-based bar), repeatable, several files per role")
    ap.add_argument("--omit", action="append", default=[], help="a part to leave out (stab, arp, sub, bass, pad, keys, lead), repeatable")
    ap.add_argument("--label", action="append", default=[], help="ROLE=channel name, e.g. keys=\"Bass - Vowel Talker\" puts a second bass on the stab channel (roles come from names)")
    ap.add_argument("--serum-state", action="append", default=[], help="PART=FILE: a Serum 2 channel state (render_serum_sound) for reese, sub, stab, arp or pad")
    ap.add_argument("--serum-preset", action="append", default=[], help="PART=PRESET NAME, by name in the Serum project")
    ap.add_argument("--serum", default=first(HOME / "sandbox" / "serum" / "serum_sounds.flp", HOME / "sandbox" / "templates" / "serum_carrier.flp"))
    ap.add_argument("--base", default=first(HOME / "sandbox" / "stemstest" / "stemstest.flp", HOME / "sandbox" / "templates" / "base_project.flp"))
    ap.add_argument("--sytrus", default=first(HOME / "sandbox" / "DTP_work" / "Notorious_DTP_28_auto.flp", HOME / "sandbox" / "templates" / "sytrus_patches.flp"))
    ap.add_argument("--work", default="")
    ap.add_argument("--title", default="")
    ap.add_argument("--note", action="append", default=[], help="a line for the plan's notes (the brief), repeatable")
    ap.add_argument("--variety-seed", default=None, help="let the variety engine choose groove, kit and sounds (default: the pack as written)")
    ap.add_argument("--no-render", action="store_true")
    a = ap.parse_args()
    if a.key not in _PC:
        sys.exit("unknown key %r" % a.key)
    s = make_session(HOME, "original_" + a.name, "fl-bridge", "A2")
    call = s.registry.call
    work = Path(a.work or HOME / "sandbox" / "remix" / ("%s_%s" % (a.name, a.style)))
    work.mkdir(parents=True, exist_ok=True)
    report: dict = {"name": a.name, "style": a.style, "original": True, "steps": []}

    def step(label: str, module: str, **kw):
        r = call(module, **kw)
        row = {"step": label, "module": module, "ok": r.ok, "verified": r.meta.get("verified")}
        row.update({"value": r.value} if r.ok else {"error": r.error.code, "message": r.error.message})
        report["steps"].append(row)
        (work / "remix_report.json").write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
        print("%-14s %-26s %s" % (label, module, "ok" if r.ok else "%s: %s" % (r.error.code, r.error.message)), flush=True)
        return r

    plan = work / "plan.json"
    parts = pairs(a.part, "--part", many=True)
    for role, files in parts.items():
        for f in files:
            if not Path(f.rsplit("@", 1)[0] if "@" in f and f.rsplit("@", 1)[1].isdigit() else f).is_file():
                sys.exit("no MIDI file for %s at %s" % (role, f))
    spec = {**({"sections": sections_arg(a.sections)} if a.sections else {}), **({"chords": [c.strip() for c in a.chords.split(",")]} if a.chords else {}),
            **({"part_files": parts} if parts else {}), **({"omit": a.omit} if a.omit else {}), **({"notes": a.note} if a.note else {}),
            **({"labels": pairs(a.label, "--label")} if a.label else {})}
    r = step("plan", "build_song_plan", out_plan=str(plan), name="%s_%s" % (a.name, a.style), title=a.title,
             options={"style": a.style, "key_pc": _PC[a.key], "mode": a.mode, **({"bpm": a.bpm} if a.bpm else {}), "instrumental": spec,
                      "variety": {"seed": a.variety_seed} if a.variety_seed else False})
    if not r.ok:
        return 1
    r = step("audio", "prepare_remix_audio", plan_file=str(plan), vocals_path="", out_dir=str(work / "audio"))
    if not r.ok:
        return 1
    states, presets = pairs(a.serum_state, "--serum-state"), pairs(a.serum_preset, "--serum-preset")
    synth = {}
    if a.serum and Path(a.serum).is_file():
        synth = {"serum_project": a.serum, **({"serum_presets": presets} if presets else {}), **({"serum_states": states} if states else {})}
    elif states or presets:
        print("Serum sounds need a project with a Serum 2 channel to ride on (--serum); building without them")
    built = work / ("%s_%s.flp" % (a.name, a.style))
    r = step("build", "build_remix_project", base_project=a.base, sytrus_project=a.sytrus, audio_dir=str(work / "audio"), out_project=str(built),
             plan_file=str(plan), **({"options": synth} if synth else {}))
    if not r.ok:
        return 1
    if r.value.get("stand_in"):
        print("stand-ins (no sound given): %s" % ", ".join(r.value["stand_in"]))
    pack = stylepack.load(a.style)
    produced = work / ("%s_%s_produced.flp" % (a.name, a.style))
    r = step("produce", "apply_production_recipe", project=str(built), out_project=str(produced), recipe=pack["production_recipe"], key=a.key, plan_file=str(plan))
    if not r.ok:
        return 1
    if a.no_render:
        print("built and produced:", produced)
        return 0
    from tools import remix_song  # noqa: E402  (the render, the contrast loop, the master and the panel, as for a remix)
    sys.argv = ["remix_song.py", a.name, a.style, "--from-produced", str(produced), "--plan", str(plan), "--work", str(work), "--sounds", "named"]
    return remix_song.main()


if __name__ == "__main__":
    raise SystemExit(main())

# name=Coproducer Probe
# GENERATED-FREE: hand written. Runs inside FL Studio (Python 3.9 compatible, no f-strings, no type hints).
"""Gate 0 probe that runs inside FL Studio and writes probe_report.json next to this file.

Install:   coproducer probe install-fl          (read-only probes)
           coproducer probe install-fl --mutating   (also tests writes: use ONLY on a copy of a project)
Use:       In MIDI Settings choose "Coproducer Probe (user)" as the controller type, open the Script output window
           (View > Script output), and wait for "probe done". Then run:  coproducer probe report
Then switch the controller type back to "Coproducer (user)".
"""
import os
import sys

MUTATING = False        # coproducer probe install-fl --mutating rewrites this line
_done = [False]
REPORT = {}

MODULES = ["general", "ui", "transport", "mixer", "channels", "patterns", "playlist", "arrangement", "plugins", "device", "midi", "utils", "screen"]


def _here():
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        return os.path.expanduser("~")


def _try(name, fn):
    """Run one probe. Whatever happens is recorded; one failure never stops the others."""
    try:
        REPORT[name] = {"ok": True, "value": fn()}
    except Exception as e:  # noqa: BLE001 - the point of a probe is to record the failure
        REPORT[name] = {"ok": False, "error": "%s: %s" % (type(e).__name__, e)}
    print("probe", name, "ok" if REPORT[name]["ok"] else "FAILED " + REPORT[name]["error"])


def probe_versions():
    import general
    import ui
    out = {"python": sys.version, "general_getVersion": general.getVersion(), "ui_getVersion": ui.getVersion(), "title": ui.getProgTitle()}
    return out


def probe_inventory():
    """Every public callable in every FL module on this build. Compared with the L1 plan by coproducer probe report."""
    inv = {}
    for m in MODULES:
        try:
            mod = __import__(m)
        except ImportError:
            inv[m] = None
            continue
        inv[m] = sorted(n for n in dir(mod) if not n.startswith("_") and callable(getattr(mod, n)))
    return inv


def probe_json():
    import json
    return {"import": True, "roundtrip": json.loads(json.dumps({"a": [1, 2.5, "x", None, True]})) == {"a": [1, 2.5, "x", None, True]}}


def probe_file_io():
    """Can a controller script write and read a file? The answer decides whether staged note files can be used."""
    path = os.path.join(_here(), "probe_io.tmp")
    with open(path, "w") as f:
        f.write("coproducer")
    with open(path) as f:
        back = f.read()
    os.remove(path)
    return {"dir": _here(), "write_read": back == "coproducer"}


def probe_project_shape():
    import channels
    import mixer
    import patterns
    import playlist
    out = {"channels": channels.channelCount(), "mixer_tracks": mixer.trackCount(), "patterns": patterns.patternCount(), "playlist_tracks": playlist.trackCount()}
    out["pattern_names"] = [patterns.getPatternName(i) for i in (0, 1, 2)]
    out["pattern_lengths"] = [patterns.getPatternLength(i) for i in (0, 1, 2)]
    out["tempo"] = mixer.getCurrentTempo()
    out["tempo_unit_note"] = "compare with the tempo shown in FL; if it is 120000 for 120 the unit is milli-BPM"
    return out


def probe_song_pos():
    import transport
    out = {}
    for mode in (0, 1, 2, 3):
        for fn in ("getSongPos", "getSongLength"):
            try:
                out["%s(%d)" % (fn, mode)] = getattr(transport, fn)(mode)
            except Exception as e:  # noqa: BLE001
                out["%s(%d)" % (fn, mode)] = "error " + str(e)
    return out


def probe_routing_names():
    """Sidechain has no documented API; list every routing related name so a human can see what exists."""
    import mixer
    return sorted(n for n in dir(mixer) if "oute" in n or "ide" in n or "ypass" in n or "ink" in n)


def probe_tempo_names():
    """Where is the tempo setter on this build? Lists every name containing 'empo' (setters were added in 25.2.4 per the plan)."""
    found = {}
    for m in MODULES:
        try:
            mod = __import__(m)
        except ImportError:
            continue
        hits = [n for n in dir(mod) if "empo" in n]
        if hits:
            found[m] = hits
    return found


def probe_save_names():
    """Look for any save or export capability anywhere in the API (the save route is probed, not assumed)."""
    found = {}
    for m in MODULES:
        try:
            mod = __import__(m)
        except ImportError:
            continue
        hits = [n for n in dir(mod) if "ave" in n.lower() or "xport" in n.lower() or "render" in n.lower()]
        if hits:
            found[m] = hits
    return found


def probe_fader_law():
    """Write fader positions and read both raw and dB-like values back. Restores the original value. Mutating."""
    import mixer
    original = mixer.getTrackVolume(1)
    rows = []
    try:
        for v in (0.0, 0.25, 0.5, 0.8, 1.0):
            mixer.setTrackVolume(1, v)
            rows.append({"set": v, "raw": mixer.getTrackVolume(1), "mode1": mixer.getTrackVolume(1, 1)})
    finally:
        mixer.setTrackVolume(1, original)
    return {"restored_to": original, "rows": rows}


def probe_undo():
    """Does general.undo() reverse a script write? Mutating."""
    import general
    import mixer
    before = mixer.getTrackVolume(1)
    general.saveUndo("coproducer probe", 0)
    mixer.setTrackVolume(1, 0.3 if before > 0.4 else 0.9)
    changed = mixer.getTrackVolume(1)
    general.undo()
    after = mixer.getTrackVolume(1)
    mixer.setTrackVolume(1, before)
    return {"before": before, "changed": changed, "after_undo": after, "undo_restored": abs(after - before) < 1e-6}


def probe_markers():
    """Add an arrangement marker and read its name back. Mutating; the marker is removed by undo."""
    import arrangement
    import general
    general.saveUndo("coproducer probe marker", 0)
    arrangement.addAutoTimeMarker(0, "probe marker")
    names = []
    for i in range(0, 6):
        try:
            names.append(arrangement.getMarkerName(i))
        except Exception as e:  # noqa: BLE001
            names.append("error " + str(e))
    general.undo()
    return {"names_after_add": names}


READ_ONLY = [("versions", probe_versions), ("inventory", probe_inventory), ("json", probe_json), ("file_io", probe_file_io),
             ("project_shape", probe_project_shape), ("song_pos", probe_song_pos), ("routing_names", probe_routing_names),
             ("save_names", probe_save_names), ("tempo_names", probe_tempo_names)]
WRITING = [("fader_law", probe_fader_law), ("undo", probe_undo), ("markers", probe_markers)]


def run_all():
    for name, fn in READ_ONLY + (WRITING if MUTATING else []):
        _try(name, fn)
    REPORT["_meta"] = {"mutating": MUTATING}
    try:
        import json
        with open(os.path.join(_here(), "probe_report.json"), "w") as f:
            f.write(json.dumps(REPORT, indent=1, sort_keys=True))
        print("probe done: report written to", _here())
    except Exception as e:  # noqa: BLE001
        print("probe done, but the report file could not be written:", e)
        print(REPORT)


def OnInit():
    print("Coproducer Probe loaded; it runs on the next idle tick. MUTATING =", MUTATING)


def OnIdle():
    if not _done[0]:
        _done[0] = True
        run_all()

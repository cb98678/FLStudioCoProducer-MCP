"""Read-only questions about the running FL Studio, asked over the bridge (inlined into the FL-side script).

FL's embedded Python can read files but cannot write them (Gate 0, 2026.1.7), so probe answers travel back as bridge
replies, not as a report file. Each probe is a plain function that returns data or raises; the dispatcher records either.
Python 3.9 compatible: no f-strings, no type hints.
"""
import sys

_FL_MODULES = ["general", "ui", "transport", "mixer", "channels", "patterns", "playlist", "arrangement", "plugins", "device", "midi", "utils", "screen"]


def probe_versions():
    import general
    import ui
    return {"python": sys.version, "general_getVersion": general.getVersion(), "ui_getVersion": ui.getVersion(), "title": ui.getProgTitle()}


def probe_inventory():
    """Every public callable in every FL module on this build."""
    inv = {}
    for m in _FL_MODULES:
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


def _try_write(path):
    """Write, read back and remove one small file. Returns a small dict; never raises."""
    try:
        with open(path, "w") as f:
            f.write("coproducer")
        with open(path) as f:
            back = f.read()
        try:
            import os
            os.remove(path)
            removed = True
        except BaseException as e:  # noqa: BLE001
            removed = "%s: %s" % (type(e).__name__, e)
        return {"ok": back == "coproducer", "removed": removed}
    except BaseException as e:  # noqa: BLE001 - recording the failure is the point
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, e)}


def probe_file_io(dirs=None):
    """Can a script write files, and where? Tries the working folder, the home folder and every folder in dirs."""
    import os
    targets = [("cwd", "coproducer_probe_io.tmp")]
    targets.append(("home", os.path.join(os.path.expanduser("~"), "coproducer_probe_io.tmp")))
    for d in (dirs or []):
        targets.append((d, os.path.join(d, "coproducer_probe_io.tmp")))
    out = {"cwd_is": os.getcwd()}
    for label, path in targets:
        out[label] = _try_write(path)
    return out


_NEW_API = ["patterns.clearPattern", "patterns.setPatternLength", "patterns.incrementPatternLength", "patterns.movePattern",
            "patterns.duplicatePatternData", "mixer.setCurrentTempo", "mixer.getCurrentTempo", "mixer.getTrackCount",
            "mixer.setPluginMixLevel", "mixer.getPluginMixLevel", "mixer.setPluginMuteState", "mixer.getPluginMuteState",
            "general.setNumerator", "general.setDenominator", "general.getProjectTitle", "general.setRecPPQ",
            "channels.getSwing", "channels.setSwing", "channels.fillEachNSteps", "arrangement.selectionSet",
            "arrangement.selectionClear", "arrangement.selectionIsActive", "transport.globalTransport", "transport.setSongPos",
            "transport.getSongPos", "device.midiOutSysex"]


def probe_new_api():
    """Docstring and signature of functions this build has that the stubs lack (or that need exact units confirmed)."""
    import inspect
    out = {}
    for full in _NEW_API:
        mod_name, fn_name = full.split(".")
        row = {}
        try:
            fn = getattr(__import__(mod_name), fn_name)
            row["doc"] = (getattr(fn, "__doc__", None) or "")[:400]
            try:
                row["signature"] = str(inspect.signature(fn))
            except BaseException as e:  # noqa: BLE001
                row["signature"] = "unavailable: %s" % type(e).__name__
        except BaseException as e:  # noqa: BLE001
            row["error"] = "%s: %s" % (type(e).__name__, e)
        out[full] = row
    return out


def _err_text(e):
    return "%s: %s" % (type(e).__name__, str(e)[:160])


def probe_new_api_arity():
    """Learn each function's arity from its TypeError text without running it: nine arguments, then one string."""
    out = {}
    for full in _NEW_API:
        mod_name, fn_name = full.split(".")
        row = {}
        try:
            fn = getattr(__import__(mod_name), fn_name)
        except BaseException as e:  # noqa: BLE001
            out[full] = {"error": _err_text(e)}
            continue
        for label, args in (("nine_args", (0,) * 9), ("one_str", ("x",))):
            try:
                fn(*args)
                row[label] = "ACCEPTED"
            except BaseException as e:  # noqa: BLE001
                row[label] = _err_text(e)
        out[full] = row
    return out


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


def _names_containing(test):
    found = {}
    for m in _FL_MODULES:
        try:
            mod = __import__(m)
        except ImportError:
            continue
        hits = [n for n in dir(mod) if test(n)]
        if hits:
            found[m] = hits
    return found


def probe_tempo_names():
    """Where is the tempo setter on this build? Lists every name containing 'empo'."""
    return _names_containing(lambda n: "empo" in n)


def probe_save_names():
    """Look for any save, export or render capability anywhere in the API."""
    return _names_containing(lambda n: "ave" in n.lower() or "xport" in n.lower() or "render" in n.lower())


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


def _attempt(fn, *args):
    try:
        return {"args": list(args), "returned": repr(fn(*args))[:80]}
    except BaseException as e:  # noqa: BLE001
        return {"args": list(args), "error": _err_text(e)}


def _trial_tempo(mixer):
    """Tempo setter takes whole milli-BPM. getCurrentTempo() gives milli-BPM, getCurrentTempo(True) gives BPM."""
    milli0 = mixer.getCurrentTempo()
    rows = []
    try:
        for v in (127000, 127500, 10000, 9999, 522000, 523000):
            r = _attempt(mixer.setCurrentTempo, v)
            r["readback_milli"] = mixer.getCurrentTempo()
            r["readback_bpm"] = mixer.getCurrentTempo(True)
            rows.append(r)
    finally:
        mixer.setCurrentTempo(milli0)
    return {"original_milli": milli0, "after_restore": mixer.getCurrentTempo(), "trials": rows}


def _trial_swing(channels):
    swing0 = channels.getSwing()
    rows = []
    try:
        for v in (0.25, 1.0, 1.5, 25):
            r = _attempt(channels.setSwing, v)
            r["readback"] = channels.getSwing()
            rows.append(r)
    finally:
        channels.setSwing(swing0)
    return {"original": swing0, "after_restore": channels.getSwing(), "trials": rows}


def _trial_pattern_length(patterns, pat):
    len0 = patterns.getPatternLength(pat)
    rows = []
    for fname, argsets in (("setPatternLength", [(pat, 8)]), ("incrementPatternLength", [(pat, 1), (pat, -1)])):
        for args in argsets:
            r = _attempt(getattr(patterns, fname), *args)
            r["length_after"] = patterns.getPatternLength(pat)
            rows.append({"fn": fname, **r})
    _attempt(patterns.setPatternLength, pat, len0)
    return {"pattern": pat, "original": len0, "restored": patterns.getPatternLength(pat), "trials": rows}


def _trial_reads(mixer, channels, general):
    reads = {}
    for label, fn, args in (("getTrackCount", mixer.getTrackCount, ()), ("getSwing", channels.getSwing, ()),
                            ("getProjectTitle", general.getProjectTitle, ()),
                            ("getPluginMixLevel(1,0)", mixer.getPluginMixLevel, (1, 0)),
                            ("getPluginMuteState(1,0)", mixer.getPluginMuteState, (1, 0))):
        reads[label] = _attempt(fn, *args)
    return reads


def probe_new_api_trial():
    """Call the new write functions with small arguments and read the state back. Restores what it can. Mutating."""
    import channels
    import general
    import mixer
    import patterns
    out = {}
    for label, fn in (("tempo", lambda: _trial_tempo(mixer)), ("swing", lambda: _trial_swing(channels)),
                      ("pattern_length", lambda: _trial_pattern_length(patterns, 1)),
                      ("reads", lambda: _trial_reads(mixer, channels, general)),
                      ("pattern_default", lambda: patterns.isPatternDefault(1))):
        try:
            out[label] = fn()
        except BaseException as e:  # noqa: BLE001
            out[label] = {"error": _err_text(e)}
    return out


def _grid_counts(steps=64):
    """Count lit step-sequencer bits per channel in the active pattern."""
    import channels
    out = []
    for c in range(channels.channelCount()):
        out.append(sum(1 for i in range(steps) if channels.getGridBit(c, i)))
    return out


def probe_clear_experiment():
    """Clone the active pattern, then clear the clone and see what isPatternDefault and patternCount report. Mutating.

    Leaves one extra (cleared) pattern in the project; delete it by hand. Aborts if the clone did not become active.
    """
    import patterns
    src = patterns.patternNumber()
    out = {"source": src, "count_before": patterns.patternCount(), "source_default": patterns.isPatternDefault(src)}
    out["clone_call"] = _attempt(patterns.clonePattern, src)
    new = patterns.patternNumber()
    out["clone"] = new
    if new == src:
        out["aborted"] = "the clone did not become the active pattern; nothing was cleared"
        return out
    out["grid_before"] = _grid_counts()
    out["clone_default_before"] = patterns.isPatternDefault(new)
    out["count_after_clone"] = patterns.patternCount()
    out["clear_call"] = _attempt(patterns.clearPattern, new)
    out["grid_after"] = _grid_counts()
    out["clone_default_after"] = patterns.isPatternDefault(new)
    out["length_after"] = patterns.getPatternLength(new)
    out["count_after_clear"] = patterns.patternCount()
    out["source_default_after"] = patterns.isPatternDefault(src)
    return out


def probe_undo_order():
    """Does saveUndo AFTER a change make general.undo() reverse it? Mutating."""
    import general
    import mixer
    before = mixer.getTrackVolume(1)
    mixer.setTrackVolume(1, 0.3 if before > 0.4 else 0.9)
    changed = mixer.getTrackVolume(1)
    general.saveUndo("coproducer probe after", 0)
    general.undo()
    after = mixer.getTrackVolume(1)
    mixer.setTrackVolume(1, before)
    return {"before": before, "changed": changed, "after_undo": after, "undo_restored": abs(after - before) < 1e-6}


PROBE_TABLE = {"versions": probe_versions, "inventory": probe_inventory, "json": probe_json, "file_io": probe_file_io,
               "project_shape": probe_project_shape, "song_pos": probe_song_pos, "routing_names": probe_routing_names,
               "save_names": probe_save_names, "tempo_names": probe_tempo_names, "new_api": probe_new_api,
               "new_api_arity": probe_new_api_arity}
MUTATING_PROBES = {"fader_law": probe_fader_law, "undo": probe_undo, "markers": probe_markers,
                   "undo_order": probe_undo_order, "new_api_trial": probe_new_api_trial,
                   "clear_experiment": probe_clear_experiment}

"""coproducer setup-midi: the two virtual MIDI ports in loopMIDI and FL Studio's MIDI settings for the bridge, without clicking.

Read from rtxclub's registry on 2026-10-26, where the bridge works (FL Studio 2026, loopMIDI 1.0.16.27):
- loopMIDI keeps its ports as DWORD values under HKCU\\Software\\Tobias Erichsen\\loopMIDI\\Ports (name = 1) and creates them when it starts.
- FL keeps each MIDI device under HKCU\\Software\\Image-Line\\FL Studio <N>\\Devices\\MIDI input\\<port> and ...\\MIDI output\\<port>, all
  values strings. The working bridge: input coproducer-in enabled on port 1 with controller type -3 and script folder "Coproducer" (the
  "# name=" of fl_side/device_coproducer.py), output coproducer-out on port 1. FL writes these keys when it closes, so they are only
  changed while FL is not running.
"""
from __future__ import annotations

import sys

PORTS = ("coproducer-in", "coproducer-out")
LOOPMIDI_KEY = r"Software\Tobias Erichsen\loopMIDI"
LOOPMIDI_EXE = r"C:\Program Files (x86)\Tobias Erichsen\loopMIDI\loopMIDI.exe"
FL_KEY = r"Software\Image-Line"
INPUT = {"Type": "-3", "ScriptFolder": "Coproducer", "IDString": "-", "Port": "1", "Enabled": "1"}
INPUT_OFF = {"Enabled": "0", "Port": "-1"}            # coproducer-out as an input stays off: the host program listens on it
OUTPUT = {"Port": "1", "Sync": "0", "SendAllNotesOff": "1", "IDString": "-"}
OUTPUT_OFF = {"Port": "-1"}


def plan(fl_versions: list[str]) -> list[tuple[str, str, str, object]]:
    """[(key, value name, kind 'dword' or 'sz', data)] to write: the loopMIDI ports, and the FL device settings for each FL version key."""
    rows = [(LOOPMIDI_KEY + "\\Ports", p, "dword", 1) for p in PORTS]
    for ver in fl_versions:
        base = "%s\\%s\\Devices" % (FL_KEY, ver)
        for name, vals in ((PORTS[0], INPUT), (PORTS[1], INPUT_OFF)):
            rows += [("%s\\MIDI input\\%s" % (base, name), k, "sz", v) for k, v in vals.items()]
        for name, vals in ((PORTS[1], OUTPUT), (PORTS[0], OUTPUT_OFF)):
            rows += [("%s\\MIDI output\\%s" % (base, name), k, "sz", v) for k, v in vals.items()]
    return rows


def fl_version_keys() -> list[str]:
    """FL Studio's per-version keys under HKCU\\Software\\Image-Line ("FL Studio 26"), newest first."""
    import winreg
    out = []
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, FL_KEY) as k:
            i = 0
            while True:
                try:
                    name = winreg.EnumKey(k, i)
                except OSError:
                    break
                if name.startswith("FL Studio ") and name.split()[-1].isdigit():
                    out.append(name)
                i += 1
    except OSError:
        pass
    return sorted(out, key=lambda n: -int(n.split()[-1]))


def write(rows: list) -> int:
    import winreg
    for key, name, kind, data in rows:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key) as k:
            winreg.SetValueEx(k, name, 0, winreg.REG_DWORD if kind == "dword" else winreg.REG_SZ, data)
    return len(rows)


def run(fl_running: bool, out=print, start_loopmidi: bool = True) -> int:
    """Write the ports and FL's settings. Refuses while FL runs (it would overwrite them when it closes). Returns an exit code."""
    if not sys.platform.startswith("win"):
        out("setup-midi is for Windows")
        return 1
    if fl_running:
        out("FL Studio is running: close it first (it saves its MIDI settings when it closes and would undo these).")
        return 3
    vers = fl_version_keys() or ["FL Studio 26"]
    n = write(plan(vers))
    out("wrote %d settings: loopMIDI ports %s; FL MIDI devices for %s" % (n, ", ".join(PORTS), ", ".join(vers)))
    if start_loopmidi:
        import os
        import subprocess
        from pathlib import Path
        exe = Path(LOOPMIDI_EXE)
        if exe.is_file():
            listed = subprocess.run(["tasklist", "/FI", "IMAGENAME eq loopMIDI.exe", "/NH"], capture_output=True, text=True).stdout
            if "loopmidi.exe" in listed.lower():
                out("loopMIDI is already running: ports it does not show yet appear when it starts next (or add them in its window now)")
            else:
                subprocess.Popen([str(exe)], creationflags=getattr(subprocess, "DETACHED_PROCESS", 0), close_fds=True)
                out("started loopMIDI")
            import winreg
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run") as k:
                winreg.SetValueEx(k, "loopMIDI", 0, winreg.REG_SZ, '"%s"' % exe)
            out("loopMIDI starts with Windows")
        else:
            out("loopMIDI is not installed: winget install --id TobiasErichsen.loopMIDI -e   (the installer does this)")
            return 2
        del os
    return 0

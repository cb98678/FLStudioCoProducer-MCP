"""Plain-language instructions printed by setup. Sources: loopMIDI page and the FL MIDI scripting manual."""

LOOPMIDI = """1. Install loopMIDI (https://www.tobias-erichsen.de/software/loopmidi.html).
2. Open it. In "New port-name" type  coproducer-in  and click the + button.
3. Type  coproducer-out  and click + again. Two ports must be listed.
4. Tick "Autostart" and "Start minimized" in loopMIDI, so the ports exist whenever Windows starts."""

MIDI_SETTINGS = """1. Start FL Studio (restart it once so it sees the new ports and the new script).
2. Options > MIDI Settings.
3. In the Input list, select  coproducer-in  and tick Enable. In the Output list, select  coproducer-out  and enable it (hover its Port knob and scroll the mouse wheel; the power icon appears on the row).
4. With the input selected, set Controller type to  Coproducer (user)  (the manual says user scripts show a "(user)" suffix).
5. Set the Port number of the input  coproducer-in  and of the output  coproducer-out  to the same value (verified working with 1 and 1 on FL 2026.1.7). The input list also shows  coproducer-out; leave that input disabled, because the host program listens on it.
6. Open View > Script output. It should show "Coproducer bridge ready" and a line "Coproducer: port number N, assigned True". If you edit the script later, use Reload in that window. While you run a probe, lines starting "Coproducer: sysex in" show that FL received the request, and "sysex out" that it answered.
7. Back in a terminal run:  coproducer probe ping   (it must print the FL version within 2 seconds)."""

FL_MANUAL = "https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/midi_scripting.htm"

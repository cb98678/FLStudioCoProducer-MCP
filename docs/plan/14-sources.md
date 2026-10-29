# 14. Sources

As of October 18, 2026. Each source has a status:

- **READ**: opened and read during planning.
- **SEEN**: appeared in search results (title and link only). Verify before relying on it.
- **VENDOR**: a well-known vendor page that was not opened this round.

Re-check any version-dependent claim before building on it. Where documentation and a live FL install disagree, the live install and the Gate 0 inventory probe win.

## 1. Image-Line official documentation (authority for FL behavior)

| Source | Used for | Status |
| --- | --- | --- |
| [MIDI scripting manual](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/midi_scripting.htm) | Script location, modules, events, output window | READ |
| [Piano roll scripting](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/pianoroll_scripting_api.htm) | `.pyscript` location, `flpianoroll` availability, factory reference file | READ |
| [Export and save formats](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/fformats_save_export.htm) | Command-line render, split mixer tracks | READ |
| [Tools menu](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/menu_tools.htm) | Audio Logger (memory only) | READ |
| [What's new in FL Studio 2026](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/basics_new.htm) | Release date, maintenance versions, scripting additions, MIDI score opening | READ |
| [What's new in FL Studio 25](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/basics_new_25.htm) | Tempo setters, MIDI import behavior, Extract Stems, update policy | READ |

## 2. FL Studio API reference pages (signatures and API version tags)

The repository is marked unmaintained by its owners and points back to the manual. These pages are used for signatures only, behind the manual and the live interpreter.

| Source | Used for | Status |
| --- | --- | --- |
| [FL-Studio-API-Stubs repository](https://github.com/IL-Group/FL-Studio-API-Stubs) | Unmaintained notice | READ |
| [Reference site](https://il-group.github.io/FL-Studio-API-Stubs/) | Index of module pages | SEEN |
| [Mixer tracks](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/mixer/tracks/) | Disk access disabled, peaks, route levels, volume | READ |
| [Plugins](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/plugins/) | Parameters, VST parameter counts, API tags | READ |
| [Transport](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/transport/) | Start toggle, loop toggle | READ |
| [Channel notes](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/channels/notes/) | `midiNoteOn`, quick quantize | READ |
| [Pattern properties](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/patterns/properties/) | Pattern functions | READ |
| [flpianoroll](https://il-group.github.io/FL-Studio-API-Stubs/piano_roll_scripting/flpianoroll/) | Piano roll API signatures | READ |
| [FL MIDI scripting 101](https://flmidi-101.readthedocs.io/en/latest/scripting/fl_midi_api.html) | Embedded interpreter notes | SEEN |
| [FL Studio API Stubs on PyPI](https://pypi.org/project/fl-studio-api-stubs/) | Last release listing | SEEN |

## 3. Local models and tools

| Source | Used for | Status |
| --- | --- | --- |
| [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5) | License, Python versions, VRAM tiers, features | READ |
| [acestep.vst3](https://github.com/ace-step/acestep.vst3) | A VST3 plugin option | SEEN |
| [Music Flamingo model card](https://huggingface.co/nvidia/music-flamingo-hf) | Size, license, tested hardware, checkpoint | READ |
| [libretta on PyPI](https://pypi.org/project/libretta/) | Demucs weight size, Basic Pitch notes | SEEN |
| [AceForge](https://github.com/audiohacking/aceforge) | Example Demucs and Basic Pitch pipeline | SEEN |
| [pyloudnorm on PyPI](https://pypi.org/project/pyloudnorm/0.0.1) | BS.1770 loudness implementation | SEEN |
| [MCP Python SDK documentation](https://py.sdk.modelcontextprotocol.io/) | Server framework | SEEN |
| [mcp on PyPI](https://pypi.org/project/mcp/) | Release listing | SEEN |
| [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html) | Virtual MIDI ports | VENDOR |

## 4. Local LLM and GUI-grounding landscape (search results only)

Used to build shortlists. No model is chosen from these. Benchmarks in file 08 decide.

| Source | Used for | Status |
| --- | --- | --- |
| [Top 7 coding models you can run locally in 2026, KDnuggets](https://www.kdnuggets.com/top-7-coding-models-you-can-run-locally-in-2026) | Candidate coding models | SEEN |
| [Best Ollama models, Morph](https://www.morphllm.com/best-ollama-models) | Candidate models by VRAM | SEEN |
| [The local LLM stack in 2026, DEV](https://dev.to/thegatewayguy/the-local-llm-stack-in-2026-what-actually-works-ib1) | Runtime options | SEEN |
| [Best local LLMs for 16GB, Atomic Chat](https://atomic.chat/blog/guides/best-local-llm-16gb) | 16 GB candidates | SEEN |
| [GUI grounding models 2026, perea.ai](https://www.perea.ai/research/gui-grounding-models-2026) | Vision candidates | SEEN |
| [UGround](https://github.com/OSU-NLP-Group/UGround) | Vision candidate | SEEN |
| [GUI-Actor](https://microsoft.github.io/GUI-Actor/) | Vision candidate | SEEN |
| [Building desktop GUI agents in 2026, DEV](https://dev.to/agdex_ai/beyond-the-browser-building-desktop-gui-agents-in-2026-with-ui-tars-claude-computer-use-and-2gpe) | GUI agent landscape | SEEN |

## 5. SysEx size behavior (search results only)

| Source | Used for | Status |
| --- | --- | --- |
| [JUCE forum: SysEx truncated to 240 bytes](https://forum.juce.com/t/sysex-midi-message-truncated-to-240-bytes/67818) | Conservative frame size | SEEN |
| [ALSA SysEx split into 256 byte chunks](https://www.midimusicadventures.com/phpbb/viewtopic.php?p=18500) | Conservative frame size | SEEN |
| [Red Hat bug on 4096-byte SysEx buffer](https://bugzilla.redhat.com/show_bug.cgi?id=2517136) | Buffer limits can fail large transfers | SEEN |

## 6. Prior art (pitfalls only; nothing reused)

| Source | What it taught | Status |
| --- | --- | --- |
| [rosasynthesiz/flstudio-mcp](https://github.com/rosasynthesiz/flstudio-mcp) | API cannot load plugins or audio files or render audio | READ |
| [Postfader on PyPI](https://pypi.org/project/postfader-fl-studio-mcp/) | Silently ignored writes, verified writes, fake API for tests | READ |
| [Flapi](https://github.com/MaddyGuthridge/Flapi) | Remote control of FL's API over MIDI exists | SEEN |

## 7. Method

| Source | Used for | Status |
| --- | --- | --- |
| Your `agentic-prompt-architect.md` | Spec, Verifier, Environment, Loop; verifiability ladder; autonomy slider; failure modes; no em dashes | READ (uploaded file) |
| RFC 2119 | MUST and SHOULD language | Convention only |

## 8. How to refresh this list

1. Re-open each READ source before Gate 0 and note any change. The FL 2026 page changes with each maintenance update.
2. Open each SEEN source before it is relied on, and change its status to READ or remove it.
3. Add the live API inventory and the factory piano roll reference file as primary sources once Gate 0 has produced them. They outrank every web page above.

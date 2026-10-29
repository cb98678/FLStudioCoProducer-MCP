"""Key of every demo full-mix render from the audio (dsp.estimate_key, first 120 s), to cross-check the key read from the project notes.

    .venv\\Scripts\\python.exe tools\\demo_study\\keys.py     # writes sandbox\\demo_study\\audio_keys.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from coproducer import dsp  # noqa: E402

out = {}
for p in sorted((ROOT / "sandbox" / "demo_study" / "wav").glob("*.wav")):
    x, rate = dsp.load_audio(str(p), 120.0)
    out[p.stem] = dsp.estimate_key(x, rate)
    print(p.stem, out[p.stem])
(ROOT / "sandbox" / "demo_study" / "audio_keys.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")

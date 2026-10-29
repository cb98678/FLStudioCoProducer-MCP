"""How each model stack is installed. Data plus one function that turns it into commands.

Every version below is exact. They are the versions measured working on the development machine (Windows 11, RTX 3090,
2026-10-18); change one only after the smoke test (coproducer probe models) passes with the new value. When models/locks/<stack>.txt exists
(frozen from the working environment, 2026-10-25), the install uses it, so transitive packages are exact too; the direct pins here must match it.
Sources checked 2026-10-18.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ACESTEP_REPO = "https://github.com/ACE-Step/ACE-Step-1.5.git"      # README: git clone, then uv sync (no pip package is documented)
ACESTEP_COMMIT = "ca1e85fe9430179831e6bc6be790c332190a3866"        # v0.1.8-21-gca1e85f; its uv.lock fixes every dependency
WHISPER_REVISION = "06f233fe06e710322aca913c1bc4249a0d71fce1"  # openai/whisper-large-v3 snapshot cached on the host since 2026-10-22
# The files a worker loads from each pinned snapshot (transformers takes model.safetensors). The whole Whisper repo is about 25 GB because
# it also carries fp32, PyTorch .bin and Flax copies of the same weights; these patterns keep it to about 3 GB. Repos not listed download whole.
SNAPSHOT_FILES = {"openai/whisper-large-v3": ["*.json", "*.txt", "model.safetensors"], "xlm-roberta-base": ["*.json", "*.model", "model.safetensors"]}
TORCH_HELP = "https://pytorch.org/get-started/locally/"            # pick the CUDA index there and set [gpu] torch_index in config.toml
# torch_index measured on this machine: https://download.pytorch.org/whl/cu128 (holds torch up to 2.11.0 for Windows and Python 3.12).
# Newer torch builds sit on the cu130 index and need a driver that supports CUDA 13; the cu128 index works with the current driver.

STACKS = {
    "demucs": {"python": "3.12", "torch": "2.11.0", "torchaudio": "2.11.0",
               "packages": ["demucs==4.1.0", "numpy==2.5.4"],
               # The checkpoints torch hub keeps (htdemucs, and the four of htdemucs_ft); each name ends in the start of its sha256, checked
               # on the host 2026-10-25. The host's network resets some downloads (WinError 10054), so the download retries.
               "files": {n: {"url": "https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/" + n, "dest": "~/.cache/torch/hub/checkpoints/" + n, "bytes": b, "sha256": h}
                         for n, b, h in (("955717e8-8726e21a.th", 84141911, "8726e21a993978c7ba086d3872e7608d7d5bfca646ca4aca459ffda844faa8b4"),
                                         ("f7e0c4bc-ba3fe64a.th", 84141271, "ba3fe64ae8ef66ac9a4857222ce48efbdc5eb3ad375cb79dd13debee5aaa4066"),
                                         ("d12395a8-e57c48e6.th", 84141271, "e57c48e6b0e38af4f7118d7bd08c49f0a0c0edf7d09143bdd902ea0d237303e6"),
                                         ("92cfc3b6-ef3bcb9c.th", 84141271, "ef3bcb9c8b40d14ae5d51b6db2587339cc12c6b77c0be151ce6d69002e087bf2"),
                                         ("04573f0d-f3cf25b2.th", 84141271, "f3cf25b222c4eed7cd49dd8b2c9597d50c18bd154090f7b919cfa5f93cf22c49"))},
               "doc": "https://github.com/adefossez/demucs"},
    "basicpitch": {"python": "3.11", "torch": None,
                   # TensorFlow 2.14 fails to import under numpy 2; resampy imports pkg_resources, which setuptools 82 removed.
                   "packages": ["basic-pitch==0.4.0", "numpy==1.26.4", "setuptools==80.10.2", "tensorflow==2.14.0", "keras==2.14.0",
                                "resampy==0.4.2", "librosa==0.11.0", "scipy==1.17.1", "soundfile==0.14.0"],
                   "doc": "https://github.com/spotify/basic-pitch"},
    # Pins checked 2026-10-19 on PyPI (transformers 5.20.2, accelerate 1.15.0). librosa and soundfile load the audio files for the processor.
    "critique": {"python": "3.12", "torch": "2.11.0", "torchaudio": "2.11.0",
                 "packages": ["transformers==5.20.2", "accelerate==1.15.0", "librosa==0.11.0", "soundfile==0.14.0"],
                 # Listed by file because the hub's /api listing is reset on the development machine (WinError 10054) while file downloads work,
                 # and snapshot_download then returns the near-empty local cache without an error. Checked 2026-10-19 against the repo file list.
                 # The same environment runs Whisper (tools/transcribe_vocals.py, openai/whisper-large-v3 at WHISPER_REVISION), checked 2026-10-25.
                 # Whisper large-v3 for word times runs offline from this snapshot; a fresh machine downloads it here (2026-10-26).
                 "hf_snapshots": {"openai/whisper-large-v3": WHISPER_REVISION},
                 # Music Flamingo (the audio critic, about 16 GB) is optional: install-models --with-optional, or the installer's full profile.
                 "weights_optional": True,
                 "weights": {"repo": "nvidia/music-flamingo-2601-hf", "revision": "6b5be086d52f65a1e204cb0faf70bf54e2741ecd",
                             "files": ["config.json", "generation_config.json", "processor_config.json", "tokenizer_config.json",
                                       "tokenizer.json", "chat_template.jinja", "model.safetensors"]},
                 "doc": "https://huggingface.co/nvidia/music-flamingo-2601-hf"},
    # The checkpoints come from ACE-Step's own downloader (acestep-download in its pyproject: the main model with the 1.7B LM, then the 0.6B LM
    # the default variant uses) into <clone>/checkpoints, where the runner reads them. It takes no revision, so these files are not pinned;
    # they are optional downloads (install-models --with-optional, install.ps1 -Models full).
    "acestep": {"clone": ACESTEP_REPO, "commit": ACESTEP_COMMIT, "doc": "https://github.com/ace-step/ACE-Step-1.5",
                "downloads": [["acestep-download", "--dir", "checkpoints"], ["acestep-download", "--model", "acestep-5Hz-lm-0.6B", "--dir", "checkpoints"]],
                "downloads_optional": True},
    # Music analysis (runners/mir_runner.py): beats and downbeats, vocal pitch. Installed and measured on the host 2026-10-25: 475 beats and
    # 119 four-beat bars on the Friends stems in 2.0 s, 20 s of vocal pitch in 21 s. torchcrepe carries its weights in the wheel; the beat_this
    # checkpoint is a file from the authors' server, kept under models/weights and checked by its hash (81 MB).
    "mir": {"python": "3.12", "torch": "2.11.0", "torchaudio": "2.11.0",
            # MuQ-MuLan (embeddings for reference similarity) needs transformers 4: under 5.20.2 its conformer fails on _attn_implementation
            # (measured on the host 2026-10-25); 4.48.3 loads it and embeds 30 s of audio in 16 s with the model load.
            "packages": ["beat-this==1.1.0", "torchcrepe==0.0.24", "rotary-embedding-torch==0.6.5", "soxr==1.1.0", "einops==0.8.2",
                         "librosa==0.11.0", "soundfile==0.14.0", "numpy==2.4.6", "scipy==1.17.1", "muq==0.1.0", "transformers==4.48.3"],
            # Hugging Face snapshots the worker reads offline (refs/main in the cache must point at these): weights CC-BY-NC 4.0 (MuQ-MuLan).
            "hf_snapshots": {"OpenMuQ/MuQ-MuLan-large": "2e01c796b71dca71b45251384c04cd7b237c9020", "xlm-roberta-base": "e73636d4f797dec63c3081bb6ed5c7b0bb3f2089"},
            "snapshots_optional": True,   # only the reference-similarity judge uses MuQ-MuLan
            "files": {"beat_this_final0": {"url": "https://cloud.cp.jku.at/public.php/dav/files/7ik4RrBKTS273gp/final0.ckpt",
                                           "dest": "weights/beat_this/final0.ckpt", "bytes": 81058141,
                                           "sha256": "8c328b45f59d8dd3dff219253ff6a8d6482be57d0133a29140e2febbf8eb8331"}},
            "doc": "https://github.com/CPJKU/beat_this"},
    # Vocal separation (runners/sep_runner.py): Mel-Band RoFormer through python-audio-separator. Installed and measured on the host 2026-10-25:
    # 60 s of the Friends mix in 3 s on the GPU, 9.6 dB SDR for the vocal against the stem the mix was summed from. audio-separator fetches its
    # own model files from its repositories; install-models lets it, then checks every file against the hashes below.
    "sep": {"python": "3.12", "torch": "2.11.0", "torchaudio": "2.11.0",
            "packages": ["audio-separator[gpu]==0.47.1", "audioread==3.1.0"],
            "separator_models": {"vocals_mel_band_roformer.ckpt": {"bytes": 913106900, "sha256": "87201f4d31afb5bc79993230fc49446918425574db48c01c405e44f365c7559e"},
                                 "vocals_mel_band_roformer.yaml": {"bytes": 944, "sha256": "b958b29c8f7195f0d86bee6759a33980db675c4ecaf2fcaa80fa125828e6cd38"}},
            "model_dir": "weights/audio_separator",
            "doc": "https://github.com/nomadkaraoke/python-audio-separator"},
    # Serum 2 played headless (runners/serum_runner.py): hear a generated preset and get the state Serum itself saves for it, without FL.
    # pedalboard is GPL-3.0 and runs in its own environment as a separate process. Measured on the host 2026-10-26 (Python 3.11.3):
    # Serum 2.1.5 loads with plugin_name "Serum 2" from the binary inside Serum2.vst3; pins as installed there.
    # serum-mcp's own preset writer (runners/serummcp_runner.py) in its clone's environment, made by its uv.lock. Already cloned on the host
    # at sandbox\third_party\serum-mcp (2026-10-23); "dir" keeps it there instead of models\serummcp.
    "serummcp": {"clone": "https://github.com/Celian-mrc/serum-mcp.git", "commit": "eada85a87f529e39f0c735d403c1067e00bbcc6c",
                 "dir": "sandbox/third_party/serum-mcp", "doc": "https://github.com/Celian-mrc/serum-mcp"},
    "serum": {"python": "3.11", "torch": None,
              "packages": ["pedalboard==0.9.26", "numpy==2.4.6", "soundfile==0.14.0", "zstandard==0.25.0", "cbor2==6.1.3"],
              "doc": "https://github.com/spotify/pedalboard"},
}


def separator_model(home: Path, cfg: dict, name: str = "vocals_mel_band_roformer.ckpt") -> dict:
    """{"model_dir", "model", "sha256"} of a pinned audio-separator checkpoint."""
    d = STACKS["sep"]
    return {"model_dir": str(home / cfg["paths"]["models"] / d["model_dir"]), "model": name, "sha256": d["separator_models"][name]["sha256"]}


def _dest(home: Path, cfg: dict, dest: str) -> str:
    """Where a pinned file lives: under the models folder, or a home-relative path (~/...) for caches a library reads itself (torch hub)."""
    return str(Path(dest).expanduser()) if dest.startswith("~") else str(home / cfg["paths"]["models"] / dest)


def weight_file(stack: str, key: str, home: Path, cfg: dict) -> tuple[str, str]:
    """(local path, sha256) of a pinned weight file of a stack (STACKS[stack]["files"][key])."""
    f = STACKS[stack]["files"][key]
    return _dest(home, cfg, f["dest"]), f["sha256"]


def venv_python(root: Path) -> Path:
    return root / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def weights_command(stack: str, home: Path, cfg: dict):
    """The command that downloads a stack's weights into the Hugging Face cache, or None. Model workers run offline (HF_HUB_OFFLINE=1), so this is the one place that downloads."""
    py = str(venv_python(home / cfg["paths"]["models"] / "envs" / stack))
    files = STACKS.get(stack, {}).get("files")
    if files:  # plain files from a URL, each checked against its pinned hash; an existing file with the right hash is kept
        rows = [(_dest(home, cfg, f["dest"]), f["url"], f["sha256"]) for f in files.values()]
        return [py, "-c", "import hashlib, os, time, urllib.request\nfor p, u, h in %r:\n    ok = os.path.isfile(p) and hashlib.sha256(open(p, 'rb').read()).hexdigest() == h\n"
                "    for attempt in range(6):\n        if ok:\n            break\n        try:\n"
                "            os.makedirs(os.path.dirname(p), exist_ok=True); urllib.request.urlretrieve(u, p + '.part')\n"
                "            assert hashlib.sha256(open(p + '.part', 'rb').read()).hexdigest() == h, 'hash mismatch: ' + u\n            os.replace(p + '.part', p); ok = True\n"
                "        except OSError:\n            time.sleep(3)\n    assert ok, 'could not download ' + u\n    print(p)" % (rows,)]
    sep = STACKS.get(stack, {}).get("separator_models")
    if sep:  # audio-separator downloads its own files; each must then match its pinned hash
        d = str(home / cfg["paths"]["models"] / STACKS[stack]["model_dir"])
        pins = {k: v["sha256"] for k, v in sep.items()}
        main = [k for k in sep if not k.endswith(".yaml")]
        return [py, "-c", "import hashlib, os\nfrom audio_separator.separator import Separator\nd = %r\nos.makedirs(d, exist_ok=True)\ns = Separator(model_file_dir=d)\n"
                "for m in %r:\n    s.load_model(m)\nfor f, h in %r.items():\n    got = hashlib.sha256(open(os.path.join(d, f), 'rb').read()).hexdigest()\n"
                "    assert got == h, 'hash mismatch: ' + f\n    print(f, 'ok')" % (d, main, pins)]
    w = STACKS.get(stack, {}).get("weights")
    if not w:
        return None
    # Offline mode is cleared first: this is the one command that is meant to download, and a stray HF_HUB_OFFLINE in the shell would make it fail.
    return [py, "-c", "import os; os.environ.pop('HF_HUB_OFFLINE', None); from huggingface_hub import hf_hub_download as d; [print(d(%r, f, revision=%r)) for f in %r]"
            % (w["repo"], w.get("revision"), w["files"])]


def snapshots_command(stack: str, home: Path, cfg: dict):
    """The command that puts a stack's pinned Hugging Face snapshots (repo at a revision) into the local cache, or None. Workers read them
    offline later, so a fresh machine needs this once (Whisper for the critique stack, MuQ-MuLan for mir)."""
    snaps = STACKS.get(stack, {}).get("hf_snapshots")
    if not snaps:
        return None
    py = str(venv_python(home / cfg["paths"]["models"] / "envs" / stack))
    jobs = [(r, v, SNAPSHOT_FILES.get(r)) for r, v in sorted(snaps.items())]
    return [py, "-c", "import os; os.environ.pop('HF_HUB_OFFLINE', None); from huggingface_hub import snapshot_download as s; "
            "[print(s(r, revision=v, allow_patterns=p)) for r, v, p in %r]" % (jobs,)]


def zip_url(d: dict) -> str:
    """A GitHub repository's archive of the pinned commit, for a machine without git."""
    repo = d["clone"].rstrip("/").removesuffix(".git").split("github.com/", 1)[1]
    return "https://codeload.github.com/%s/zip/%s" % (repo, d["commit"])


def unzip_command(d: dict, root: Path) -> list:
    """Download the pinned commit's archive and unpack it as root (GitHub puts it in one folder named REPO-COMMIT)."""
    return [sys.executable, "-c", "import io, os, shutil, sys, urllib.request, zipfile\nu, root = sys.argv[1], sys.argv[2]\n"
            "data = urllib.request.urlopen(u, timeout=300).read()\nz = zipfile.ZipFile(io.BytesIO(data))\ntop = z.namelist()[0].split('/')[0]\n"
            "tmp = root + '.part'\nshutil.rmtree(tmp, ignore_errors=True)\nz.extractall(tmp)\nos.replace(os.path.join(tmp, top), root)\n"
            "shutil.rmtree(tmp, ignore_errors=True)\nprint('unpacked', u, 'to', root)", zip_url(d), str(root)]


def install_plan(stack: str, home: Path, cfg: dict) -> dict:
    """Return {commands: [(argv, cwd)], python: path-of-interpreter-after-install, notes: [...]} for one stack."""
    if stack not in STACKS:
        return {"commands": [], "python": None, "notes": ["no installer for %r; the vision model is chosen after bench-vision" % stack]}
    d, models = STACKS[stack], home / cfg["paths"]["models"]
    if "clone" in d:
        root = home / d["dir"] if d.get("dir") else models / stack
        if not root.exists() and not shutil.which("git"):          # no git on this machine: the commit's archive instead (same files, no history)
            cmds = [(unzip_command(d, root), None)]
        elif not root.exists():
            cmds = [(["git", "clone", d["clone"], str(root)], None), (["git", "checkout", "--detach", d["commit"]], str(root))]
        else:
            cmds = [(["git", "checkout", "--detach", d["commit"]], str(root))] if (root / ".git").exists() else []
        cmds = cmds + [(["uv", "sync", "--locked"], str(root))]
        dl = [(["uv", "run", "--locked", *x], str(root)) for x in d.get("downloads", [])]
        optional = list(range(len(cmds), len(cmds) + len(dl))) if d.get("downloads_optional") else []
        return {"commands": cmds + dl, "optional": optional,
                "python": str(venv_python(root / ".venv")),
                "notes": ["pinned to commit %s" % d["commit"][:9], "models download on first use; set [paths] acestep in config.toml if you cloned elsewhere"], "root": str(root)}
    env = models / "envs" / stack
    py, idx = str(venv_python(env)), cfg["gpu"].get("torch_index", "")
    # --allow-existing: running the install again (after a dropped download, or by the installer on an upgrade) keeps the environment and
    # lets uv pip install bring it to the pins; without it uv refuses an existing environment.
    cmds = [(["uv", "venv", "--allow-existing", "--python", d["python"], str(env)], None)]
    if d["torch"]:
        torch_pins = ["torch==" + d["torch"], "torchaudio==" + d["torchaudio"]]
        cmds.append((["uv", "pip", "install", "--python", py, *torch_pins] + (["--index-url", idx] if idx else []), None))
    lock = home / "models" / "locks" / (stack + ".txt")
    if lock.is_file():  # the whole environment as frozen on the working machine, transitive packages included (record_lock writes it)
        cmds.append((["uv", "pip", "install", "--python", py, "-r", str(lock), "--index-strategy", "unsafe-best-match"]
                     + (["--extra-index-url", idx] if idx else []), None))
    else:
        cmds.append((["uv", "pip", "install", "--python", py, *d["packages"]], None))
    optional = []
    snap = snapshots_command(stack, home, cfg)
    if snap:
        if d.get("snapshots_optional"):
            optional.append(len(cmds))
        cmds.append((snap, None))
    if weights_command(stack, home, cfg):
        if d.get("weights_optional"):
            optional.append(len(cmds))
        cmds.append((weights_command(stack, home, cfg), None))
    notes = [] if idx or not d["torch"] else ["no [gpu] torch_index set: the default torch build is CPU only (%s)" % TORCH_HELP]
    if optional:
        notes.append("optional downloads (install-models --with-optional): %d" % len(optional))
    return {"commands": cmds, "python": py, "notes": notes, "optional": optional}

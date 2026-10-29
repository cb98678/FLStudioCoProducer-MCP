"""Shared pytest fixture: a full in-process rig (fake FL, generated FL-side script, loopback, bridge, registry)."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from .bridge import BridgeClient
from .fakefl import FakeFL
from .loopback import LoopbackTransport, load_device_script
from .registry import Registry
from .services import clear_services

MODULES = Path(os.environ.get("COPRODUCER_MODULES") or Path(__file__).resolve().parents[2] / "modules")
DATA = Path(__file__).resolve().parent / "data"


class Rig:
    def __init__(self, fake, script, transport, reg, client) -> None:
        self.fake, self.script, self.transport, self.reg, self.client = fake, script, transport, reg, client

    def call(self, name, /, **kw):
        return self.reg.call(name, **kw)


@pytest.fixture
def rig():
    fake = FakeFL()
    script = load_device_script(fake)
    transport = LoopbackTransport(fake, script)
    reg = Registry(MODULES, ceiling="A2").load()
    client = BridgeClient(reg, transport)
    client.attach(reg)
    reg.activate()
    yield Rig(fake, script, transport, reg, client)
    fake.uninstall()
    clear_services()


@pytest.fixture
def wav(tmp_path):
    """wav("name", samples, rate=48000) writes a float WAV file in a temp folder and returns its path."""
    from .synth import RATE, to_wav

    def make(name, x, rate=RATE, subtype="FLOAT"):
        return to_wav(str(tmp_path / f"{name}.wav"), x, rate, subtype)
    return make


@pytest.fixture
def run(tmp_path):
    """run(collab=None) builds an orchestrator Session wired to a fake FL; run.fake and run.session are set after the call."""
    from .orchestrator.collab import ScriptedCollab
    from .orchestrator.session import new_session

    made = []

    def build(collab=None, run_dir=None, fake=None):
        fake = fake or FakeFL()
        script = load_device_script(fake)
        s = new_session(MODULES, run_dir or tmp_path / "run", collab or ScriptedCollab(approve_all=True))
        BridgeClient(s.registry, LoopbackTransport(fake, script)).attach(s.registry)
        s.registry.activate()
        made.append(fake)
        build.fake, build.session = fake, s
        return s
    yield build
    for f in made:
        f.uninstall()
    clear_services()


def build_ml():
    """A Scheduler whose workers are the fake runner, installed as the scheduler service. Returns a handle with .sched and .state."""
    from .models.factory import make_worker_factory
    from .models.scheduler import Scheduler
    from .models.spec import ModelSpec
    from .services import set_service

    specs = {n: ModelSpec(n, role, "test", vram_typical_mb=mb, default_variant="v1", runner="fake_runner.py", optional=n == "flamingo")
             for n, role, mb in (("demucs", "separate", 4000), ("basicpitch", "transcribe", 0), ("acestep", "generate", 12000),
                                 ("flamingo", "critique", 14000), ("vision", "ground_gui", 6000), ("mir", "analyze", 1500), ("roformer", "separate", 4000), ("whisper", "transcribe", 5000), ("serum", "generate", 0), ("serummcp", "generate", 0))}
    state = {"free": 16000}

    class Handle:
        pass

    h = Handle()
    h.state = state
    h.sched = Scheduler(specs, make_worker_factory({}), lambda: (state["free"] - sum(r.need_mb for r in h.sched.resident.values()), 16000))
    set_service("scheduler", h.sched)
    return h


@pytest.fixture
def ml(rig):
    """Install a Scheduler whose workers are the fake runner; model names match the real registry. ml.sched, ml.free_mb."""
    h = build_ml()
    yield h
    h.sched.unload_all()


class Halt:
    def __init__(self) -> None:
        self.flag = False

    def is_set(self) -> bool:
        return self.flag

    def set(self) -> None:
        self.flag = True


def build_desk(sandbox_root):
    """A FakeDesktop installed as the desktop service with a halt flag and a desktop config. Returns a handle with .fake, .halt, .cfg."""
    from .fakedesktop import FakeDesktop
    from .services import set_service

    class Handle:
        pass

    h = Handle()
    h.fake, h.halt = FakeDesktop(), Halt()
    h.cfg = {"display_scale": 0.0, "allow_unverified": True, "action_budget": 200, "timeout_scale": 0.02, "anchors": {}}
    set_service("recipes_dir", str(DATA / "gui_recipes"))
    set_service("templates_dir", str(DATA / "gui_templates"))
    set_service("desktop", h.fake)
    set_service("halt", h.halt)
    set_service("desktop_config", h.cfg)
    set_service("sandbox_root", str(sandbox_root))
    return h


@pytest.fixture
def desk(rig, tmp_path):
    """A FakeDesktop installed as the desktop service, with a halt flag and a desktop config. desk.fake, desk.halt, desk.cfg."""
    return build_desk(tmp_path)


@pytest.fixture
def procs(rig):
    """A FakeProcs installed as the procs service. procs.open says whether FL is running; procs.log lists close and launch calls."""
    from .fakeprocs import FakeProcs
    from .services import set_service

    p = FakeProcs()
    set_service("procs", p)
    return p


def runnable(script):
    """Make a Python script runnable as an executable: a shebang file on Linux, a .cmd wrapper on Windows."""
    import stat
    import sys
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    if sys.platform != "win32":
        return script
    wrapper = script.with_suffix(".cmd")
    wrapper.write_text('@"%s" "%s" %%*\r\n' % (sys.executable, script))
    return wrapper


def synthetic_flp(channels=(0, 1)):
    """A tiny in-memory FLP (version, two channel blocks, an empty playlist) for tests of file patchers."""
    import struct

    from .flpfile import Flp, enc16

    head = b"FLhd" + struct.pack("<I", 6) + struct.pack("<HHH", 0, len(channels), 96)
    ev = [[199, enc16("26.1.7")], [65, struct.pack("<H", 1)], [226, b"\x01" * 20]]
    for c in channels:
        ev += [[64, struct.pack("<H", c)], [21, b"\x02"], [203, enc16("Ch%d" % c)], [226, b"\x02" * 20]]
    ev += [[99, b"\x00\x00"], [233, b""]]
    return Flp(head, ev, b"")

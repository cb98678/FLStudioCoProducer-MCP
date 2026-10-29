"""Build and run one MCP server over stdio from the shared registry."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import anyio
import mcp.server.stdio
import mcp_types as types
from mcp.server.lowlevel import Server

from .. import __version__
from ..orchestrator.collab import PendingCollab
from ..orchestrator.session import Session, new_session
from ..config import load_config
from ..wiring import install_services
from .tools import SERVER_LAYERS, list_tools, route_call, to_mcp

INSTRUCTIONS = {
    "fl-bridge": "Read and write FL Studio project state with verified writes, plus the run's plan, spec, phase and ledger tools. "
                 "In a new chat call list_skills first, then read_skill co-producer-protocol and the skill for the task before any other tool.",
    "studio-audio": "Measure audio and note data. Deterministic and CPU only; writers stay inside the sandbox folder.",
    "studio-ml": "Local generative, separation, transcription and critique models. Heavy and optional.",
    "desktop-control": "Operate the FL Studio window when the API cannot. Every action checks the target window and the halt flag.",
}


def make_session(home: Path, run_id: str, server: str, ceiling: str = "A2", lint: bool = False) -> Session:
    """One session per server process. Run state is shared with other servers through the run folder."""
    run_dir = home / "runs" / run_id
    s = new_session(home / "modules", run_dir, PendingCollab(run_dir / "pending_decisions.json"), ceiling=ceiling, lint=lint)
    install_services(home, run_dir, s.ledger)
    s.registry.activate()
    return s


def attach_bridge(s: Session, out_name: str, in_name: str, max_payload: int = 200) -> str | None:
    """Connect the registry to FL over real MIDI ports. Returns a warning when it cannot, so the server still starts."""
    from ..bridge import BridgeClient
    from ..midi_transport import open_midi_transport
    opened = open_midi_transport(out_name, in_name)
    if not opened.ok:
        return opened.error.message
    BridgeClient(s.registry, opened.value, max_payload=max_payload).attach(s.registry)
    return None


def build_server(s: Session, server: str, slicing: bool) -> Server:
    lock = anyio.Lock()

    async def on_list_tools(ctx, params):
        return types.ListToolsResult(tools=list_tools(s, server, slicing))

    async def on_call_tool(ctx, params):
        async with lock:                      # one tool at a time keeps FL traffic and the ledger in order
            res = await anyio.to_thread.run_sync(lambda: route_call(s, server, slicing, params.name, params.arguments or {}))
        return to_mcp(res)

    return Server(server, version=__version__, instructions=INSTRUCTIONS[server],
                  on_list_tools=on_list_tools, on_call_tool=on_call_tool)


async def serve(server: Server) -> None:
    async with mcp.server.stdio.stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def parse_args(server: str, argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="coproducer-" + server)
    p.add_argument("--home", default=os.environ.get("COPRODUCER_HOME", "."), help="project home with modules/, runs/, sandbox/")
    p.add_argument("--run", default=os.environ.get("COPRODUCER_RUN", "default"), help="run id")
    p.add_argument("--ceiling", default=os.environ.get("COPRODUCER_CEILING", "A2"), choices=["A0", "A1", "A2"])
    p.add_argument("--no-slice", action="store_true", help="list every tool of this server, not just the phase slice")
    p.add_argument("--lint", action="store_true", help="lint all modules at start (slower)")
    p.add_argument("--midi-out", default=os.environ.get("COPRODUCER_MIDI_OUT", "coproducer-in"))
    p.add_argument("--midi-in", default=os.environ.get("COPRODUCER_MIDI_IN", "coproducer-out"))
    return p.parse_args(argv)


def main(server: str, argv: list[str] | None = None) -> None:
    assert server in SERVER_LAYERS
    a = parse_args(server, argv)
    s = make_session(Path(a.home).resolve(), a.run, server, a.ceiling, a.lint)
    if server == "fl-bridge":
        warn = attach_bridge(s, a.midi_out, a.midi_in, load_config(Path(a.home).resolve())["bridge"]["max_payload"])
        if warn:
            print("fl-bridge: FL is not connected (%s). Tools that need FL will report E_UNSUPPORTED_API." % warn, file=sys.stderr)
    anyio.run(serve, build_server(s, server, not a.no_slice))

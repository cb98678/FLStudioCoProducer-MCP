"""Turn registry modules and meta tools into MCP tool definitions and calls. No hand-written tool schemas."""
from __future__ import annotations

import json

import mcp_types as types

from ..orchestrator import meta_tools, phases
from ..orchestrator.session import Session, halted, load_state
from ..registry import Module
from ..result import Result, fail

SERVER_LAYERS = {"fl-bridge": ("L2", "L3"), "studio-audio": ("L4",), "studio-ml": ("L5",), "desktop-control": ("L6",)}


def describe(mod: Module) -> str:
    """Tool description: the one-sentence summary plus how risky and how slow the module is."""
    p = mod.manifest["policy"]
    return "%s [%s, %s, %s]" % (mod.summary, p["autonomy"], p["side_effect"], p["cost"])


def visible_modules(s: Session, server: str, slicing: bool) -> list[Module]:
    mine = [m for m in s.registry.exposed() if m.layer in SERVER_LAYERS[server]]
    if not slicing:
        return sorted(mine, key=lambda m: m.name)
    allowed = set(phases.slice_for(s))
    return sorted((m for m in mine if m.name in allowed), key=lambda m: m.name)


def list_tools(s: Session, server: str, slicing: bool) -> list[types.Tool]:
    load_state(s)
    tools = [types.Tool(name=m.name, description=describe(m), input_schema=m.input_schema)
             for m in visible_modules(s, server, slicing)]
    if server == "fl-bridge":
        tools += [types.Tool(name=n, description=d, input_schema=schema) for n, (d, schema, _) in meta_tools.META.items()]
    return tools


def route_call(s: Session, server: str, slicing: bool, name: str, args: dict) -> Result:
    """Run one tool call: refuse when halted or outside the slice, else run the module or meta tool."""
    load_state(s)
    if name in meta_tools.META:
        return meta_tools.call_meta(s, name, args) if server == "fl-bridge" else fail("E_NOT_FOUND", "meta tools live on fl-bridge")
    if halted(s):
        return fail("E_HALTED", "the run was halted")
    mod = s.registry.modules.get(name)
    if mod is None or mod.layer not in SERVER_LAYERS[server] or not mod.expose:
        return fail("E_NOT_FOUND", "no tool named %r on %s" % (name, server), nearest=s.registry.nearest(name))
    if slicing and name not in phases.slice_for(s):
        return fail("E_NOT_FOUND", "%s is not in the %s tool slice; call request_tool first" % (name, s.phase), phase=s.phase)
    return s.registry.call(name, **args)


def to_mcp(res: Result) -> types.CallToolResult:
    body = res.to_dict()
    return types.CallToolResult(content=[types.TextContent(type="text", text=json.dumps(body, default=str))],
                                structured_content=json.loads(json.dumps(body, default=str)), is_error=not res.ok)

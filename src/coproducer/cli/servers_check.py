"""coproducer check-servers: start each coproducer server the way Claude Desktop will (the command, arguments and environment in its config)
and list the tools it serves. A server that does not answer is reported with its error, so a broken install shows here, not in a chat."""
from __future__ import annotations

import json
import os
from pathlib import Path

from . import desktop_cmd


async def _one(entry: dict) -> dict:
    from mcp.client import Client
    from mcp.client.stdio import StdioServerParameters
    params = StdioServerParameters(command=entry["command"], args=entry["args"], env={**os.environ, **entry.get("env", {})})
    async with Client(params) as c:
        tools = sorted(t.name for t in (await c.list_tools()).tools)
        skills = None
        if "list_skills" in tools:
            r = await c.call_tool("list_skills", {})
            skills = len(json.loads(r.content[0].text)["value"]["skills"])
        return {"tools": len(tools), "skills": skills, "sample": tools[:5]}


def check(config: Path | None = None) -> list[dict]:
    import anyio
    cfg = config or desktop_cmd.config_path()
    try:
        servers = desktop_cmd.load_config_file(cfg).get("mcpServers", {})
    except ValueError as e:
        return [{"name": str(cfg), "ok": False, "error": str(e)}]
    rows = []
    for name, entry in servers.items():
        if not name.startswith(desktop_cmd.PREFIX):
            continue
        try:
            got = anyio.run(_one, entry)
            # Claude Desktop marks a server that lists no tools as failed ("Offered no tools"), so this does too.
            rows.append({"name": name, "ok": got["tools"] > 0, **got, **({} if got["tools"] else {"error": "started but lists no tools"})})
        except Exception as e:  # noqa: BLE001 - every failure is reported, none stops the others
            rows.append({"name": name, "ok": False, "error": "%s: %s" % (type(e).__name__, e)})
    return rows


def render(rows: list[dict], cfg: Path) -> str:
    lines = ["Claude Desktop config: %s" % cfg]
    if not rows:
        lines.append("  no coproducer servers registered: run  coproducer install-desktop")
    for r in rows:
        if r["ok"]:
            lines.append("  PASS  %-26s %d tools%s" % (r["name"], r["tools"], ", %d skills" % r["skills"] if r.get("skills") is not None else ""))
        else:
            lines.append("  FAIL  %-26s %s" % (r["name"], r["error"][:200]))
    return "\n".join(lines)

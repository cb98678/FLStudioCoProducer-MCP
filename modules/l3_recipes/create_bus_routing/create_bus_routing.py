from __future__ import annotations

from coproducer import call, flpfile, mixroute
from coproducer.result import Result, fail, ok
from coproducer.services import get_service

KINDS = {"music": mixroute.MUSIC_ROLES, "drums": mixroute.DRUM_ROLES}


def create_bus_routing(project: str, out_project: str, name: str, kind: str = "music", parts: list | None = None, bus: int = -1) -> Result:
    """Make a bus on a free mixer insert and route parts into it, in a sandbox copy, as the Future House reference does: kind "music" (chops,
    vocal, stabs, arp, reese and mid bass; not the sub or FX) or "drums", or `parts`: roles (names) or insert numbers. A part that already feeds a family bus
    has that bus routed instead. The bus is named and coloured the house way. Errors: E_SANDBOX_VIOLATION, E_ARG (no free insert, unknown kind), E_IO."""
    chk = call("check_sandbox_path", path=out_project, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    try:
        f = flpfile.Flp.load(project)
        if parts:
            ids = [p for p in parts if isinstance(p, int)]
            sources = ids + mixroute.inserts_for_roles(f, tuple(p for p in parts if isinstance(p, str)))
        elif kind in KINDS:
            sources = mixroute.inserts_for_roles(f, KINDS[kind])
        else:
            return fail("E_ARG", "kind must be music or drums, or give roles or inserts")
        rep = mixroute.build_bus(f, name, sources, None if bus < 0 else bus)
        f.save(out_project)
        g = flpfile.Flp.load(out_project)
        back = all(mixroute.routes(g, s) == [rep["bus"]] for s in rep["routed"]) and mixroute.routes(g, rep["bus"]) == [0]
    except flpfile.FlpError as e:
        return fail("E_ARG", str(e))
    except OSError as e:
        return fail("E_IO", str(e))
    return ok(dict(rep, out_project=out_project), verified=back)

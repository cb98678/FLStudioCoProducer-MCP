from __future__ import annotations

from coproducer import call, flpfile, flporg, fxchains, fxlib, mixroute
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def _plan(f: flpfile.Flp, chains: list | None) -> list[dict]:
    if chains:
        return [{"insert": int(c["insert"]), "chain": c["chain"]} for c in chains]
    known = fxchains.load()["chains"]
    out = [{"insert": t, "chain": r} for r in known for t in mixroute.inserts_for_roles(f, (r,))]
    for t in range(1, mixroute.insert_count(f)):
        key = (flporg.insert_name(f, t) or "").strip().lower().replace(" ", "_")
        if key in known:
            out.append({"insert": t, "chain": key})  # a bus named after its chain, such as Music Bus
    return sorted(out, key=lambda x: x["insert"])


def apply_fx_chain(project: str, out_project: str, chains: list | None = None) -> Result:
    """Put whole effect chains from the reference (plugins/chains.json) into part inserts in one step, in a sandbox copy of an FL-saved project:
    chains [{"insert", "chain": role or bus name}], or by default every part insert by its role (chops, vocal, kick, clap, hats, perc, stab,
    bass, reese, sub, arp, synth, fx) and a bus named Music Bus. Effects go after what an insert already holds; an insert without room is
    listed and left alone. Rebalance levels after (gain-staging). Errors: E_SANDBOX_VIOLATION, E_ARG, E_IO."""
    chk = call("check_sandbox_path", path=out_project, sandbox_root=str(get_service("sandbox_root")))
    if not chk.ok:
        return chk
    try:
        f = flpfile.Flp.load(project)
        done, left = [], []
        for item in _plan(f, chains):
            try:
                done.append(fxchains.apply_chain(f, item["insert"], item["chain"], tuple(get_service("fl_not_owned") or ())))
            except flpfile.FlpError as e:
                left.append({"insert": item["insert"], "chain": item["chain"], "why": str(e)})
        if not done:
            return fail("E_ARG", "no chain went in: %s" % (left or "no part insert has a known role"))
        f.save(out_project)
        g = flpfile.Flp.load(out_project)
        back = all(fxlib.slot_plugin(g, d["insert"], p["slot"]) == p["plugin"] for d in done for p in d["placed"])
    except (flpfile.FlpError, KeyError) as e:
        return fail("E_ARG", str(e))
    except OSError as e:
        return fail("E_IO", str(e))
    return ok({"out_project": out_project, "applied": done, "left": left}, verified=back)

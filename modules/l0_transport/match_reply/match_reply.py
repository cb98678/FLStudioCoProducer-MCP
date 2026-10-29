from __future__ import annotations

from coproducer.result import Result, fail, ok


def match_reply(parsed: list[dict], req_id: int) -> Result:
    """Collect the parsed frames for one request id and report whether the group is complete.

    When complete, value holds the message type and the joined payload in sequence order.
    Errors: E_ARG when frames of one request disagree on the total.
    """
    mine = [p for p in parsed if p.get("req_id") == req_id]
    if not mine:
        return ok({"complete": False, "have": 0, "total": 0})
    total = mine[0]["total"]
    if any(p["total"] != total for p in mine):
        return fail("E_ARG", "frames of one request disagree on total")
    by_seq = {}
    for p in mine:
        by_seq.setdefault(p["seq"], p)
    if len(by_seq) < total:
        return ok({"complete": False, "have": len(by_seq), "total": total})
    payload = [b for s in range(total) for b in by_seq[s]["payload"]]
    return ok({"complete": True, "have": total, "total": total, "type": mine[0]["type"], "payload": payload})

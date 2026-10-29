from __future__ import annotations

from pathlib import Path

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service

REF_WINDOWS = [[30.0, 40.0], [60.0, 70.0], [90.0, 100.0], [120.0, 130.0]]  # four 10 s windows across a reference


def _dot(a: list, b: list) -> float:
    return sum(x * y for x, y in zip(a, b))


def compare_to_references_ml(path: str, references: list, windows: list | None = None, baseline: str = "") -> Result:
    """Cosine similarity of 10 s windows of a remix (windows [[start_s, end_s]], default four across it) to windows of each reference track, with
    MuQ-MuLan (the embedding a 2026 study found closest to perceived similarity; weights CC-BY-NC 4.0, run in the mir environment). Each window's
    score is its best match over the references. With baseline (the original song), the same is measured for it, so "sounds more like the
    references than the original did" is a number. A judge for the evaluation panel, not a target. Errors: E_NOT_FOUND, E_MODEL.
    """
    for p in [path, *references] + ([baseline] if baseline else []):
        if not Path(p).is_file():
            return fail("E_NOT_FOUND", "no audio file at %s" % Path(p).name)
    snaps = (get_service("model_files") or {}).get("mulan_snapshots", {})

    def embed(p: str, wins: list) -> Result:
        return call("run_model_op", model="mir", op="embed", timeout_s=1800, args={"path": p, "segments": wins, "snapshots": snaps})
    mine = embed(path, windows or REF_WINDOWS)
    if not mine.ok:
        return mine
    refs = []
    for r in references:
        got = embed(r, REF_WINDOWS)
        if not got.ok:
            return got
        refs += got.value["embeddings"]
    score = [round(max(_dot(e, f) for f in refs), 4) for e in mine.value["embeddings"]]
    out = {"windows": windows or REF_WINDOWS, "scores": score, "mean": round(sum(score) / len(score), 4), "references": len(references)}
    if baseline:
        base = embed(baseline, windows or REF_WINDOWS)
        if not base.ok:
            return base
        b = [round(max(_dot(e, f) for f in refs), 4) for e in base.value["embeddings"]]
        out.update(baseline_scores=b, baseline_mean=round(sum(b) / len(b), 4), closer_than_baseline=out["mean"] > sum(b) / len(b))
    return ok(out, verified=True)

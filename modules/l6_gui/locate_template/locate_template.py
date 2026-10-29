from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image
from scipy.signal import fftconvolve

from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def _gray(path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("L"), dtype=np.float64)


def _ncc(img: np.ndarray, tpl: np.ndarray) -> np.ndarray:
    """Normalised cross-correlation of tpl over img (valid positions only), values in -1..1."""
    n = tpl.size
    t = tpl - tpl.mean()
    ones = np.ones_like(tpl)
    num = fftconvolve(img, t[::-1, ::-1], mode="valid")
    s1 = fftconvolve(img, ones, mode="valid")
    s2 = fftconvolve(img * img, ones, mode="valid")
    var = np.maximum(s2 - s1 * s1 / n, 0.0)
    out = np.zeros_like(num)
    ok_ = var > 1e-3 * n
    out[ok_] = num[ok_] / (np.sqrt(var[ok_]) * np.sqrt((t * t).sum()))
    return out


def locate_template(image_path: str, template_name: str, min_score: float = 0.9) -> Result:
    """Find a stored interface picture (a template) in a screenshot and return the centre {x, y, score} in image pixels.

    Matching is pixel exact up to brightness, so it works for fixed text such as menu entries. Never clicks.
    Errors: E_NOT_FOUND (image or template), E_GUI_MISMATCH when the best score is under min_score or a second place matches as well.
    """
    folder = get_service("templates_dir")
    tpl_path = Path(folder) / (template_name + ".png") if folder else None
    if tpl_path is None or not tpl_path.is_file() or not Path(image_path).is_file():
        return fail("E_NOT_FOUND", "missing image or template %r" % template_name)
    img, tpl = _gray(image_path), _gray(tpl_path)
    if img.shape[0] < tpl.shape[0] or img.shape[1] < tpl.shape[1]:
        return fail("E_ARG", "the template is larger than the image")
    score = _ncc(img, tpl)
    r, c = np.unravel_index(int(np.argmax(score)), score.shape)
    best = float(score[r, c])
    if best < min_score:
        return fail("E_GUI_MISMATCH", "template %r not found; best match %.2f is under %.2f" % (template_name, best, min_score), best=round(best, 3))
    rest = score.copy()
    h, w = tpl.shape
    rest[max(0, r - h):r + h + 1, max(0, c - w):c + w + 1] = -1.0
    second = float(rest.max())
    if second >= min_score and second > best - 0.03:
        return fail("E_GUI_MISMATCH", "template %r matches in more than one place (%.2f and %.2f)" % (template_name, best, second))
    return ok({"x": int(c + w // 2), "y": int(r + h // 2), "score": round(best, 3)})

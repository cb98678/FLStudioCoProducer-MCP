from __future__ import annotations

from coproducer import call
from coproducer.result import Result, first_error, ok


def build_measure_report(path: str) -> Result:
    """Run the standard measures on one audio file and assemble a single report.

    Covers peaks, loudness, spectrum, stereo image, clipping, silence and DC offset. Stereo-only measures are skipped for mono.
    Loudness range needs 3 seconds of audio; for shorter audio it is left out and named in "skipped".
    """
    parts = {
        "sample_peak": call("measure_sample_peak", path=path), "true_peak": call("measure_true_peak", path=path),
        "rms": call("measure_rms", path=path), "crest": call("measure_crest_factor", path=path),
        "loudness": call("measure_integrated_loudness", path=path), "range": call("measure_loudness_range", path=path),
        "bands": call("measure_band_energy", path=path), "centroid": call("measure_spectral_centroid", path=path),
        "clipping": call("count_clipped_samples", path=path), "silence": call("detect_silence", path=path),
        "dc": call("measure_dc_offset", path=path),
    }
    skipped = {}
    if not parts["range"].ok and parts["range"].error.code == "E_ARG":
        skipped["range"] = parts.pop("range").error.message
    bad = first_error(*parts.values())
    if bad:
        return bad
    stereo = {"correlation": call("measure_stereo_correlation", path=path), "mid_side": call("measure_mid_side_ratio", path=path),
              "low_end_mono": call("measure_low_end_mono_ratio", path=path)}
    report = {k: v.value for k, v in parts.items()}
    report.update({k: v.value for k, v in stereo.items() if v.ok})
    if skipped:
        report["skipped"] = skipped
    return ok(report)

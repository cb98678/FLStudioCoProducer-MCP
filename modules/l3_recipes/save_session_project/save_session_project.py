from __future__ import annotations

from coproducer import call, flpfile, sessionflp
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def save_session_project(bench_path: str, out_path: str, bpm: float, clips: list) -> Result:
    """Save an FL project that holds audio files on the song's clock, to be opened later and adjusted by hand (a Newtime or Newtone session, a vocal's chunks, stems).

    The bench (a project with an audio clip on playlist row 1) is copied without its other channels, set to bpm, with one clip per entry of
    clips {file, name, start_s, row, length_s}; the first sits where Newtime and Newtone open from. Files are referenced, so the .zpw and
    .zpa analysis files beside them are read when the editor opens. Errors: E_SANDBOX_VIOLATION, E_IO, E_ARG.
    """
    root = str(get_service("sandbox_root"))
    for p in [bench_path, out_path]:
        chk = call("check_sandbox_path", path=p, sandbox_root=root)
        if not chk.ok:
            return chk
    if not clips or not all(isinstance(c, dict) and c.get("file") for c in clips):
        return fail("E_ARG", "clips must be a list of {file, name, start_s, row}")
    for c in clips:
        chk = call("check_sandbox_path", path=c["file"], sandbox_root=root)
        if not chk.ok:
            return chk
    try:
        done = sessionflp.write_project(bench_path, out_path, float(bpm), clips)
        back = flpfile.Flp.load(out_path)
    except (OSError, ValueError, flpfile.FlpError) as e:
        return fail("E_IO", str(e))
    return ok({**done, "audio_clips": len(back.audio_clips(True)), "tempo": back.tempo()}, verified=len(back.audio_clips(True)) == len(clips))

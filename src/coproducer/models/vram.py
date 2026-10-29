"""Ask the GPU how much memory is free. Returns None when there is no NVIDIA GPU or the tool is missing."""
from __future__ import annotations

import subprocess


def parse_nvidia_smi(text: str) -> tuple[int, int] | None:
    """Parse 'free, total' lines (MiB, no units) from nvidia-smi and return the first GPU as (free_mb, total_mb)."""
    for line in text.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 2 and all(p.isdigit() for p in parts):
            return int(parts[0]), int(parts[1])
    return None


def query_vram() -> tuple[int, int] | None:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.free,memory.total", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=10, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return parse_nvidia_smi(out)

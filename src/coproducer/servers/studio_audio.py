"""Entry point: python -m coproducer.servers.studio_audio (or the coproducer-studio-audio command)."""
from .common import main


def run() -> None:
    main("studio-audio")


if __name__ == "__main__":
    run()

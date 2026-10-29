"""Entry point: python -m coproducer.servers.desktop_control (or the coproducer-desktop-control command)."""
from .common import main


def run() -> None:
    main("desktop-control")


if __name__ == "__main__":
    run()

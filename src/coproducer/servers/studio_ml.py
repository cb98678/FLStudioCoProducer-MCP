"""Entry point: python -m coproducer.servers.studio_ml (or the coproducer-studio-ml command)."""
from .common import main


def run() -> None:
    main("studio-ml")


if __name__ == "__main__":
    run()

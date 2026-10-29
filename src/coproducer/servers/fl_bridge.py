"""Entry point: python -m coproducer.servers.fl_bridge (or the coproducer-fl-bridge command)."""
from .common import main


def run() -> None:
    main("fl-bridge")


if __name__ == "__main__":
    run()

"""Entry point: python main.py"""
import os

from oes.cli import CLI
from oes.seed import seed_sample_data
from oes.storage import JsonStore

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "oes_data.json")


def main() -> None:
    store = JsonStore(DATA_FILE)
    seed_sample_data(store)
    CLI(store).run()


if __name__ == "__main__":
    main()

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.cli.app import AgentApp


def main():
    config_path = None
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    app = AgentApp(config_path)
    app.run()


if __name__ == "__main__":
    main()

"""LinkedIn Post Scraper — Entry Point"""

import sys
import os
import logging

# Ensure src is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import load_config, save_config
from src.ui.app import App


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    setup_logging()
    config = load_config()
    save_config(config)  # Ensure config file exists with defaults

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()

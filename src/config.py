"""Configuration management for LinkedIn Post Scraper."""

import json
import os

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "output_folder": "output",
    "browser_state_dir": "browser_state",
    "max_posts": 50,
}


def get_app_dir():
    """Get the application root directory."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_config_path():
    """Get the full path to the config file."""
    return os.path.join(get_app_dir(), CONFIG_FILE)


def load_config() -> dict:
    """Load configuration from JSON file, creating defaults if needed."""
    config_path = get_config_path()
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            stored = json.load(f)
            # Merge with defaults to ensure new keys are present
            merged = {**DEFAULT_CONFIG, **stored}
            return merged
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    """Save configuration to JSON file."""
    config_path = get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def get_output_folder(config: dict) -> str:
    """Get the absolute path to the output folder."""
    folder = config.get("output_folder", DEFAULT_CONFIG["output_folder"])
    if not os.path.isabs(folder):
        folder = os.path.join(get_app_dir(), folder)
    os.makedirs(folder, exist_ok=True)
    return folder


def get_browser_state_dir(config: dict) -> str:
    """Get the absolute path to the browser state directory."""
    state_dir = config.get("browser_state_dir", DEFAULT_CONFIG["browser_state_dir"])
    if not os.path.isabs(state_dir):
        state_dir = os.path.join(get_app_dir(), state_dir)
    return state_dir

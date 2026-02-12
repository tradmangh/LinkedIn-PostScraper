"""Configuration management for LinkedIn Post Scraper."""

import json
import os

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "output_folder": os.path.join("~", "LinkedIn-Posts"),
    "browser_state_dir": "browser_state",
    "max_posts": 50,
    "appearance_mode": "system",  # "system", "light", or "dark"
}


def get_app_dir():
    """Get the application root directory."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_user_data_dir():
    """Get the user data directory."""
    path = os.path.expanduser("~/.LinkedIn-Scraper")
    # Ensure directory exists when requested, effectively creating it if needed
    # However, for pure getters, we might just return path. 
    # But usually we want to ensure it exists before writing.
    # We'll rely on save_config to create it, or load_config to just check existence.
    return path


def get_config_path():
    """Get the full path to the config file."""
    # Use config in user data dir
    return os.path.join(get_user_data_dir(), CONFIG_FILE)


def load_config() -> dict:
    """Load configuration from JSON file, creating defaults if needed."""
    config_path = get_config_path()
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            stored = json.load(f)
            # Merge with defaults to ensure new keys are present
            merged = {**DEFAULT_CONFIG, **stored}
            
            # Migration: if output_folder is the old default "output", update it to the new default
            needs_save = False
            if merged.get("output_folder") == "output":
                merged["output_folder"] = DEFAULT_CONFIG["output_folder"]
                needs_save = True
            
            # Auto-save migrated config
            if needs_save:
                save_config(merged)
                
            return merged
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    """Save configuration to JSON file."""
    # Ensure user data directory exists
    user_data_dir = get_user_data_dir()
    os.makedirs(user_data_dir, exist_ok=True)
    
    config_path = get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def get_output_folder(config: dict) -> str:
    """Get the absolute path to the output folder."""
    folder = config.get("output_folder", DEFAULT_CONFIG["output_folder"])
    
    # Expand user tilde (~) if present
    folder = os.path.expanduser(folder)
    
    if not os.path.isabs(folder):
        folder = os.path.join(get_app_dir(), folder)
    
    # Normalize path separators for the current OS
    folder = os.path.normpath(folder)
    
    # NOTE: We do NOT create the folder here anymore. 
    # It is created only when saving posts to allow user to change it beforehand.
    return folder


def get_browser_state_dir(config: dict) -> str:
    """Get the absolute path to the browser state directory."""
    state_dir = config.get("browser_state_dir", DEFAULT_CONFIG["browser_state_dir"])
    if not os.path.isabs(state_dir):
        state_dir = os.path.join(get_app_dir(), state_dir)
    return state_dir


def get_appearance_mode(config: dict) -> str:
    """Get the appearance mode setting.
    
    Returns:
        One of "system", "light", or "dark"
    """
    return config.get("appearance_mode", DEFAULT_CONFIG["appearance_mode"])

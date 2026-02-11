"""Main application window for LinkedIn Post Scraper."""

import customtkinter as ctk

from .scrape_frame import ScrapeFrame
from .browse_frame import BrowseFrame
from ..config import load_config, save_config


class App(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.title("LinkedIn Post Scraper")
        self.geometry("960x680")
        self.minsize(800, 550)

        # Set appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Load config
        self.config_data = load_config()

        # Configure grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 0))
        header.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header,
            text="LinkedIn Post Scraper",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title_label.grid(row=0, column=0, sticky="w")

        version_label = ctk.CTkLabel(
            header,
            text="v1.0",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        version_label.grid(row=0, column=1, sticky="e")

        # Tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=16, pady=16)

        # Create tabs
        self.scrape_tab = self.tabview.add("  Scrape  ")
        self.browse_tab = self.tabview.add("  Browse  ")

        # Configure tab grids
        self.scrape_tab.grid_rowconfigure(0, weight=1)
        self.scrape_tab.grid_columnconfigure(0, weight=1)
        self.browse_tab.grid_rowconfigure(0, weight=1)
        self.browse_tab.grid_columnconfigure(0, weight=1)

        # Populate tabs
        self.scrape_frame = ScrapeFrame(self.scrape_tab, self.config_data)
        self.scrape_frame.grid(row=0, column=0, sticky="nsew")

        self.browse_frame = BrowseFrame(self.browse_tab, self.config_data)
        self.browse_frame.grid(row=0, column=0, sticky="nsew")

        # Save config on close
        self.protocol("WM_DELETE_CLOSE", self._on_close)

    def _on_close(self):
        save_config(self.config_data)
        self.destroy()

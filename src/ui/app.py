"""Main application window for LinkedIn Post Scraper."""

import customtkinter as ctk

from .scrape_frame import ScrapeFrame
from .browse_frame import BrowseFrame
from .settings_dialog import SettingsDialog
from ..config import load_config, save_config, get_appearance_mode


class App(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.title("LinkedIn Post Scraper")
        
        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Calculate left half dimensions
        window_width = screen_width // 2
        # Subtract taskbar height (typically 40-48px on Windows)
        window_height = screen_height - 40
        
        # Position at left side (x=0, y=0)
        self.geometry(f"{window_width}x{window_height}+0+0")
        self.minsize(800, 550)

        # Load config
        self.config_data = load_config()

        # Set appearance mode from config
        appearance_mode = get_appearance_mode(self.config_data)
        if appearance_mode == "system":
            ctk.set_appearance_mode("system")
        else:
            ctk.set_appearance_mode(appearance_mode)
        
        ctk.set_default_color_theme("blue")

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

        # Header buttons frame
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")

        settings_btn = ctk.CTkButton(
            btn_frame,
            text="⚙️ Settings",
            width=100,
            height=28,
            command=self._show_settings,
        )
        settings_btn.grid(row=0, column=0, padx=(0, 8))

        about_btn = ctk.CTkButton(
            btn_frame,
            text="ℹ️ About",
            width=80,
            height=28,
            command=self._show_about,
        )
        about_btn.grid(row=0, column=1)

        # Tabview
        self.tabview = ctk.CTkTabview(self, command=self._on_tab_change)
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

        # Global bindings
        self.bind_all("<Button-1>", self._on_global_click)
        self.bind("<Control-f>", self._on_ctrl_f)

    def _on_close(self):
        save_config(self.config_data)
        self.destroy()

    def _on_ctrl_f(self, event=None):
        """Shortcut handler: Focus filter in active tab."""
        current_tab = self.tabview.get().strip()
        
        if current_tab == "Scrape":
            self.scrape_frame.focus_filter_entry()
        elif current_tab == "Browse":
            self.browse_frame.focus_filter_entry()

    def _on_tab_change(self):
        """Handle tab changes."""
        current_tab = self.tabview.get().strip()
        if current_tab == "Browse":
            # Auto-refresh files when switching to Browse tab
            self.browse_frame.refresh_files()

    def _on_global_click(self, event):
        """Global click handler to unfocus entries when clicking outside."""
        # obtaining the widget that was clicked
        widget = event.widget
        
        # If the widget is not an entry/text widget, we want to clear focus
        # This allows clicking on background/labels to unfocus the search bar
        if isinstance(widget, str):
            # If widget is a string identifier (rare but possible in tk), ignore it or just return
            return

        if not isinstance(widget, (ctk.CTkEntry, ctk.CTkTextbox)):
            # Helper to check widget type properly for both tk and ctk
            try:
                w_class = widget.winfo_class().lower()
            except AttributeError:
                return
            
            # formatting: entry, text, etc. are input classes
            if "entry" not in w_class and "text" not in w_class:
                self.focus()

    def _show_settings(self):
        """Show Settings dialog."""
        SettingsDialog(self, self.config_data)

    def _show_about(self):
        """Show About dialog."""
        from tkinter import messagebox
        messagebox.showinfo(
            "About LinkedIn Post Scraper",
            "LinkedIn Post Scraper v1.3.0\n\n"
            "A tool for archiving LinkedIn posts as markdown files.\n\n"
            "Co-created by:\n"
            "• Google Antigravity (AI Agent)\n"
            "• Anthropic Claude Opus 4.6 & Sonnet 4.5\n"
            "• Google Gemini 3.0\n\n"
            "Licensed under MIT License\n\n"
            "https://github.com/tradmangh/LinkedIn-PostScraper"
        )

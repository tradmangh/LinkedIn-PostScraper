"""Settings dialog for LinkedIn Post Scraper."""

import customtkinter as ctk
from ..config import save_config


class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog window."""

    def __init__(self, parent, config: dict):
        super().__init__(parent)
        
        self.config = config
        self.title("Settings")
        self.geometry("400x250")
        self.resizable(False, False)
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Center the dialog
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 400) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 250) // 2
        self.geometry(f"+{x}+{y}")
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="⚙️ Settings",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Appearance section
        appearance_frame = ctk.CTkFrame(self, fg_color="transparent")
        appearance_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        appearance_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            appearance_frame,
            text="Theme:",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))
        
        # Theme selection
        current_mode = config.get("appearance_mode", "system")
        self.theme_var = ctk.StringVar(value=current_mode)
        
        theme_options = ["system", "light", "dark"]
        theme_labels = {
            "system": "🔄 Auto (Follow OS)",
            "light": "☀️ Light",
            "dark": "🌙 Dark"
        }
        
        for i, mode in enumerate(theme_options):
            radio = ctk.CTkRadioButton(
                appearance_frame,
                text=theme_labels[mode],
                variable=self.theme_var,
                value=mode,
                font=ctk.CTkFont(size=13),
                command=self._on_theme_change,
            )
            radio.grid(row=i+1, column=0, sticky="w", pady=4, padx=(20, 0))
        
        # Info label
        info_label = ctk.CTkLabel(
            self,
            text="Theme changes are applied immediately and saved automatically.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            wraplength=360,
        )
        info_label.grid(row=2, column=0, padx=20, pady=(10, 10))
        
        # Close button
        close_btn = ctk.CTkButton(
            self,
            text="Close",
            width=100,
            command=self.destroy,
        )
        close_btn.grid(row=3, column=0, pady=(0, 20))
    
    def _on_theme_change(self):
        """Handle theme selection change."""
        new_mode = self.theme_var.get()
        
        # Update config
        self.config["appearance_mode"] = new_mode
        save_config(self.config)
        
        # Close dialog first, then apply theme to avoid UI freeze
        # We need to release grab_set() before changing appearance mode
        self.grab_release()
        self.withdraw()  # Hide the dialog
        
        # Schedule theme application after dialog is fully closed
        self.after(100, lambda: self._apply_theme(new_mode))
        self.after(200, self.destroy)  # Destroy dialog after theme is applied
    
    def _apply_theme(self, mode: str):
        """Apply the theme change."""
        if mode == "system":
            ctk.set_appearance_mode("system")
        else:
            ctk.set_appearance_mode(mode)

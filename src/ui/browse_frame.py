"""Browse tab — view saved markdown posts."""

import os
import subprocess
import customtkinter as ctk

from ..config import get_output_folder


class BrowseFrame(ctk.CTkFrame):
    """Frame for browsing saved posts."""

    def __init__(self, parent, config: dict):
        super().__init__(parent, fg_color="transparent")
        self.config = config
        self.all_files = []  # Cache for filtering

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)

        # --- Top bar ---
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        top_frame.grid_columnconfigure(0, weight=1)

        self.refresh_btn = ctk.CTkButton(
            top_frame,
            text="🔄 Refresh",
            width=100,
            height=32,
            command=self._refresh_list,
        )
        self.refresh_btn.grid(row=0, column=0, sticky="w")

        self.open_folder_btn = ctk.CTkButton(
            top_frame,
            text="📂 Open Folder",
            width=120,
            height=32,
            command=self._open_folder,
        )
        self.open_folder_btn.grid(row=0, column=1, padx=(8, 0))

        self.open_folder_btn.grid(row=0, column=1, padx=(8, 0))

        # --- File list header ---
        saved_header_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), corner_radius=6)
        saved_header_frame.grid(row=1, column=0, sticky="ew", pady=(4, 4), padx=(0, 8))
        saved_header_frame.grid_columnconfigure(2, weight=1)
        
        saved_header = ctk.CTkLabel(
            saved_header_frame,
            text="💾 Saved Posts",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        )
        saved_header.grid(row=0, column=0, sticky="w", padx=(12, 4), pady=8)

        self.file_count_label = ctk.CTkLabel(
            saved_header_frame,
            text="(0)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="gray",
            anchor="w"
        )
        self.file_count_label.grid(row=0, column=1, sticky="w", padx=(0, 12), pady=8)

        # Filter input
        self.file_filter_entry = ctk.CTkEntry(
            saved_header_frame,
            placeholder_text="🔍 Filter files...",
            width=150,
            height=28,
        )
        self.file_filter_entry.grid(row=0, column=3, sticky="e", padx=12, pady=8)
        self.file_filter_entry.bind("<KeyRelease>", self._on_filter_change)

        # --- File list (left panel) ---
        self.file_list = ctk.CTkScrollableFrame(
            self,
            width=280,
        )
        self.file_list.grid(row=2, column=0, sticky="nsew", padx=(0, 8))
        self.file_list.grid_columnconfigure(0, weight=1)

        self.file_buttons: list[ctk.CTkButton] = []
        self._selected_file: str = ""

        # --- Preview panel (right panel) ---
        self.preview_frame = ctk.CTkFrame(self)
        self.preview_frame.grid(row=2, column=1, sticky="nsew")
        self.preview_frame.grid_rowconfigure(1, weight=1)
        self.preview_frame.grid_columnconfigure(0, weight=1)

        self.preview_title = ctk.CTkLabel(
            self.preview_frame,
            text="Select a post to preview",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        self.preview_title.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))

        self.preview_text = ctk.CTkTextbox(
            self.preview_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
            state="disabled",
        )
        self.preview_text.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        # Initial load
        self.after(500, self._refresh_list)

    def refresh_files(self):
        """Public method to refresh the file list."""
        self._refresh_list()

    def _refresh_list(self):
        """Reload the file list from the output folder and update UI."""
        output_folder = get_output_folder(self.config)
        self.all_files = []

        if os.path.isdir(output_folder):
            for root, dirs, files in os.walk(output_folder):
                for f in sorted(files):
                    if f.endswith(".md"):
                        full_path = os.path.join(root, f)
                        # Show relative path from output folder
                        rel_path = os.path.relpath(full_path, output_folder)
                        self.all_files.append((rel_path, full_path))
        
        self._update_list_ui()

    def _update_list_ui(self):
        """Update the file list UI based on filter."""
        # Clear existing buttons
        for btn in self.file_buttons:
            btn.destroy()
        self.file_buttons.clear()
        
        # Toggle filter visibility
        if len(self.all_files) >= 3:
            self.file_filter_entry.grid()
        else:
            self.file_filter_entry.grid_remove()
        
        filter_text = self.file_filter_entry.get().lower()
        visible_files = []
        
        for rel_path, full_path in self.all_files:
            if filter_text and filter_text not in rel_path.lower():
                continue
            visible_files.append((rel_path, full_path))

        count_text = f"({len(visible_files)})"
        if len(visible_files) != len(self.all_files):
            count_text = f"({len(visible_files)}/{len(self.all_files)})"
        self.file_count_label.configure(text=count_text)

        if not visible_files:
            placeholder = ctk.CTkLabel(
                self.file_list,
                text="No files found." if self.all_files else "No saved posts found.\nScrape some posts first!",
                text_color="gray",
            )
            placeholder.grid(row=0, column=0, pady=20)
            # Add to list so it gets destroyed on next refresh
            self.file_buttons.append(placeholder)
        else:
            for i, (rel_path, full_path) in enumerate(visible_files):
                btn = ctk.CTkButton(
                    self.file_list,
                    text=rel_path,
                    font=ctk.CTkFont(size=11),
                    anchor="w",
                    height=28,
                    fg_color="transparent",
                    text_color=("gray10", "gray90"),
                    hover_color=("gray80", "gray30"),
                    command=lambda p=full_path, r=rel_path: self._preview_file(p, r),
                )
                btn.grid(row=i, column=0, sticky="ew", padx=2, pady=1)
                self.file_buttons.append(btn)

    def _on_filter_change(self, event=None):
        """Handle filter text change."""
        self._update_list_ui()

    def _preview_file(self, filepath: str, display_name: str):
        """Show a markdown file's contents in the preview panel."""
        self._selected_file = filepath
        self.preview_title.configure(text=display_name)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            content = f"Error reading file: {e}"

        self.preview_text.configure(state="normal")
        self.preview_text.delete("0.0", "end")
        self.preview_text.insert("0.0", content)
        self.preview_text.configure(state="disabled")

    def _open_folder(self):
        """Open the output folder in Windows Explorer."""
        output_folder = get_output_folder(self.config)
        if os.path.isdir(output_folder):
            subprocess.Popen(["explorer", output_folder])

    def focus_filter_entry(self):
        """Set focus to the file filter entry widget."""
        self.file_filter_entry.focus_set()

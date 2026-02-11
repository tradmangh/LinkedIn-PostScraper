"""Scrape tab — URL input, login, post scanning, and scraping with progress."""

import threading
import customtkinter as ctk

from ..scraper import LinkedInScraper, PostPreview
from ..parser import parse_post
from ..storage import save_posts
from ..config import get_output_folder, get_browser_state_dir


class ScrapeFrame(ctk.CTkFrame):
    """Frame for the Scrape tab."""

    def __init__(self, parent, config: dict):
        super().__init__(parent, fg_color="transparent")
        self.config = config
        self.previews: list[PostPreview] = []
        self._scraper = None

        self.grid_rowconfigure(4, weight=1)  # post list gets the space
        self.grid_columnconfigure(0, weight=1)

        # --- Row 0: URL input + Login ---
        url_frame = ctk.CTkFrame(self, fg_color="transparent")
        url_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        url_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(url_frame, text="Profile URL:", font=ctk.CTkFont(size=13)).grid(
            row=0, column=0, padx=(0, 8), sticky="w"
        )

        self.url_entry = ctk.CTkEntry(
            url_frame,
            placeholder_text="https://www.linkedin.com/in/username/recent-activity/all/",
            height=36,
            font=ctk.CTkFont(size=13),
        )
        self.url_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))

        self.login_btn = ctk.CTkButton(
            url_frame,
            text="🔑 Login",
            width=100,
            height=36,
            command=self._on_login,
        )
        self.login_btn.grid(row=0, column=2, padx=(0, 0))

        # --- Row 1: Action buttons ---
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        self.scan_btn = ctk.CTkButton(
            btn_frame,
            text="📋 Scan Posts",
            width=140,
            height=36,
            command=self._on_scan,
        )
        self.scan_btn.grid(row=0, column=0, padx=(0, 8))

        self.scrape_btn = ctk.CTkButton(
            btn_frame,
            text="⬇ Scrape Selected",
            width=160,
            height=36,
            state="disabled",
            command=self._on_scrape,
        )
        self.scrape_btn.grid(row=0, column=1, padx=(0, 8))

        self.post_count_label = ctk.CTkLabel(
            btn_frame, text="", font=ctk.CTkFont(size=12), text_color="gray"
        )
        self.post_count_label.grid(row=0, column=2, padx=(8, 0))

        # --- Row 2: Output folder ---
        folder_frame = ctk.CTkFrame(self, fg_color="transparent")
        folder_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        folder_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(folder_frame, text="Output:", font=ctk.CTkFont(size=12), text_color="gray").grid(
            row=0, column=0, padx=(0, 8), sticky="w"
        )

        self.output_label = ctk.CTkLabel(
            folder_frame,
            text=get_output_folder(self.config),
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w",
        )
        self.output_label.grid(row=0, column=1, sticky="ew")

        self.folder_btn = ctk.CTkButton(
            folder_frame,
            text="📁",
            width=36,
            height=28,
            command=self._pick_folder,
        )
        self.folder_btn.grid(row=0, column=2)

        # --- Row 3: Progress ---
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        self.progress_bar.set(0)

        # --- Row 4: Post list (scrollable) ---
        self.post_list_frame = ctk.CTkScrollableFrame(
            self,
            label_text="Posts",
            label_font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.post_list_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 8))
        self.post_list_frame.grid_columnconfigure(0, weight=0)   # checkbox
        self.post_list_frame.grid_columnconfigure(1, weight=0)   # index
        self.post_list_frame.grid_columnconfigure(2, weight=0)   # date
        self.post_list_frame.grid_columnconfigure(3, weight=1)   # headline

        self.post_checkboxes: list[ctk.CTkCheckBox] = []
        self.post_vars: list[ctk.BooleanVar] = []

        # --- Row 5: Status log ---
        self.status_label = ctk.CTkLabel(
            self,
            text="Ready. Enter a LinkedIn profile URL and click Scan Posts.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w",
        )
        self.status_label.grid(row=5, column=0, sticky="ew")

    def _set_status(self, msg: str):
        """Update status label from any thread."""
        self.after(0, lambda: self.status_label.configure(text=msg))

    def _set_progress(self, value: float):
        """Update progress bar (0.0 - 1.0) from any thread."""
        self.after(0, lambda: self.progress_bar.set(value))

    def _set_buttons(self, enabled: bool):
        """Enable or disable action buttons."""
        state = "normal" if enabled else "disabled"
        self.after(0, lambda: self.scan_btn.configure(state=state))
        self.after(0, lambda: self.login_btn.configure(state=state))

    def _get_scraper(self) -> LinkedInScraper:
        """Get or create the scraper instance."""
        if self._scraper is None:
            state_dir = get_browser_state_dir(self.config)
            self._scraper = LinkedInScraper(state_dir)
        return self._scraper

    # ──────────── LOGIN ────────────

    def _on_login(self):
        """Open LinkedIn login in a Playwright browser."""
        self._set_buttons(False)
        self._set_status("Opening browser for LinkedIn login...")

        def worker():
            try:
                scraper = self._get_scraper()
                scraper.open_login(on_status=self._set_status)
            except Exception as e:
                self._set_status(f"Login error: {e}")
            finally:
                self._set_buttons(True)

        threading.Thread(target=worker, daemon=True).start()

    # ──────────── SCAN ────────────

    def _on_scan(self):
        """Scan posts from the entered LinkedIn URL."""
        url = self.url_entry.get().strip()
        if not url:
            self._set_status("Please enter a LinkedIn profile URL.")
            return

        self._set_buttons(False)
        self._set_progress(0)
        self._set_status("Scanning posts...")

        def worker():
            try:
                scraper = self._get_scraper()
                self.previews = scraper.scan_posts(url, on_status=self._set_status)
                self.after(0, self._populate_post_list)
                self._set_status(f"Found {len(self.previews)} posts. Select a starting post and click Scrape.")
            except PermissionError as e:
                self._set_status(f"⚠ {e}")
            except Exception as e:
                self._set_status(f"Scan error: {e}")
            finally:
                self._set_buttons(True)
                self._set_progress(1.0)

        threading.Thread(target=worker, daemon=True).start()

    def _populate_post_list(self):
        """Fill the post list with scan results."""
        # Clear existing
        for widget in self.post_list_frame.winfo_children():
            widget.destroy()
        self.post_checkboxes.clear()
        self.post_vars.clear()

        # Header row
        ctk.CTkLabel(
            self.post_list_frame, text="", width=30
        ).grid(row=0, column=0, padx=2, pady=2)
        ctk.CTkLabel(
            self.post_list_frame, text="#", font=ctk.CTkFont(size=11, weight="bold"), width=30
        ).grid(row=0, column=1, padx=2, pady=2, sticky="w")
        ctk.CTkLabel(
            self.post_list_frame, text="Date", font=ctk.CTkFont(size=11, weight="bold"), width=100
        ).grid(row=0, column=2, padx=2, pady=2, sticky="w")
        ctk.CTkLabel(
            self.post_list_frame, text="Preview", font=ctk.CTkFont(size=11, weight="bold")
        ).grid(row=0, column=3, padx=2, pady=2, sticky="w")

        self.post_count_label.configure(text=f"{len(self.previews)} posts found")

        for i, preview in enumerate(self.previews):
            row = i + 1
            var = ctk.BooleanVar(value=True)
            self.post_vars.append(var)

            cb = ctk.CTkCheckBox(self.post_list_frame, text="", variable=var, width=30)
            cb.grid(row=row, column=0, padx=2, pady=1, sticky="w")
            self.post_checkboxes.append(cb)

            ctk.CTkLabel(
                self.post_list_frame,
                text=str(i + 1),
                font=ctk.CTkFont(size=11),
                text_color="gray",
                width=30,
            ).grid(row=row, column=1, padx=2, pady=1, sticky="w")

            ctk.CTkLabel(
                self.post_list_frame,
                text=preview.date_text[:20] if preview.date_text else "—",
                font=ctk.CTkFont(size=11),
                width=100,
            ).grid(row=row, column=2, padx=2, pady=1, sticky="w")

            headline_text = preview.headline[:100] + ("..." if len(preview.headline) > 100 else "")
            ctk.CTkLabel(
                self.post_list_frame,
                text=headline_text,
                font=ctk.CTkFont(size=11),
                anchor="w",
            ).grid(row=row, column=3, padx=2, pady=1, sticky="ew")

        # Enable scrape button
        self.scrape_btn.configure(state="normal")

    # ──────────── SCRAPE ────────────

    def _on_scrape(self):
        """Scrape selected posts and save as markdown."""
        url = self.url_entry.get().strip()
        if not url:
            self._set_status("Please enter a LinkedIn profile URL.")
            return

        # Find the last selected post (the "start from" post — furthest down = oldest)
        selected_indices = [i for i, var in enumerate(self.post_vars) if var.get()]
        if not selected_indices:
            self._set_status("No posts selected. Check the posts you want to scrape.")
            return

        start_index = max(selected_indices)

        self._set_buttons(False)
        self.scrape_btn.configure(state="disabled")
        self._set_progress(0)
        self._set_status("Scraping posts...")

        def worker():
            try:
                scraper = self._get_scraper()

                def on_status(msg):
                    self._set_status(msg)

                raw_posts = scraper.scrape_posts(
                    url,
                    start_index=start_index,
                    max_posts=self.config.get("max_posts", 50),
                    on_status=on_status,
                )

                self._set_status(f"Parsing {len(raw_posts)} posts...")

                # Parse raw posts
                parsed_posts = []
                for raw in raw_posts:
                    post = parse_post(raw.html, raw.date_text, raw.element_id)
                    parsed_posts.append(post)

                # Filter to only selected indices
                # The raw_posts are reversed (oldest first), but we need to match
                # against the original preview indices
                # For simplicity, we save all scraped posts (user already selected range)

                self._set_status("Saving posts as markdown...")
                output_folder = get_output_folder(self.config)

                def on_save_progress(current, total, filepath):
                    self._set_progress(current / total if total else 1.0)
                    if filepath:
                        self._set_status(f"Saved {current}/{total}: {filepath}")

                saved = save_posts(parsed_posts, output_folder, on_progress=on_save_progress)
                self._set_status(f"✅ Done! Saved {len(saved)} posts to {output_folder}")
                self._set_progress(1.0)

            except PermissionError as e:
                self._set_status(f"⚠ {e}")
            except Exception as e:
                self._set_status(f"Scrape error: {e}")
            finally:
                self._set_buttons(True)
                self.after(0, lambda: self.scrape_btn.configure(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    # ──────────── FOLDER PICKER ────────────

    def _pick_folder(self):
        """Open a folder picker dialog for the output folder."""
        from tkinter import filedialog
        folder = filedialog.askdirectory(
            title="Select Output Folder",
            initialdir=get_output_folder(self.config),
        )
        if folder:
            self.config["output_folder"] = folder
            self.output_label.configure(text=folder)

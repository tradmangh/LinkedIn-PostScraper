"""Scrape tab — URL input, login, post scanning, and scraping with progress."""


import logging
import threading
import customtkinter as ctk
import random
import tkinter as tk

from ..scraper import LinkedInScraper, PostPreview
from ..parser import parse_post
from ..storage import save_posts
from ..config import get_output_folder, get_browser_state_dir

logger = logging.getLogger(__name__)


class ToolTip:
    """Simple ToolTip for CustomTkinter widgets."""
    def __init__(self, widget, message):
        self.widget = widget
        self.message = message
        self.tooltip_window = None

    def show(self):
        if self.tooltip_window or not self.message:
            return
        
        # Position tooltip relative to the widget using geometry
        widget_root_x = self.widget.winfo_rootx()
        widget_root_y = self.widget.winfo_rooty()
        widget_width = self.widget.winfo_width()
        widget_height = self.widget.winfo_height()
        
        self.tooltip_window = ctk.CTkToplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        
        label = ctk.CTkLabel(
            self.tooltip_window, 
            text=self.message, 
            corner_radius=6, 
            fg_color="#333333", 
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12)
        )
        label.pack(ipadx=8, ipady=4)
        
        # Update to get actual tooltip dimensions
        self.tooltip_window.update_idletasks()
        tooltip_width = self.tooltip_window.winfo_width()
        
        # Center tooltip horizontally relative to widget, slightly below it
        x = widget_root_x + (widget_width - tooltip_width) // 2
        y = widget_root_y + widget_height + 10
        
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

    def hide(self):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def update_message(self, message):
        self.message = message


class ScrapeFrame(ctk.CTkFrame):
    """Frame for the Scrape tab."""

    def __init__(self, parent, config: dict):
        super().__init__(parent, fg_color="transparent")
        self.config = config
        self.previews: list[PostPreview] = []
        self._scraper = None
        self._scraper_lock = threading.Lock()  # Ensure scraping/validation don't collide
        self._is_logged_in = False  # Track login state
        self._pulse_animation_active = True  # Control pulse animation
        
        self.stop_event = threading.Event()
        self._matrix_running = False
        self.matrix_canvas = None
        self.matrix_chars = []
        
        self._validation_after_id = None  # Store after callback ID for cancellation
        self._tooltip = None  # Will be attached to url_entry
        self.selected_indices = set()  # Track selected post indices

        self.grid_rowconfigure(4, weight=1)  # post list gets the space
        self.grid_columnconfigure(0, weight=1)

        # --- Row 0: Login button (left) + URL input (hidden until login) ---
        url_frame = ctk.CTkFrame(self, fg_color="transparent")
        url_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        url_frame.grid_columnconfigure(2, weight=1)

        # Login button on the left
        self.login_btn = ctk.CTkButton(
            url_frame,
            text="🔑 Login to LinkedIn",
            width=150,
            height=36,
            command=self._on_login,
        )
        self.login_btn.grid(row=0, column=0, padx=(0, 0))
        
        # Start pulse animation for login button
        self._start_login_pulse()

        # URL label (hidden initially)
        self.url_label = ctk.CTkLabel(url_frame, text="Profile URL / Name:", font=ctk.CTkFont(size=13))
        self.url_label.grid(row=0, column=1, padx=(16, 8), sticky="w")
        self.url_label.grid_remove()  # Hide until login

        # URL entry (hidden initially)
        self.url_entry = ctk.CTkEntry(
            url_frame,
            placeholder_text="https://www.linkedin.com/in/username/ (or just 'username')",
            height=36,
            font=ctk.CTkFont(size=13),
        )
        self.url_entry.grid(row=0, column=2, sticky="ew", padx=(0, 0))
        self.url_entry.grid_remove()  # Hide until login
        
        # Bind URL entry to validate and enable scan button
        self.url_entry.bind("<KeyRelease>", self._on_url_change)
        
        # Initialize tooltip
        self._tooltip = ToolTip(self.url_entry, "")
        self.url_entry.bind("<Enter>", lambda e: self._tooltip.show() if self._tooltip.message else None)
        self.url_entry.bind("<Leave>", lambda e: self._tooltip.hide())

        # --- Row 1: Action buttons + Output folder ---
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        btn_frame.grid_columnconfigure(4, weight=1)  # Output label gets remaining space

        self.scan_btn = ctk.CTkButton(
            btn_frame,
            text="📋 Scan Posts",
            width=140,
            height=36,
            command=self._on_scan,
            state="disabled",  # Start disabled until valid URL
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
        self.scrape_btn.grid(row=0, column=1, padx=(0, 16))

        # Output folder display (moved to same row)
        ctk.CTkLabel(btn_frame, text="Output:", font=ctk.CTkFont(size=12), text_color="gray").grid(
            row=0, column=2, padx=(0, 8), sticky="w"
        )

        self.output_label = ctk.CTkLabel(
            btn_frame,
            text=get_output_folder(self.config),
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w",
        )
        self.output_label.grid(row=0, column=3, sticky="ew")

        self.folder_btn = ctk.CTkButton(
            btn_frame,
            text="📁",
            width=36,
            height=28,
            command=self._pick_folder,
        )
        self.folder_btn.grid(row=0, column=4, padx=(8, 0))



        # --- Row 2: Progress ---
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        self.progress_bar.set(0)

        # --- Row 3: Post list header + scrollable ---
        posts_header_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), corner_radius=6)
        posts_header_frame.grid(row=3, column=0, sticky="ew", pady=(4, 4))
        posts_header_frame.grid_columnconfigure(2, weight=1)
        
        posts_header = ctk.CTkLabel(
            posts_header_frame,
            text="📝 Posts",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        )
        posts_header.grid(row=0, column=0, sticky="w", padx=(12, 4), pady=8)

        self.post_count_label = ctk.CTkLabel(
            posts_header_frame,
            text="(0)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="gray",
            anchor="w",
        )
        self.post_count_label.grid(row=0, column=1, sticky="w", padx=(0, 12), pady=8)
        
        # Filter input
        self.post_filter_entry = ctk.CTkEntry(
            posts_header_frame,
            placeholder_text="🔍 Filter posts...",
            width=200,
            height=28,
        )
        self.post_filter_entry.grid(row=0, column=3, sticky="e", padx=12, pady=8)
        self.post_filter_entry.bind("<KeyRelease>", self._on_post_filter_change)

        self.post_list_frame = ctk.CTkScrollableFrame(self)
        self.post_list_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 8))
        self.post_list_frame.grid_columnconfigure(0, weight=0)   # checkbox
        self.post_list_frame.grid_columnconfigure(1, weight=0)   # index
        self.post_list_frame.grid_columnconfigure(2, weight=0)   # date
        self.post_list_frame.grid_columnconfigure(3, weight=1)   # headline

        self.post_checkboxes: list[ctk.CTkCheckBox] = []
        self.post_vars: list[ctk.BooleanVar] = []
        self.select_all_var = ctk.BooleanVar(value=True)

        # --- Row 5: Status frame (prominent) ---
        self.status_frame = ctk.CTkFrame(self, fg_color=("#E8F4F8", "#1a3a4a"), corner_radius=8)
        self.status_frame.grid(row=5, column=0, sticky="ew", pady=(0, 0))
        self.status_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="ℹ️  Please login.",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#1a5490", "#6db3e8"),
            anchor="w",
        )
        self.status_label.grid(row=0, column=0, sticky="ew", padx=16, pady=12)

    def focus_filter_entry(self):
        """Focus the filter entry."""
        if self.post_filter_entry.winfo_viewable():
            self.post_filter_entry.focus_set()

    def _set_status(self, msg: str, status_type: str = "info"):
        """Update status label from any thread with icon and color.
        
        Args:
            msg: Status message to display
            status_type: One of 'info', 'success', 'warning', 'error', 'working'
        """
        # Icon mapping
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "working": "🔄",
        }
        
        # Color mapping (light mode, dark mode)
        colors = {
            "info": (("#E8F4F8", "#1a3a4a"), ("#1a5490", "#6db3e8")),
            "success": (("#E8F8E8", "#1a4a1a"), ("#1a7a1a", "#6de86d")),
            "warning": (("#FFF4E6", "#4a3a1a"), ("#8a5a00", "#e8b36d")),
            "error": (("#FFE8E8", "#4a1a1a"), ("#8a1a1a", "#e86d6d")),
            "working": (("#F0E8FF", "#2a1a4a"), ("#5a1a8a", "#b36de8")),
        }
        
        icon = icons.get(status_type, icons["info"])
        bg_color, text_color = colors.get(status_type, colors["info"])
        
        full_msg = f"{icon}  {msg}"
        
        def update():
            self.status_frame.configure(fg_color=bg_color)
            self.status_label.configure(text=full_msg, text_color=text_color)
        
        self.after(0, update)

    def _set_progress(self, value: float):
        """Update progress bar (0.0 - 1.0) from any thread."""
        self.after(0, lambda: self.progress_bar.set(value))

    def _set_buttons(self, enabled: bool):
        """Enable or disable action buttons (Legacy, used for Login)."""
        state = "normal" if enabled else "disabled"
        self.after(0, lambda: self.scan_btn.configure(state=state))
        self.after(0, lambda: self.login_btn.configure(state=state))

    def _set_ui_state(self, state: str):
        """Set UI state for buttons and animation.
        
        Args:
            state: 'idle', 'scanning', 'scraping'
        """
        if state == "idle":
             self.stop_event.clear()
             self.after(0, lambda: self.scan_btn.configure(
                 text="📋 Scan Posts", 
                 command=self._on_scan,
                 fg_color=["#3B8ED0", "#1F6AA5"],
                 hover_color=["#36719F", "#144870"],
                 state="normal"
             ))
             self.after(0, lambda: self.scrape_btn.configure(
                 text="⬇ Scrape Selected", 
                 command=self._on_scrape,
                 fg_color=["#3B8ED0", "#1F6AA5"],
                 hover_color=["#36719F", "#144870"],
                 state="normal" if self.previews else "disabled"
             ))
             self.after(0, lambda: self.login_btn.configure(state="normal"))
             self.after(0, self._stop_matrix_animation)

        elif state == "scanning":
             self.stop_event.clear()
             self.after(0, self._start_matrix_animation)
             self.after(0, lambda: self.scan_btn.configure(
                 text="🛑 STOP", 
                 command=self._on_stop,
                 fg_color="#CC0000",
                 hover_color="#AA0000",
                 state="normal"
             ))
             self.after(0, lambda: self.scrape_btn.configure(state="disabled"))
             self.after(0, lambda: self.login_btn.configure(state="disabled"))
             
        elif state == "scraping":
             self.stop_event.clear()
             self.after(0, self._start_matrix_animation)
             self.after(0, lambda: self.scrape_btn.configure(
                 text="🛑 STOP", 
                 command=self._on_stop,
                 fg_color="#CC0000",
                 hover_color="#AA0000",
                 state="normal"
             ))
             self.after(0, lambda: self.scan_btn.configure(state="disabled"))
             self.after(0, lambda: self.login_btn.configure(state="disabled"))

    def _on_stop(self):
        """Handle Stop button click."""
        self.stop_event.set()
        self._set_status("Stopping operation...", "warning")
        # Buttons will reset when the worker thread finishes and calls _set_ui_state("idle")

    # ──────────── MATRIX ANIMATION ────────────

    def _start_matrix_animation(self):
        """Start the Matrix-style rain animation overlay."""
        if self._matrix_running:
            return
            
        self._matrix_running = True
        
        # Create canvas overlay if not exists
        if not self.matrix_canvas:
            self.matrix_canvas = tk.Canvas(
                self, 
                bg="#0D1117", 
                highlightthickness=0
            )
        
        # Position over the post list frame
        self.post_list_frame.grid_remove()
        self.matrix_canvas.grid(row=4, column=0, sticky="nsew", pady=(0, 8))
        
        # Initialize drops
        width = self.post_list_frame.winfo_width()
        col_width = 24
        columns = int(width / col_width)
        self.matrix_drops = [random.randint(-20, 0) for _ in range(columns)]
        
        self._animate_matrix()

    def _animate_matrix(self):
        """Animation loop for Matrix rain."""
        if not self._matrix_running:
            return
            
        height = self.post_list_frame.winfo_height()
        col_width = 24
        
        self.matrix_canvas.delete("all")
        
        # Draw characters
        for i in range(len(self.matrix_drops)):
            # Draw trail
            head_y = self.matrix_drops[i]
            x = i * col_width + 10
            
            # Trail length
            trail_len = 8
            
            for j in range(trail_len):
                y_pos = head_y - j
                if y_pos < 0:
                    continue
                
                # Char selection
                char = random.choice("01XYCRZ01")
                
                # Color & Font
                if j == 0:
                    # Head: Bright White/Green
                    color = "#CCFFCC" 
                    font = ("Courier", 18, "bold")
                elif j == 1:
                    # Second: Bright Green
                    color = "#00FF00"
                    font = ("Courier", 18, "bold")
                else:
                    # Tail: Fade out
                    # Simple hex fade for green
                    # 00FF00 -> 003300
                    intensity = max(50, 255 - (j * 30))
                    hex_val = f"{intensity:02x}"
                    color = f"#00{hex_val}00"
                    font = ("Courier", 18, "normal")

                self.matrix_canvas.create_text(
                    x, 
                    y_pos * 24, # y step matches col width approx 
                    text=char, 
                    fill=color, 
                    font=font
                )
            
            # Increment Y
            self.matrix_drops[i] += 1
            
            # Reset if off screen (randomize reset to avoid wave pattern)
            min_reset_y = height / 24
            if self.matrix_drops[i] > min_reset_y and random.random() > 0.96:
                self.matrix_drops[i] = 0
                
        self.after(50, self._animate_matrix)

    def _stop_matrix_animation(self):
        """Stop the animation and restore list view."""
        self._matrix_running = False
        if self.matrix_canvas:
            self.matrix_canvas.grid_remove()
        self.post_list_frame.grid()

    def _get_scraper(self) -> LinkedInScraper:
        """Get or create the scraper instance."""
        if self._scraper is None:
            state_dir = get_browser_state_dir(self.config)
            self._scraper = LinkedInScraper(state_dir)
        return self._scraper

    def _start_login_pulse(self):
        """Start pulsing animation on login button."""
        if not self._pulse_animation_active:
            return
        
        # Pulse by changing the button's appearance
        def pulse():
            if not self._pulse_animation_active:
                # Reset to normal state when animation stops
                try:
                    self.login_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"])
                except Exception:
                    # Button may be destroyed, ignore
                    pass
                return
            
            # Get current appearance mode colors
            try:
                # Alternate between normal and brighter color
                import time
                cycle = int(time.time() * 2) % 2  # 0.5 second cycle
                
                if cycle == 0:
                    # Brighter
                    self.login_btn.configure(fg_color=["#5BA3E0", "#3F8AC5"])
                else:
                    # Normal
                    self.login_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"])
                
                # Schedule next pulse
                self.after(500, pulse)
            except Exception:
                # If button is destroyed, stop animation
                self._pulse_animation_active = False
        
        pulse()

    def _stop_login_pulse(self):
        """Stop pulsing animation on login button."""
        self._pulse_animation_active = False
        # Reset button to normal color
        try:
            self.login_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"])
        except Exception:
            # Button may be destroyed, ignore
            pass

    # ──────────── URL VALIDATION ────────────
    
    def _on_url_change(self, event=None):
        """Validate URL and enable/disable scan button. Debounce deep validation."""
        url = self.url_entry.get().strip()
        
        # Cancel pending validation
        if self._validation_after_id:
            self.after_cancel(self._validation_after_id)
            self._validation_after_id = None
        
        # Reset tooltip/style
        self._tooltip.update_message("")
        self.url_entry.configure(border_color=["#979DA2", "#565B5E"]) # Default border color (approx)

        # Immediate Regex/Format Check
        is_format_valid, is_username_only = self._check_url_format(url)
        
        if not is_format_valid:
            self.scan_btn.configure(state="disabled")
            if url: # Only show error if not empty
                self.url_entry.configure(border_color="#FF5555")
                self._tooltip.update_message("Invalid URL format. Use https://linkedin.com/in/... or just username")
            return

        # Format passed (either full URL or username)
        # If it's a full URL, we trust it for now but still can verify.
        # If it's a username, we DEFINITELY want to verify and convert.
        
        # We assume valid format for now to enable button, but we'll do a deep check
        self.scan_btn.configure(state="disabled") # Disable until verified reachable? Or allow?
        # User requested: "postfix the validate if the URL exists/is reachable"
        # So wait for debounce
        
        # Schedule validation on UI thread (thread-safe)
        self._validation_after_id = self.after(1500, lambda: self._perform_delayed_validation(url, is_username_only))
    
    def _check_url_format(self, url: str) -> tuple[bool, bool]:
        """Check format. Returns (is_valid_format, is_username_only)."""
        if not url:
            return False, False
            
        # Check for forbidden chars in username/url parts
        # If full URL:
        if "linkedin.com/in/" in url:
            return True, False
            
        # If username only:
        # Should not contain / or : or spaces
        if "/" in url or ":" in url or " " in url:
            return False, False
            
        return True, True

    def _perform_delayed_validation(self, url: str, is_username_only: bool):
        """Validate the profile URL. 
        
        Called on UI thread via self.after(). Spawns a background thread for network I/O
        and schedules UI updates back on the main thread.
        """
        
        # Check if URL has changed since this validation was scheduled
        current_url = self.url_entry.get().strip()
        if current_url != url:
            # User has typed something else, skip this validation
            return
        
        target_url = url
        if is_username_only:
            target_url = f"https://www.linkedin.com/in/{url}/"
            
        self._set_status("Validating profile...", "working")
        
        def validate_task():
            # Acquire lock to use scraper
            # If scraper is busy (e.g. login or scan), schedule a retry so the
            # UI does not remain stuck with validation pending.
            if not self._scraper_lock.acquire(blocking=False):
                def retry():
                    # Only retry if the URL hasn't changed since this validation
                    current = self.url_entry.get().strip()
                    if current != url:
                        return
                    self._set_status("Scraper busy, will retry validation shortly...", "warning")
                    self._perform_delayed_validation(url, is_username_only)

                # Schedule a short delayed retry on the main UI thread
                try:
                    self.after(500, retry)
                except Exception:
                    # If scheduling fails for any reason, at least leave a warning
                    self._set_status("Scraper busy, please try validating the URL again.", "warning")
                return

            try:
                scraper = self._get_scraper()
                exists = scraper.check_profile_exists(target_url)
                
                if exists:
                    self._set_status("Profile found!", "success")
                    self.after(0, lambda: self._on_validation_success(target_url))
                else:
                    self._set_status("Profile not reachable or does not exist.", "error")
                    self.after(0, lambda: self._on_validation_failure("Profile not found on LinkedIn"))
            
            except Exception as e:
                self._set_status(f"Validation error: {e}", "error")
            finally:
                self._scraper_lock.release()
                
        threading.Thread(target=validate_task, daemon=True).start()

    def _on_validation_success(self, final_url: str):
        """Called when validation succeeds."""
        # Update URL field if it was username only
        current = self.url_entry.get().strip()
        # If user hasn't changed input yet
        if current in final_url or final_url in current or current in final_url.split("/"):
             if current != final_url:
                 self.url_entry.delete(0, "end")
                 self.url_entry.insert(0, final_url)
        
        self.url_entry.configure(border_color="#00EE00") # Green border
        self.scan_btn.configure(state="normal")
        
    def _on_validation_failure(self, message: str):
        """Called when validation fails."""
        self.url_entry.configure(border_color="#FF5555") # Red border
        self._tooltip.update_message(message)
        self.scan_btn.configure(state="disabled")

    def _is_valid_profile_url(self, url: str) -> bool:
        # Kept for compatibility if needed, but mostly replaced by _check_url_format logic
        # wrapping it:
        valid, _ = self._check_url_format(url)
        return valid

    # ──────────── LOGIN ────────────

    def _on_login(self):
        """Open LinkedIn login in a Playwright browser."""
        self._set_buttons(False)
        self._set_status("Opening browser for LinkedIn login...", "working")

        def worker():
            try:
                with self._scraper_lock:
                    scraper = self._get_scraper()
                    profile_url = scraper.open_login(on_status=lambda msg: self._set_status(msg, "working"))
                
                # Mark as logged in
                self._is_logged_in = True
                self._stop_login_pulse()
                
                # Hide login button and show URL field
                self.after(0, lambda: self.login_btn.grid_remove())
                self.after(0, lambda: self.url_label.grid())
                self.after(0, lambda: self.url_entry.grid())
                
                # Enable the URL entry field
                self.after(0, lambda: self.url_entry.configure(state="normal"))
                
                # If we got a profile URL, populate it in the entry field
                if profile_url:
                    def populate_url():
                        self.url_entry.delete(0, "end")
                        self.url_entry.insert(0, profile_url)
                    
                    self.after(0, populate_url)
                    # Trigger validation success immediately (we know it's valid from login)
                    self.after(100, lambda: self._on_validation_success(profile_url))
                    self._set_status(f"Login successful! Profile URL: {profile_url}", "success")
                else:
                    self._set_status("Login successful! You can now enter a profile URL and scan posts.", "success")
            except Exception as e:
                logger.exception("Login error occurred")
                self._set_status(f"Login error: {e}", "error")
            finally:
                self._set_buttons(True)

        threading.Thread(target=worker, daemon=True).start()

    # ──────────── SCAN ────────────

    def _on_scan(self):
        """Scan posts from the entered LinkedIn URL."""
        url = self.url_entry.get().strip()
        if not url:
            self._set_status("Please enter a LinkedIn profile URL.", "warning")
            return

        self._set_ui_state("scanning")
        self._set_progress(0)
        self._set_status("Scanning posts...", "working")

        def worker():
            try:
                with self._scraper_lock:
                    scraper = self._get_scraper()
                    def on_scan_count(count):
                        self.after(0, lambda: self.post_count_label.configure(text=f"(Found {count})"))

                    self.previews = scraper.scan_posts(
                        url, 
                        on_status=lambda msg: self._set_status(msg, "working"),
                        should_stop=lambda: self.stop_event.is_set(),
                        on_data_count=on_scan_count
                    )
                    
                    if self.stop_event.is_set():
                        self._set_status("Scan cancelled.", "warning")
                    else:
                        # Select all by default
                        self.selected_indices = set(range(len(self.previews)))
                        self._set_status(f"Found {len(self.previews)} posts. Select posts and click Scrape.", "success")
                
                self.after(0, self._populate_post_list)
                
            except PermissionError as e:
                self._set_status(str(e), "warning")
            except Exception as e:
                self._set_status(f"Scan error: {e}", "error")
            finally:
                self._set_ui_state("idle")
                self._set_progress(1.0)

        threading.Thread(target=worker, daemon=True).start()

    def _populate_post_list(self):
        """Fill the post list with scan results."""
        # Clear existing
        for widget in self.post_list_frame.winfo_children():
            widget.destroy()
        self.post_checkboxes.clear()
        self.post_vars.clear()
        # Note: self.selected_indices is NOT cleared here, to persist across filters.

        # Toggle filter visibility
        if len(self.previews) >= 3:
            self.post_filter_entry.grid()
        else:
            self.post_filter_entry.grid_remove()

        # Header row with select-all checkbox
        select_all_cb = ctk.CTkCheckBox(
            self.post_list_frame,
            text="",
            variable=self.select_all_var,
            width=30,
            command=self._toggle_all_posts
        )
        select_all_cb.grid(row=0, column=0, padx=2, pady=2)
        
        ctk.CTkLabel(
            self.post_list_frame, text="#", font=ctk.CTkFont(size=11, weight="bold"), width=30
        ).grid(row=0, column=1, padx=2, pady=2, sticky="w")
        ctk.CTkLabel(
            self.post_list_frame, text="Date", font=ctk.CTkFont(size=11, weight="bold"), width=100
        ).grid(row=0, column=2, padx=2, pady=2, sticky="w")
        ctk.CTkLabel(
            self.post_list_frame, text="Preview", font=ctk.CTkFont(size=11, weight="bold")
        ).grid(row=0, column=3, padx=2, pady=2, sticky="w")

        # Filter logic
        filter_text = self.post_filter_entry.get().lower()
        visible_count = 0

        for i, preview in enumerate(self.previews):
            headline = (preview.headline or "").lower()
            date = (preview.date_text or "").lower()
            
            # Simple text filter
            if filter_text and (filter_text not in headline and filter_text not in date):
                continue
            
            visible_count += 1
            row = visible_count

            # Determine if this post is selected based on index
            is_selected = i in self.selected_indices
            var = ctk.BooleanVar(value=is_selected)
            self.post_vars.append(var)

            # Callback to update set
            # Use default args to capture current i
            def on_toggle(idx=i, v=var):
                if v.get():
                    self.selected_indices.add(idx)
                else:
                    self.selected_indices.discard(idx)

            cb = ctk.CTkCheckBox(self.post_list_frame, text="", variable=var, width=30, command=on_toggle)
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

        if visible_count == len(self.previews):
            count_text = f"({visible_count})"
        else:
            count_text = f"(Filtered {visible_count}/{len(self.previews)})"
        self.post_count_label.configure(text=count_text)

        # Enable scrape button if we have any posts
        if self.previews:
            self.scrape_btn.configure(state="normal")
        else:
            self.scrape_btn.configure(state="disabled")

    def _toggle_all_posts(self):
        """Toggle all VISIBLE post checkboxes based on select-all checkbox."""
        select_all = self.select_all_var.get()
        filter_text = self.post_filter_entry.get().lower()

        for i, preview in enumerate(self.previews):
            headline = (preview.headline or "").lower()
            date = (preview.date_text or "").lower()
             
            if filter_text and (filter_text not in headline and filter_text not in date):
                continue
            
            if select_all:
                self.selected_indices.add(i)
            else:
                self.selected_indices.discard(i)
        
        # Refresh UI to show new states
        self._populate_post_list()

    def _on_post_filter_change(self, event=None):
        """Handle filter text change."""
        self._populate_post_list()

    # ──────────── SCRAPE ────────────

    def _on_scrape(self):
        """Scrape selected posts and save as markdown."""
        url = self.url_entry.get().strip()
        if not url:
            self._set_status("Please enter a LinkedIn profile URL.", "warning")
            return

        # Filter selected_indices based on current text filter
        # Only scrape what is visible in the filter
        filter_text = self.post_filter_entry.get().lower()
        effective_indices = []
        
        for idx in self.selected_indices:
            try:
                if idx < len(self.previews):
                    preview = self.previews[idx]
                    headline = (preview.headline or "").lower()
                    date = (preview.date_text or "").lower()
                    
                    if not filter_text or (filter_text in headline or filter_text in date):
                        effective_indices.append(idx)
            except IndexError:
                continue

        if not effective_indices:
            if self.selected_indices:
                self._set_status("No selected posts match the current filter.", "warning")
            else:
                self._set_status("No posts selected. Check the posts you want to scrape.", "warning")
            return

        # Find the last selected post (the "start from" post — furthest down = oldest)
        selected_indices = sorted(effective_indices)
        
        start_index = max(selected_indices)

        # Extract author handle for folder name
        forced_author = None
        if "/in/" in url:
             parts = url.split("/in/")
             if len(parts) > 1:
                 # Take first part after /in/, remove queries/slashes
                 forced_author = parts[1].split("/")[0].split("?")[0]
        elif url and "linkedin.com" not in url:
             # Assume username
             forced_author = url

        self._set_ui_state("scraping")
        self._set_progress(0)
        self._set_status("Starting scrape...", "working")

        def worker():
            try:
                def on_scrape_count(count):
                    # During verify/scroll phase
                     self.after(0, lambda: self.post_count_label.configure(text=f"(Found {count})"))

                def on_save_progress(current, total, filepath):
                     # Update label
                     self.after(0, lambda: self.post_count_label.configure(text=f"(Scraped {current}/{total})"))
                     self._set_progress(current / total)
                     if filepath:
                        self._set_status(f"Saved {current}/{total}: {filepath}", "working")

                with self._scraper_lock:
                    scraper = self._get_scraper()

                    def on_status(msg):
                        self._set_status(msg, "working")

                    # Scraper returns everything up to start_index
                    raw_posts = scraper.scrape_posts(
                        url,
                        start_index=start_index,
                        max_posts=self.config.get("max_posts", 50),
                        on_status=on_status,
                        should_stop=lambda: self.stop_event.is_set(),
                        on_data_count=on_scrape_count
                    )

                if self.stop_event.is_set() and not raw_posts:
                     self._set_status("Scrape cancelled.", "warning")
                     return

                self._set_status(f"Filtering and parsing {len(raw_posts)} posts...", "working")

                # Filter and Parse
                parsed_posts = []
                for raw in raw_posts:
                    if raw.index in selected_indices:
                        post = parse_post(raw.html, raw.date_text, raw.element_id)
                        parsed_posts.append(post)

                if not parsed_posts:
                    self._set_status("No selected posts found in scrape result.", "warning")
                    return

                self._set_status("Saving posts as markdown...", "working")
                output_folder = get_output_folder(self.config)

                saved = save_posts(
                    parsed_posts, 
                    output_folder, 
                    on_progress=on_save_progress,
                    forced_author=forced_author
                )
                
                self._set_status(f"Done! Saved {len(saved)} posts to {output_folder}/{forced_author or 'unknown'}", "success")
                self._set_progress(1.0)
                # Reset counter label to normal view
                self.after(0, self._populate_post_list)

            except PermissionError as e:
                self._set_status(str(e), "warning")
            except Exception as e:
                self._set_status(f"Scrape error: {e}", "error")
                logger.exception("Scrape error in worker thread")
            finally:
                self._set_ui_state("idle")

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

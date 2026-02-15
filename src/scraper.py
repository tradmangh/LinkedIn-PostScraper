"""LinkedIn post scraper using Playwright with persistent session."""

import re
import time
import random
import logging
from dataclasses import dataclass, field
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)


@dataclass
class PostPreview:
    """Lightweight post preview for the scan phase."""
    index: int
    date_text: str
    headline: str
    element_id: str  # data-urn or similar identifier


@dataclass
class RawPost:
    """Raw post data extracted from LinkedIn."""
    html: str
    date_text: str
    element_id: str
    index: int


class LinkedInScraper:
    """Scrapes LinkedIn posts using Playwright with persistent browser session."""

    SCROLL_PAUSE_TIME = 2.0
    MAX_NO_CHANGE = 3
    
    # Human-like delay ranges (in seconds)
    DELAY_BETWEEN_SCROLLS = (1.5, 3.0)  # Random delay between scrolls
    DELAY_BETWEEN_CLICKS = (0.8, 1.5)   # Random delay between clicks
    DELAY_AFTER_LOAD = (2.0, 3.5)       # Random delay after page load

    def __init__(self, browser_state_dir: str):
        self.browser_state_dir = browser_state_dir
        self._playwright = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
    
    def _human_delay(self, delay_range: tuple[float, float]):
        """Sleep for a random duration within the given range to simulate human behavior."""
        delay = random.uniform(*delay_range)
        time.sleep(delay)

    def _ensure_context(self, headless: bool = False):
        """Create or reuse a persistent browser context."""
        if self._context is not None:
            return
        self._playwright = sync_playwright().start()
        self._context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=self.browser_state_dir,
            headless=headless,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        self._page = self._context.pages[0] if self._context.pages else self._context.new_page()

    def close(self, on_status=None):
        """Close browser and cleanup."""
        if on_status:
            on_status("Closing browser...")
        
        if self._context:
            try:
                self._context.close()
            except Exception as e:
                if on_status:
                    on_status(f"Warning: Error closing context: {e}")
            self._context = None
            self._page = None
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception as e:
                if on_status:
                    on_status(f"Warning: Error stopping playwright: {e}")
            self._playwright = None
        
        if on_status:
            on_status("Browser closed.")

    def open_login(self, on_status=None) -> Optional[str]:
        """Open LinkedIn login page for user to authenticate manually.
        
        After successful login, navigates to the user's profile to extract the profile URL.
        
        Returns:
            The user's profile URL (e.g., https://www.linkedin.com/in/username/) or None if extraction fails.
        """
        if on_status:
            on_status("Opening browser for LinkedIn login...")

        self._ensure_context(headless=False)
        self._page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")

        if on_status:
            on_status("Please log in to LinkedIn in the browser window.")

        # Wait for the user to log in — we detect it by checking for the feed page
        profile_url = None
        login_successful = False
        
        try:
            self._page.wait_for_url("**/feed/**", timeout=300_000)  # 5 min timeout
            login_successful = True
            
            if on_status:
                on_status("Login detected! Extracting your profile URL...")
            
            # Navigate to profile page to get the actual username
            profile_url = self._extract_profile_url(on_status)
            
        except Exception as e:
            # User might have navigated elsewhere after login, check if logged in
            current_url = self._page.url
            
            if "feed" in current_url or "mynetwork" in current_url or "in/" in current_url:
                login_successful = True
                
                if on_status:
                    on_status("Login detected! Extracting your profile URL...")
                
                # Try to extract profile URL
                try:
                    profile_url = self._extract_profile_url(on_status)
                except Exception as extract_error:
                    if on_status:
                        on_status(f"Could not extract profile URL: {str(extract_error)}")
            else:
                if on_status:
                    on_status(f"Login timeout or navigation error: {str(e)}")

        # Only close the browser after we've attempted to extract the profile URL
        # or if login clearly failed
        if login_successful or profile_url:
            if on_status:
                if profile_url:
                    on_status(f"✓ Login complete! Profile: {profile_url}")
                else:
                    on_status("Login complete! You can now enter a profile URL manually.")
        
        self.close(on_status)
        return profile_url

    def _extract_profile_url(self, on_status=None) -> Optional[str]:
        """Navigate to the user's profile page and extract the profile URL.
        
        Returns:
            The user's profile URL or None if extraction fails.
        """
        try:
            if on_status:
                on_status("Navigating to your profile page...")
            
            # Navigate to the generic profile page which will redirect to the user's actual profile
            # Wait for domcontentloaded (faster than networkidle)
            self._page.goto("https://www.linkedin.com/in/", wait_until="domcontentloaded", timeout=15000)
            
            if on_status:
                on_status("Extracting profile URL...")
            
            # Wait for the URL to stabilize (LinkedIn might do redirects)
            # Quick check with minimal delays for better UX
            stable_url = None
            for attempt in range(3):  # Reduced from 5 to 3 attempts
                current_url = self._page.url
                
                # Check if we have a valid profile URL
                if "/in/" in current_url:
                    # Extract the part after /in/
                    parts = current_url.split("/in/")
                    if len(parts) > 1:
                        # Get username (everything before ?, #, or next /)
                        username_part = parts[1].split("?")[0].split("#")[0].split("/")[0]
                        
                        # Check if we have a valid username (not empty)
                        if len(username_part) > 0:
                            # Quick stability check (reduced from 1s to 0.3s)
                            time.sleep(0.3)
                            next_url = self._page.url
                            
                            if current_url == next_url:
                                # URL is stable
                                stable_url = current_url
                                break
                
                # Still redirecting, wait a bit (reduced from 1s to 0.5s)
                if attempt < 2:  # Don't wait on last attempt
                    time.sleep(0.5)
            
            if not stable_url:
                if on_status:
                    on_status("Profile page did not load properly. You can enter the URL manually.")
                return None
            
            # Extract the profile URL (remove any query parameters or fragments)
            if "/in/" in stable_url:
                # Match the profile URL pattern
                match = re.match(r"(https://www\.linkedin\.com/in/[^/?#]+)", stable_url)
                if match:
                    profile_url = match.group(1) + "/"
                    
                    # Verify the URL is valid before returning
                    if len(profile_url) > len("https://www.linkedin.com/in/"):
                        print(f"[DEBUG] Extracted profile URL: {profile_url}")  # Debug
                        if on_status:
                            on_status(f"✓ Profile URL extracted: {profile_url}")
                        return profile_url
            
            print(f"[DEBUG] Could not extract valid profile URL from: {stable_url}")  # Debug
            if on_status:
                on_status("Could not extract a valid profile URL. You can enter it manually.")
            return None
            
        except Exception as e:
            if on_status:
                on_status(f"Error extracting profile URL: {str(e)}")
            return None

    def is_logged_in(self) -> bool:
        """Check if we have a saved session by attempting to load LinkedIn."""
        try:
            self._ensure_context(headless=True)
            self._page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=15000)
            self._human_delay(self.DELAY_AFTER_LOAD)
            logged_in = "feed" in self._page.url and "login" not in self._page.url
            self.close()
            return logged_in
        except Exception:
            self.close()
            return False

    def check_profile_exists(self, profile_url: str) -> bool:
        """Check if a LinkedIn profile URL is reachable and valid."""
        try:
            self._ensure_context(headless=True)
            self._page.goto(profile_url, wait_until="domcontentloaded", timeout=15000)
            
            # 1. Check if we got redirected to auth wall (login challenge)
            if "authwall" in self._page.url or "login" in self._page.url:
                # Redirected to login/authwall, so we cannot access the profile content.
                # Treat this as "profile not reachable" for the purposes of this check.
                self.close()
                return False

            # 1b. Check for explicit 404 redirect
            if "/404/" in self._page.url:
                self.close()
                return False

            # 2. Check page title and content for 404-like messages
            # LinkedIn 404 pages often have "Page not found" or "Profile not available"
            title = self._page.title()
            content = self._page.content()
            
            if "Page not found" in title or "profile is not available" in content:
                self.close()
                return False
            
            # 3. If we are on a profile page, it usually contains "LinkedIn" in title and the name
            # or the URL matches
            self.close()
            return True

        except Exception as e:
            logger.warning(f"Error checking if profile exists: {e}")
            self.close()
            return False

    def _build_activity_url(self, profile_url: str) -> str:
        """Build the recent activity URL from a profile URL.
        
        Accepts various URL formats:
        - https://www.linkedin.com/in/username/
        - https://www.linkedin.com/in/username
        - https://www.linkedin.com/in/username/recent-activity/all/
        - username (will be converted to full URL)
        
        Returns:
            Full activity URL with /recent-activity/all/ appended.
        """
        # Normalize the URL
        profile_url = profile_url.strip().rstrip("/")
        
        # If already has recent-activity, return as-is (with trailing slash)
        if "/recent-activity/" in profile_url:
            return profile_url if profile_url.endswith("/") else profile_url + "/"
        
        # If it's just a username (no https://), convert to full URL
        if not profile_url.startswith("http"):
            profile_url = f"https://www.linkedin.com/in/{profile_url}"
        
        # Extract the base profile URL (everything up to and including the username)
        # This handles URLs with or without trailing paths
        match = re.match(r"(https://(?:www\.)?linkedin\.com/in/[^/?#]+)", profile_url)
        if match:
            base_url = match.group(1)
            return f"{base_url}/recent-activity/all/"
        
        # Fallback: just append to whatever was provided
        return f"{profile_url}/recent-activity/all/"

    def _scroll_feed(self, max_scrolls: int = 0, on_status=None, should_stop=None, on_scroll=None):
        """Scroll the feed to load posts. Returns when no new content loads.
        
        Args:
            on_scroll: Callback(scrolls) -> str. Returns extra status text.
        """
        last_height = self._page.evaluate("document.body.scrollHeight")
        scrolls = 0
        no_change_count = 0

        while True:
            # Check for cancellation
            if should_stop and should_stop():
                if on_status:
                    on_status("Operation cancelled by user.")
                break

            self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            self._human_delay(self.DELAY_BETWEEN_SCROLLS)  # Human-like random delay
            new_height = self._page.evaluate("document.body.scrollHeight")

            if new_height == last_height:
                no_change_count += 1
            else:
                no_change_count = 0

            if no_change_count >= self.MAX_NO_CHANGE:
                break

            if max_scrolls and scrolls >= max_scrolls:
                break

            last_height = new_height
            scrolls += 1

            # Determine if we should stop based on finding enough posts
            stop_scrolling = False
            if on_status:
                msg = f"Scrolling... ({scrolls} scrolls)"
                if on_scroll:
                    try:
                        # on_scroll might return a status string OR True if we should stop
                        result = on_scroll(scrolls)
                        if result is True:
                            stop_scrolling = True
                        elif result:
                            msg = f"{msg} | {result}"
                    except Exception as exc:
                        # Callback error should not stop scrolling
                        logger.warning("Error in on_scroll callback at scroll %d: %s", scrolls, exc)
                on_status(msg)
            
            if stop_scrolling:
                break

    def scan_posts(self, profile_url: str, on_status=None, should_stop=None, on_data_count=None) -> list[PostPreview]:
        """Phase 1: Scan the feed and return a list of post previews with dates and headlines.
        
        Returns posts in the order they appear on the page (newest first).
        """
        activity_url = self._build_activity_url(profile_url)

        if on_status:
            on_status(f"Navigating to {activity_url}")

        self._ensure_context(headless=True)
        self._page.goto(activity_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        # Check if we're redirected to login
        if "login" in self._page.url:
            self.close()
            raise PermissionError("Not logged in. Please log in to LinkedIn first.")
        
        # Check for cancellation
        if should_stop and should_stop():
            self.close()
            return []

        if on_status:
            on_status("Page loaded. Scrolling to load all posts...")

        def get_scan_status(scrolls):
            try:
                count = self._page.evaluate("document.querySelectorAll('div.feed-shared-update-v2[data-urn*=\"activity\"]').length")
                if on_data_count:
                    on_data_count(count)
                return f"Found {count} posts"
            except Exception:
                # Query evaluation failed, return empty status
                return ""

        self._scroll_feed(on_status=on_status, should_stop=should_stop, on_scroll=get_scan_status)
        
        # Check for cancellation before extraction
        if should_stop and should_stop():
            self.close()
            return []

        if on_status:
            on_status("Extracting post previews...")

        # Save debug HTML snapshot
        try:
            import os
            debug_dir = os.path.join(os.path.dirname(self.browser_state_dir), "debug")
            os.makedirs(debug_dir, exist_ok=True)
            debug_file = os.path.join(debug_dir, "linkedin_page.html")
            html_content = self._page.content()
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"Saved debug HTML to {debug_file}")
            if on_status:
                on_status(f"Debug: Saved page HTML to {debug_file}")
        except Exception as e:
            logger.warning(f"Could not save debug HTML: {e}")

        # Extract post previews using JavaScript for speed
        previews_data = self._page.evaluate("""
            () => {
                const posts = document.querySelectorAll('div.feed-shared-update-v2[data-urn*="activity"]');
                const results = [];
                console.log('DEBUG: scan_posts found ' + posts.length + ' posts');
                posts.forEach((post, idx) => {
                    const urn = post.getAttribute('data-urn') || '';

                    // Get date text
                    const timeEl = post.querySelector('.update-components-actor__sub-description span.visually-hidden');
                    const dateText = timeEl ? timeEl.textContent.trim() : '';

                    // Get headline / first line of post content
                    const contentEl = post.querySelector('.feed-shared-update-v2__description .update-components-text');
                    let headline = '';
                    if (contentEl) {
                        headline = contentEl.textContent.trim().substring(0, 120);
                    }
                    // Fallback: try commentary
                    if (!headline) {
                        const commentaryEl = post.querySelector('.feed-shared-update-v2__commentary');
                        if (commentaryEl) {
                            headline = commentaryEl.textContent.trim().substring(0, 120);
                        }
                    }
                    // Fallback: try update-components-text directly
                    if (!headline) {
                        const anyText = post.querySelector('.update-components-text');
                        if (anyText) {
                            headline = anyText.textContent.trim().substring(0, 120);
                        }
                    }

                    results.push({
                        index: idx,
                        dateText: dateText,
                        headline: headline || '(No text content)',
                        elementId: urn
                    });
                });
                return results;
            }
        """)

        logger.info(f"Extracted {len(previews_data)} post previews")
        
        if not previews_data:
            if on_status:
                on_status("⚠ No posts found. Check the debug HTML file for the page structure.")
        
        self.close()

        return [
            PostPreview(
                index=p["index"],
                date_text=p["dateText"],
                headline=p["headline"],
                element_id=p["elementId"],
            )
            for p in previews_data
        ]

    def scrape_posts(
        self,
        profile_url: str,
        start_index: int = 0,
        max_posts: int = 50,
        on_status=None,
        on_progress=None,
        should_stop=None,
        on_data_count=None,
    ) -> list[RawPost]:
        """Phase 2: Scrape full post content starting from a given index.
        
        Args:
            profile_url: LinkedIn profile URL
            start_index: Index of the oldest post to start from
            max_posts: Maximum number of posts to scrape
            on_status: Callback for status messages
            on_progress: Callback for progress (current, total)
        
        Returns posts ordered from oldest to newest.
        """
        activity_url = self._build_activity_url(profile_url)

        if on_status:
            on_status(f"Navigating to {activity_url}")

        self._ensure_context(headless=True)
        self._page.goto(activity_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        if "login" in self._page.url:
            self.close()
            raise PermissionError("Not logged in. Please log in to LinkedIn first.")

        if should_stop and should_stop():
            self.close()
            return []

        if on_status:
            on_status("Scrolling to load posts...")

        def get_scrape_status(scrolls):
            try:
                count = self._page.evaluate("document.querySelectorAll('div.feed-shared-update-v2[data-urn*=\"activity\"]').length")
                
                # Check if we have enough posts (reached start_index)
                if count > start_index:
                    if on_status:
                        on_status(f"Found {count} posts (reached target {start_index + 1})")
                    if on_data_count:
                        on_data_count(count)
                    return True  # Stop scrolling
                
                if on_data_count:
                    on_data_count(count)
                return f"Found {count} posts (target: {start_index + 1})"
            except Exception:
                # Query evaluation failed, return empty status
                return ""

        self._scroll_feed(on_status=on_status, should_stop=should_stop, on_scroll=get_scrape_status)

        if should_stop and should_stop():
            self.close()
            return []

        if on_status:
            on_status("Extracting post content...")

        # Extract full post HTML and metadata
        posts_data = self._page.evaluate("""
            (startIndex) => {
                const posts = document.querySelectorAll('div.feed-shared-update-v2[data-urn*="activity"]');
                const results = [];
                // Actually, get all posts from startIndex down to 0 (oldest to newest on page = reversed)
                const subset = Array.from(posts).slice(0, startIndex + 1);
                subset.forEach((post, idx) => {
                    const urn = post.getAttribute('data-urn') || '';
                    const timeEl = post.querySelector('.update-components-actor__sub-description span.visually-hidden');
                    const dateText = timeEl ? timeEl.textContent.trim() : '';
                    results.push({
                        html: post.outerHTML,
                        dateText: dateText,
                        elementId: urn,
                        index: idx
                    });
                });
                return results;
            }
        """, start_index)

        self.close()

        # Reverse to get oldest first
        raw_posts = [
            RawPost(
                html=p["html"],
                date_text=p["dateText"],
                element_id=p["elementId"],
                index=p["index"]
            )
            for p in reversed(posts_data)
        ]

        # Limit to max_posts if provided; selection-based filtering (if any) happens earlier
        if max_posts is not None and max_posts > 0:
            raw_posts = raw_posts[:max_posts]

        total = len(raw_posts)
        if on_progress:
            on_progress(total, total)

        if on_status:
            on_status(f"Extracted {total} posts.")

        return raw_posts

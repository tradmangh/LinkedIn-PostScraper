"""LinkedIn post scraper using Playwright with persistent session."""

import re
import time
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


class LinkedInScraper:
    """Scrapes LinkedIn posts using Playwright with persistent browser session."""

    SCROLL_PAUSE_TIME = 2.0
    MAX_NO_CHANGE = 3

    def __init__(self, browser_state_dir: str):
        self.browser_state_dir = browser_state_dir
        self._playwright = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

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

    def close(self):
        """Close browser and cleanup."""
        if self._context:
            try:
                self._context.close()
            except Exception:
                pass
            self._context = None
            self._page = None
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

    def open_login(self, on_status=None):
        """Open LinkedIn login page for user to authenticate manually.
        
        The browser stays open until the user closes it or we detect login success.
        """
        if on_status:
            on_status("Opening browser for LinkedIn login...")

        self._ensure_context(headless=False)
        self._page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")

        if on_status:
            on_status("Please log in to LinkedIn in the browser window.\nClose the browser when done.")

        # Wait for the user to log in — we detect it by checking for the feed page
        try:
            self._page.wait_for_url("**/feed/**", timeout=300_000)  # 5 min timeout
            if on_status:
                on_status("Login successful! Session saved.")
        except Exception:
            # User might have navigated elsewhere after login, check if logged in
            if "feed" in self._page.url or "mynetwork" in self._page.url:
                if on_status:
                    on_status("Login successful! Session saved.")
            else:
                if on_status:
                    on_status("Login status unclear. Try scanning posts to verify.")

        # Close the context to save state
        self.close()

    def is_logged_in(self) -> bool:
        """Check if we have a saved session by attempting to load LinkedIn."""
        try:
            self._ensure_context(headless=True)
            self._page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=15000)
            time.sleep(2)
            logged_in = "feed" in self._page.url and "login" not in self._page.url
            self.close()
            return logged_in
        except Exception:
            self.close()
            return False

    def _build_activity_url(self, profile_url: str) -> str:
        """Build the recent activity URL from a profile URL."""
        # Normalize the URL
        profile_url = profile_url.rstrip("/")
        if "/recent-activity/" in profile_url:
            return profile_url
        # Remove any trailing path segments after the username
        match = re.match(r"(https://www\.linkedin\.com/in/[^/]+)", profile_url)
        if match:
            return f"{match.group(1)}/recent-activity/all/"
        return f"{profile_url}/recent-activity/all/"

    def _scroll_feed(self, max_scrolls: int = 0, on_status=None):
        """Scroll the feed to load posts. Returns when no new content loads."""
        last_height = self._page.evaluate("document.body.scrollHeight")
        scrolls = 0
        no_change_count = 0

        while True:
            self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(self.SCROLL_PAUSE_TIME)
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

            if on_status:
                on_status(f"Scrolling... ({scrolls} scrolls)")

    def scan_posts(self, profile_url: str, on_status=None) -> list[PostPreview]:
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

        if on_status:
            on_status("Page loaded. Scrolling to load all posts...")

        self._scroll_feed(on_status=on_status)

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
                console.log('Found posts:', posts.length);
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

        if on_status:
            on_status("Scrolling to load posts...")

        self._scroll_feed(on_status=on_status)

        if on_status:
            on_status("Extracting post content...")

        # Extract full post HTML and metadata
        posts_data = self._page.evaluate("""
            (startIndex) => {
                const posts = document.querySelectorAll('div.feed-shared-update-v2[data-urn*="activity"]');
                const results = [];
                for (let i = startIndex; i >= 0 && i < posts.length; i--) {
                    // We don't reverse here — we'll handle ordering in Python
                }
                // Actually, get all posts from startIndex down to 0 (oldest to newest on page = reversed)
                const subset = Array.from(posts).slice(0, startIndex + 1);
                subset.forEach((post, idx) => {
                    const urn = post.getAttribute('data-urn') || '';
                    const timeEl = post.querySelector('.update-components-actor__sub-description span.visually-hidden');
                    const dateText = timeEl ? timeEl.textContent.trim() : '';
                    results.push({
                        html: post.outerHTML,
                        dateText: dateText,
                        elementId: urn
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
            )
            for p in reversed(posts_data)
        ]

        # Limit to max_posts
        raw_posts = raw_posts[:max_posts]

        total = len(raw_posts)
        if on_progress:
            on_progress(total, total)

        if on_status:
            on_status(f"Extracted {total} posts.")

        return raw_posts

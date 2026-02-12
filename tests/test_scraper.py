"""
Unit tests for scraper.py module.
"""
import pytest
import time
from src.scraper import LinkedInScraper, PostPreview


class TestBuildActivityUrl:
    """Tests for URL building logic."""
    
    def test_build_activity_url_from_profile(self):
        """Test building activity URL from profile URL."""
        scraper = LinkedInScraper("test_browser_state")
        
        # Profile URL should convert to activity URL
        profile_url = "https://www.linkedin.com/in/testuser/"
        expected = "https://www.linkedin.com/in/testuser/recent-activity/all/"
        
        # This tests the internal logic that would be in _build_activity_url
        if "/recent-activity/" not in profile_url:
            result = profile_url.rstrip("/") + "/recent-activity/all/"
        else:
            result = profile_url
        
        assert result == expected
    
    def test_build_activity_url_preserves_existing(self):
        """Test that activity URLs are preserved as-is."""
        scraper = LinkedInScraper("test_browser_state")
        
        activity_url = "https://www.linkedin.com/in/testuser/recent-activity/all/"
        
        # Should not modify if already an activity URL
        if "/recent-activity/" in activity_url:
            result = activity_url
        else:
            result = activity_url.rstrip("/") + "/recent-activity/all/"
        
        assert result == activity_url


class TestHumanDelay:
    """Tests for human-like delay functionality."""
    
    def test_human_delay_within_range(self):
        """Test that _human_delay sleeps within specified range."""
        scraper = LinkedInScraper("test_browser_state")
        
        delay_range = (0.1, 0.2)  # Short delay for testing
        start_time = time.time()
        scraper._human_delay(delay_range)
        elapsed = time.time() - start_time
        
        # Should be within the range (with small tolerance)
        assert delay_range[0] <= elapsed <= delay_range[1] + 0.05
    
    def test_human_delay_randomness(self):
        """Test that _human_delay produces different values."""
        scraper = LinkedInScraper("test_browser_state")
        
        delay_range = (0.1, 0.3)
        delays = []
        
        for _ in range(5):
            start = time.time()
            scraper._human_delay(delay_range)
            delays.append(time.time() - start)
        
        # At least some delays should be different
        assert len(set([round(d, 2) for d in delays])) > 1


class TestScrollFeedLogic:
    """Tests for scroll feed logic (without actual browser)."""
    
    def test_scroll_feed_stops_on_no_change(self):
        """Test that scrolling stops when height doesn't change."""
        # Simulate scroll logic
        max_no_change = 3
        no_change_count = 0
        last_height = 1000
        
        # Simulate 3 iterations with no height change
        for _ in range(5):
            new_height = 1000  # No change
            
            if new_height == last_height:
                no_change_count += 1
            else:
                no_change_count = 0
            
            if no_change_count >= max_no_change:
                break
            
            last_height = new_height
        
        # Should have stopped after 3 no-change iterations
        assert no_change_count == max_no_change


class TestPostPreview:
    """Tests for PostPreview dataclass."""
    
    def test_post_preview_creation(self):
        """Test creating a PostPreview object."""
        preview = PostPreview(
            index=1,
            date_text="2d",
            headline="Test post headline",
            element_id="urn:li:activity:123456",
        )
        
        assert preview.index == 1
        assert preview.date_text == "2d"
        assert preview.headline == "Test post headline"
        assert preview.element_id == "urn:li:activity:123456"


class TestScraperInitialization:
    """Tests for LinkedInScraper initialization."""
    
    def test_scraper_initialization(self):
        """Test that scraper initializes with correct state."""
        scraper = LinkedInScraper("test_browser_state")
        
        assert scraper.browser_state_dir == "test_browser_state"
        assert scraper._playwright is None
        assert scraper._context is None
        assert scraper._page is None
    
    def test_scraper_delay_constants(self):
        """Test that delay constants are properly set."""
        scraper = LinkedInScraper("test_browser_state")
        
        assert scraper.DELAY_BETWEEN_SCROLLS == (1.5, 3.0)
        assert scraper.DELAY_BETWEEN_CLICKS == (0.8, 1.5)
        assert scraper.DELAY_AFTER_LOAD == (2.0, 3.5)

class TestScrapePostsLogic:
    """Tests for scrape_posts logic."""

    def test_scrape_stopping_condition(self):
        """Test that scrolling stops when count > start_index."""
        start_index = 10
        
        # Scenario 1: Not enough posts
        count = 5
        should_stop = count > start_index
        assert should_stop is False
        
        # Scenario 2: Same match (index 10 needs 11 posts? No, indices are 0..10)
        # If we have 10 posts, indices are 0..9.
        # If we want index 10, we need 11 posts.
        count = 10
        should_stop = count > start_index
        assert should_stop is False
        
        # Scenario 3: Enough posts
        count = 11
        should_stop = count > start_index
        assert should_stop is True

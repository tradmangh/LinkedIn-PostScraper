"""
Shared pytest fixtures for LinkedIn Post Scraper tests.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta


@pytest.fixture
def sample_post_html():
    """Sample LinkedIn post HTML for testing parser."""
    return """
    <div class="feed-shared-update-v2">
        <div class="update-components-actor">
            <span class="update-components-actor__name">
                <span class="visually-hidden">John Doe</span>
            </span>
            <span class="update-components-actor__sub-description">
                <span class="visually-hidden">2d</span>
            </span>
        </div>
        <div class="feed-shared-update-v2__description">
            This is a test post about LinkedIn scraping.
            <br>
            It has multiple lines.
        </div>
        <div class="update-components-image">
            <a href="https://example.com/image.jpg">Image</a>
        </div>
        <button aria-label="React Reaction">42</button>
        <button aria-label="Comment on post">7</button>
        <button aria-label="Repost this">3</button>
    </div>
    """


@pytest.fixture
def sample_post_data():
    """Expected Post object from sample_post_html."""
    from src.parser import Post
    today = datetime.today()
    two_days_ago = (today - timedelta(days=2)).strftime("%Y-%m-%d")
    
    return Post(
        author="John Doe",
        date=two_days_ago,
        date_raw="2d",
        content="This is a test post about LinkedIn scraping.\nIt has multiple lines.",
        post_url="",
        reactions=42,
        comments=7,
        reposts=3,
        media_type="Image",
        media_link="https://example.com/image.jpg",
        element_id="",
    )


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for file I/O tests."""
    temp_dir = tempfile.mkdtemp(prefix="linkedin_scraper_test_")
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_playwright_page(mocker):
    """Mock Playwright page object for scraper tests."""
    mock_page = mocker.Mock()
    mock_page.url = "https://www.linkedin.com/in/testuser/recent-activity/all/"
    mock_page.title.return_value = "Test User | LinkedIn"
    mock_page.content.return_value = "<html><body>Test content</body></html>"
    mock_page.evaluate.return_value = 1000  # Mock scroll height
    return mock_page


@pytest.fixture
def sample_linkedin_feed_html():
    """Sample LinkedIn feed HTML with multiple posts."""
    return """
    <div class="scaffold-finite-scroll__content">
        <div data-urn="urn:li:activity:1234567890" class="feed-shared-update-v2">
            <span class="update-components-actor__sub-description">
                <span class="visually-hidden">1w</span>
            </span>
            <div class="feed-shared-update-v2__description">First post</div>
        </div>
        <div data-urn="urn:li:activity:9876543210" class="feed-shared-update-v2">
            <span class="update-components-actor__sub-description">
                <span class="visually-hidden">3d</span>
            </span>
            <div class="feed-shared-update-v2__description">Second post</div>
        </div>
    </div>
    """

"""
Unit tests for parser.py module.
"""
import pytest
from datetime import datetime, timedelta
from src.parser import (
    parse_relative_date,
    parse_post,
    _convert_engagement_number,
    Post,
)


class TestParseRelativeDate:
    """Tests for parse_relative_date function."""
    
    def test_parse_hours(self):
        """Test parsing hours ago (e.g., '2h')."""
        result = parse_relative_date("2h")
        expected = (datetime.today() - timedelta(hours=2)).strftime("%Y-%m-%d")
        assert result == expected
    
    def test_parse_days(self):
        """Test parsing days ago (e.g., '3d')."""
        result = parse_relative_date("3d")
        expected = (datetime.today() - timedelta(days=3)).strftime("%Y-%m-%d")
        assert result == expected
    
    def test_parse_weeks(self):
        """Test parsing weeks ago (e.g., '2w')."""
        result = parse_relative_date("2w")
        expected = (datetime.today() - timedelta(weeks=2)).strftime("%Y-%m-%d")
        assert result == expected
    
    def test_parse_months(self):
        """Test parsing months ago (e.g., '1mo')."""
        result = parse_relative_date("1mo")
        expected = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")
        assert result == expected
    
    def test_parse_years(self):
        """Test parsing years ago (e.g., '1yr')."""
        result = parse_relative_date("1yr")
        expected = (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")
        assert result == expected
    
    def test_parse_with_bullet_separator(self):
        """Test parsing date with bullet separator (e.g., '2d •')."""
        result = parse_relative_date("2d •")
        expected = (datetime.today() - timedelta(days=2)).strftime("%Y-%m-%d")
        assert result == expected
    
    def test_parse_just_now(self):
        """Test parsing 'just now'."""
        result = parse_relative_date("just now")
        expected = datetime.today().strftime("%Y-%m-%d")
        assert result == expected
    
    def test_parse_empty_string(self):
        """Test parsing empty string returns today."""
        result = parse_relative_date("")
        expected = datetime.today().strftime("%Y-%m-%d")
        assert result == expected
    
    def test_parse_invalid_format(self):
        """Test parsing invalid format returns today with warning."""
        result = parse_relative_date("invalid date")
        expected = datetime.today().strftime("%Y-%m-%d")
        assert result == expected


class TestConvertEngagementNumber:
    """Tests for _convert_engagement_number function."""
    
    def test_convert_plain_number(self):
        """Test converting plain number string."""
        assert _convert_engagement_number("42") == 42
    
    def test_convert_thousands(self):
        """Test converting thousands (e.g., '1.2K')."""
        assert _convert_engagement_number("1.2K") == 1200
        assert _convert_engagement_number("5K") == 5000
    
    def test_convert_millions(self):
        """Test converting millions (e.g., '2.5M')."""
        assert _convert_engagement_number("2.5M") == 2500000
        assert _convert_engagement_number("1M") == 1000000
    
    def test_convert_with_commas(self):
        """Test converting numbers with commas."""
        assert _convert_engagement_number("1,234") == 1234
    
    def test_convert_empty_string(self):
        """Test converting empty string returns 0."""
        assert _convert_engagement_number("") == 0
    
    def test_convert_whitespace(self):
        """Test converting whitespace returns 0."""
        assert _convert_engagement_number("   ") == 0


class TestParsePost:
    """Tests for parse_post function."""
    
    def test_parse_post_extracts_author(self, sample_post_html):
        """Test that parse_post extracts author name correctly."""
        post = parse_post(sample_post_html)
        assert post.author == "John Doe"
    
    def test_parse_post_extracts_content(self, sample_post_html):
        """Test that parse_post extracts content correctly."""
        post = parse_post(sample_post_html)
        assert "test post about LinkedIn scraping" in post.content
        assert "multiple lines" in post.content
    
    def test_parse_post_extracts_date(self, sample_post_html):
        """Test that parse_post extracts and converts date."""
        post = parse_post(sample_post_html)
        expected = (datetime.today() - timedelta(days=2)).strftime("%Y-%m-%d")
        assert post.date == expected
        assert post.date_raw == "2d"
    
    def test_parse_post_extracts_engagement(self, sample_post_html):
        """Test that parse_post extracts engagement metrics."""
        post = parse_post(sample_post_html)
        assert post.reactions == 42
        assert post.comments == 7
        assert post.reposts == 3
    
    def test_parse_post_detects_media_type(self, sample_post_html):
        """Test that parse_post detects media type."""
        post = parse_post(sample_post_html)
        assert post.media_type == "Image"
        assert post.media_link == "https://example.com/image.jpg"
    
    def test_parse_post_handles_missing_fields(self):
        """Test that parse_post handles missing fields gracefully."""
        minimal_html = "<div class='feed-shared-update-v2'></div>"
        post = parse_post(minimal_html)
        
        assert post.author == ""
        assert post.content == ""
        assert post.reactions == 0
        assert post.comments == 0
        assert post.reposts == 0
        assert post.media_type == ""
    
    def test_parse_post_with_element_id(self):
        """Test that parse_post generates post URL from element ID."""
        html = "<div></div>"
        post = parse_post(html, element_id="urn:li:activity:1234567890")
        
        assert "1234567890" in post.post_url
        assert post.element_id == "urn:li:activity:1234567890"
    
    def test_parse_post_with_custom_date(self, sample_post_html):
        """Test that parse_post uses custom date_text parameter."""
        post = parse_post(sample_post_html, date_text="1w")
        expected = (datetime.today() - timedelta(weeks=1)).strftime("%Y-%m-%d")
        assert post.date == expected
        assert post.date_raw == "1w"

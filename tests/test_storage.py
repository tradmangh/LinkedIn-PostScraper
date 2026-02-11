"""
Unit tests for storage.py module.
"""
import pytest
import os
from pathlib import Path
from datetime import datetime
from src.storage import save_post, get_latest_post_date
from src.parser import Post


class TestSavePost:
    """Tests for save_post function."""
    
    def test_save_post_creates_file(self, temp_output_dir):
        """Test that save_post creates a markdown file."""
        post = Post(
            author="Test Author",
            date="2024-02-10",
            content="Test content",
            post_url="https://linkedin.com/post/123",
        )
        
        result = save_post(post, temp_output_dir)
        
        assert result is not None  # Should return filepath
        assert isinstance(result, str)  # Should be a string path
        # Check file was created
        files = list(Path(temp_output_dir).rglob("*.md"))
        assert len(files) == 1
    
    def test_save_post_generates_correct_filename(self, temp_output_dir):
        """Test that save_post generates filename with date and slug."""
        post = Post(
            author="Test Author",
            date="2024-02-10",
            content="This is a Test Post!",
            post_url="https://linkedin.com/post/123",
        )
        
        save_post(post, temp_output_dir)
        
        files = list(Path(temp_output_dir).rglob("2024-02-10_*.md"))
        assert len(files) == 1
        assert "this-is-a-test-post" in files[0].name.lower()
    
    def test_save_post_writes_frontmatter(self, temp_output_dir):
        """Test that save_post writes YAML frontmatter correctly."""
        post = Post(
            author="Test Author",
            date="2024-02-10",
            content="Test content",
            post_url="https://linkedin.com/post/123",
            reactions=42,
            comments=7,
        )
        
        save_post(post, temp_output_dir)
        
        files = list(Path(temp_output_dir).rglob("*.md"))
        content = files[0].read_text(encoding="utf-8")
        
        assert "---" in content
        assert "author: Test Author" in content
        assert "date: 2024-02-10" in content
        assert "source: https://linkedin.com/post/123" in content
        # Engagement metrics are in footer, not frontmatter
        assert "Reactions: 42" in content
        assert "Comments: 7" in content
    
    def test_save_post_skips_duplicates(self, temp_output_dir):
        """Test that save_post skips duplicate posts."""
        post = Post(
            author="Test Author",
            date="2024-02-10",
            content="Duplicate content",
            post_url="https://linkedin.com/post/123",
        )
        
        # Save first time
        result1 = save_post(post, temp_output_dir)
        assert result1 is not None  # Should return filepath
        
        # Try to save again
        result2 = save_post(post, temp_output_dir)
        assert result2 is None  # Should return None for duplicate
        
        # Should still only have one file
        files = list(Path(temp_output_dir).rglob("*.md"))
        assert len(files) == 1



class TestGetLatestPostDate:
    """Tests for get_latest_post_date function."""
    
    def test_get_latest_post_date_returns_most_recent(self, temp_output_dir):
        """Test that get_latest_post_date returns the most recent date."""
        # Create posts with different dates
        posts = [
            Post(author="Author", date="2024-01-15", content="Old post"),
            Post(author="Author", date="2024-02-10", content="Recent post"),
            Post(author="Author", date="2024-01-20", content="Middle post"),
        ]
        
        for post in posts:
            save_post(post, temp_output_dir)
        
        latest = get_latest_post_date(temp_output_dir)
        assert latest == "2024-02-10"
    
    def test_get_latest_post_date_handles_empty_folder(self, temp_output_dir):
        """Test that get_latest_post_date returns None for empty folder."""
        latest = get_latest_post_date(temp_output_dir)
        assert latest is None
    
    def test_get_latest_post_date_ignores_invalid_filenames(self, temp_output_dir):
        """Test that get_latest_post_date ignores files without date prefix."""
        # Create a valid post
        post = Post(author="Author", date="2024-02-10", content="Valid post")
        save_post(post, temp_output_dir)
        
        # Create an invalid file
        invalid_file = Path(temp_output_dir) / "invalid-filename.md"
        invalid_file.write_text("Invalid content")
        
        latest = get_latest_post_date(temp_output_dir)
        assert latest == "2024-02-10"

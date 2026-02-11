"""
Integration tests for LinkedIn Post Scraper.

These tests verify end-to-end workflows with mocked browser interactions.
"""
import pytest
from pathlib import Path
from src.parser import Post, parse_post
from src.storage import save_post, get_latest_post_date
from datetime import datetime, timedelta


class TestFullWorkflow:
    """Integration tests for complete scraping workflows."""
    
    def test_parse_and_save_workflow(self, sample_post_html, temp_output_dir):
        """Test complete workflow: parse HTML -> save to disk."""
        # Parse the HTML
        post = parse_post(sample_post_html)
        
        # Verify parsing worked
        assert post.author == "John Doe"
        assert "test post" in post.content.lower()
        
        # Save to disk
        filepath = save_post(post, temp_output_dir)
        
        # Verify file was created
        assert filepath is not None
        assert Path(filepath).exists()
        
        # Verify content
        content = Path(filepath).read_text(encoding="utf-8")
        assert "author: John Doe" in content
        assert "test post" in content.lower()
    
    def test_incremental_scraping_skips_existing(self, temp_output_dir):
        """Test that incremental scraping only processes new posts."""
        # Save some old posts
        old_posts = [
            Post(author="Author", date="2024-01-15", content="Old post 1", post_url="https://linkedin.com/post/1"),
            Post(author="Author", date="2024-01-20", content="Old post 2", post_url="https://linkedin.com/post/2"),
        ]
        
        for post in old_posts:
            save_post(post, temp_output_dir)
        
        # Get latest date
        latest_date = get_latest_post_date(temp_output_dir)
        assert latest_date == "2024-01-20"
        
        # Simulate new posts (some old, some new)
        all_posts = [
            Post(author="Author", date="2024-01-10", content="Very old", post_url="https://linkedin.com/post/0"),
            Post(author="Author", date="2024-01-15", content="Old post 1", post_url="https://linkedin.com/post/1"),  # Duplicate
            Post(author="Author", date="2024-02-01", content="New post 1", post_url="https://linkedin.com/post/3"),
            Post(author="Author", date="2024-02-05", content="New post 2", post_url="https://linkedin.com/post/4"),
        ]
        
        # Filter to only new posts (date > latest_date)
        new_posts = [p for p in all_posts if p.date > latest_date]
        
        # Should only have 2 new posts
        assert len(new_posts) == 2
        assert all(p.date > "2024-01-20" for p in new_posts)
    
    def test_multiple_profiles_separate_folders(self, temp_output_dir):
        """Test that posts from different profiles go to separate folders."""
        # Don't create subfolders manually - save_post does this automatically
        post1 = Post(author="John Doe", date="2024-02-10", content="John's post", post_url="https://linkedin.com/post/1")
        post2 = Post(author="Jane Smith", date="2024-02-11", content="Jane's post", post_url="https://linkedin.com/post/2")
        
        save_post(post1, temp_output_dir)
        save_post(post2, temp_output_dir)
        
        # Verify author-specific subfolders were created
        person1_folder = Path(temp_output_dir) / "john-doe"
        person2_folder = Path(temp_output_dir) / "jane-smith"
        
        assert person1_folder.exists()
        assert person2_folder.exists()
        
        person1_files = list(person1_folder.glob("*.md"))
        person2_files = list(person2_folder.glob("*.md"))
        
        assert len(person1_files) == 1
        assert len(person2_files) == 1
        
        assert "John's post" in person1_files[0].read_text()
        assert "Jane's post" in person2_files[0].read_text()


class TestDataIntegrity:
    """Tests for data integrity across parse -> save -> read cycle."""
    
    def test_engagement_metrics_preserved(self, temp_output_dir):
        """Test that engagement metrics are preserved through save/load."""
        post = Post(
            author="Test Author",
            date="2024-02-10",
            content="Test content",
            post_url="https://linkedin.com/post/123",
            reactions=1234,
            comments=56,
            reposts=78,
        )
        
        filepath = save_post(post, temp_output_dir)
        content = Path(filepath).read_text(encoding="utf-8")
        
        # Verify engagement in footer
        assert "Reactions: 1234" in content or "1234" in content
        assert "Comments: 56" in content or "56" in content
        assert "Reposts: 78" in content or "78" in content
    
    def test_media_links_preserved(self, temp_output_dir):
        """Test that media links are preserved."""
        post = Post(
            author="Test Author",
            date="2024-02-10",
            content="Post with image",
            post_url="https://linkedin.com/post/123",
            media_type="Image",
            media_link="https://example.com/image.jpg",
        )
        
        filepath = save_post(post, temp_output_dir)
        content = Path(filepath).read_text(encoding="utf-8")
        
        assert "Image" in content
        assert "https://example.com/image.jpg" in content

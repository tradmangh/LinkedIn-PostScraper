"""Storage module for saving LinkedIn posts as markdown files."""

import os
import re
import logging
from typing import Optional
from slugify import slugify

from .parser import Post

logger = logging.getLogger(__name__)


def _make_slug(text: str, max_length: int = 50) -> str:
    """Create a URL-safe slug from text."""
    if not text:
        return "post"
    # Take first line only
    first_line = text.split("\n")[0].strip()
    # Truncate before slugifying
    truncated = first_line[:max_length]
    slug = slugify(truncated, max_length=max_length)
    return slug or "post"


def _build_filename(post: Post) -> str:
    """Build a markdown filename from post date and content slug."""
    date_part = post.date or "unknown-date"
    slug = _make_slug(post.content)
    return f"{date_part}_{slug}.md"


def _post_to_markdown(post: Post) -> str:
    """Convert a Post object to a markdown string with YAML frontmatter."""
    lines = [
        "---",
        f"author: {post.author}",
        f"date: {post.date}",
        f"source: {post.post_url}",
    ]

    if post.media_type:
        lines.append(f"media_type: {post.media_type}")

    lines.append("---")
    lines.append("")

    # Post content
    if post.content:
        lines.append(post.content)
    else:
        lines.append("*(No text content)*")

    lines.append("")

    # Media link if present
    if post.media_link:
        lines.append(f"**Media:** [{post.media_type or 'Link'}]({post.media_link})")
        lines.append("")

    # Engagement footer
    engagement_parts = []
    if post.reactions:
        engagement_parts.append(f"Reactions: {post.reactions}")
    if post.comments:
        engagement_parts.append(f"Comments: {post.comments}")
    if post.reposts:
        engagement_parts.append(f"Reposts: {post.reposts}")

    if engagement_parts:
        lines.append("---")
        lines.append(f"*{' | '.join(engagement_parts)}*")

    lines.append("")
    return "\n".join(lines)


def _is_duplicate(output_folder: str, post: Post) -> bool:
    """Check if a post has already been saved (matched by source URL in frontmatter)."""
    if not post.post_url:
        return False

    # Walk the output folder and check frontmatter
    for root, dirs, files in os.walk(output_folder):
        for f in files:
            if f.endswith(".md"):
                filepath = os.path.join(root, f)
                try:
                    with open(filepath, "r", encoding="utf-8") as fh:
                        content = fh.read(500)  # Only read first 500 chars for frontmatter
                        if post.post_url in content:
                            return True
                except Exception:
                    continue
    return False


def save_post(post: Post, output_folder: str, skip_duplicates: bool = True) -> Optional[str]:
    """Save a single post as a markdown file.
    
    Args:
        post: Parsed Post object
        output_folder: Root output folder path
        skip_duplicates: If True, skip posts that already exist
    
    Returns:
        Path to the saved file, or None if skipped.
    """
    os.makedirs(output_folder, exist_ok=True)

    if skip_duplicates and _is_duplicate(output_folder, post):
        logger.info(f"Skipping duplicate post: {post.post_url}")
        return None

    filename = _build_filename(post)
    filepath = os.path.join(output_folder, filename)

    # Handle filename collision
    counter = 1
    base, ext = os.path.splitext(filepath)
    while os.path.exists(filepath):
        filepath = f"{base}_{counter}{ext}"
        counter += 1

    markdown_content = _post_to_markdown(post)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    logger.info(f"Saved post to {filepath}")
    return filepath


def save_posts(posts: list[Post], output_folder: str, on_progress=None) -> list[str]:
    """Save multiple posts as markdown files.
    
    Args:
        posts: List of parsed Post objects
        output_folder: Root output folder path
        on_progress: Callback (current, total, filepath)
    
    Returns:
        List of saved file paths.
    """
    saved = []
    total = len(posts)

    for i, post in enumerate(posts):
        filepath = save_post(post, output_folder)
        if filepath:
            saved.append(filepath)
        if on_progress:
            on_progress(i + 1, total, filepath)

    return saved

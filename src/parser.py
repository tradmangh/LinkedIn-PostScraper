"""Parser for LinkedIn post HTML content."""

import re
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class Post:
    """Structured LinkedIn post data."""
    author: str = ""
    date: str = ""           # YYYY-MM-DD
    date_raw: str = ""       # Original date text from LinkedIn (e.g., "2w")
    content: str = ""
    post_url: str = ""
    reactions: int = 0
    comments: int = 0
    reposts: int = 0
    media_type: str = ""     # Image, Video, Article, etc.
    media_link: str = ""
    element_id: str = ""     # LinkedIn URN


def parse_relative_date(date_text: str) -> str:
    """Convert LinkedIn's relative date text to YYYY-MM-DD format.
    
    Handles formats like: '2h', '3d', '1w', '2mo', '1yr', '2h •', etc.
    """
    if not date_text:
        return datetime.today().strftime("%Y-%m-%d")

    # Clean up the text — remove bullet/dot separators and extra whitespace
    cleaned = date_text.strip().split("•")[0].strip().split("·")[0].strip()
    cleaned = cleaned.lower()

    today = datetime.today()

    # Try to match relative date patterns
    # Patterns: 2h, 3d, 1w, 2mo, 1yr, "just now", "2 hours", "3 days", etc.
    patterns = [
        (r"just\s*now", lambda m: today),
        (r"(\d+)\s*s(?:ec|econds?)?", lambda m: today),
        (r"(\d+)\s*m(?:in|inutes?)?(?!\w*o)", lambda m: today),
        (r"(\d+)\s*h(?:r|ours?)?", lambda m: today - timedelta(hours=int(m.group(1)))),
        (r"(\d+)\s*d(?:ays?)?", lambda m: today - timedelta(days=int(m.group(1)))),
        (r"(\d+)\s*w(?:k|eeks?)?", lambda m: today - timedelta(weeks=int(m.group(1)))),
        (r"(\d+)\s*mo(?:nths?)?", lambda m: today - timedelta(days=int(m.group(1)) * 30)),
        (r"(\d+)\s*yr?(?:ears?)?", lambda m: today - timedelta(days=int(m.group(1)) * 365)),
    ]

    for pattern, calc in patterns:
        match = re.match(pattern, cleaned)
        if match:
            return calc(match).strftime("%Y-%m-%d")

    # If it looks like a date already, try to parse it
    for fmt in ["%Y-%m-%d", "%b %d, %Y", "%d %b %Y", "%m-%d-%Y"]:
        try:
            return datetime.strptime(cleaned, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Fallback — return today
    logger.warning(f"Could not parse date: '{date_text}', using today's date")
    return today.strftime("%Y-%m-%d")


def _convert_engagement_number(text: str) -> int:
    """Convert abbreviated numbers like '1.2K' to integers."""
    text = text.strip().replace(",", "")
    if not text:
        return 0
    text_upper = text.upper()
    try:
        if "K" in text_upper:
            return int(float(text_upper.replace("K", "")) * 1000)
        elif "M" in text_upper:
            return int(float(text_upper.replace("M", "")) * 1000000)
        else:
            return int(re.sub(r"[^\d]", "", text) or 0)
    except (ValueError, TypeError):
        return 0


def _get_text(soup, selector: str, attrs: dict) -> str:
    """Safely extract text from a BeautifulSoup element."""
    try:
        el = soup.find(selector, attrs)
        if el:
            return el.get_text(strip=True)
    except Exception:
        pass
    return ""


def _extract_media(soup) -> tuple[str, str]:
    """Extract media type and link from a post."""
    media_checks = [
        ("div", {"class": "update-components-video"}, "Video"),
        ("div", {"class": "update-components-linkedin-video"}, "Video"),
        ("div", {"class": "update-components-image"}, "Image"),
        ("article", {"class": "update-components-article"}, "Article"),
        ("div", {"class": "feed-shared-external-video__meta"}, "YouTube Video"),
        ("div", {"class": re.compile(r"feed-shared-mini-update-v2")}, "Shared Post"),
        ("div", {"class": re.compile(r"feed-shared-poll")}, "Poll"),
    ]

    for tag, attrs, media_type in media_checks:
        el = soup.find(tag, attrs)
        if el:
            link_el = el.find("a", href=True)
            link = link_el["href"] if link_el else ""
            return media_type, link

    return "", ""


def _extract_engagement(soup, keyword: str) -> int:
    """Extract engagement count (reactions/comments/reposts) from post HTML."""
    try:
        buttons = soup.find_all(
            lambda tag: tag.name == "button"
            and "aria-label" in tag.attrs
            and keyword in tag["aria-label"].lower()
        )
        if buttons:
            # Sometimes there are duplicate buttons; use the last one with text
            for btn in reversed(buttons):
                text = btn.get_text(strip=True)
                if text:
                    return _convert_engagement_number(text)
    except Exception:
        pass
    return 0


def parse_post(raw_html: str, date_text: str = "", element_id: str = "") -> Post:
    """Parse a raw LinkedIn post HTML into a structured Post object."""
    soup = BeautifulSoup(raw_html, "html.parser")

    # Author
    author = ""
    author_el = soup.find("span", {"class": re.compile(r"update-components-actor__name")})
    if author_el:
        # Get the visually-hidden span inside for clean text
        hidden = author_el.find("span", {"class": "visually-hidden"})
        if hidden:
            author = hidden.get_text(strip=True)
        else:
            author = author_el.get_text(strip=True)

    # Date
    if not date_text:
        time_el = soup.find("span", {"class": re.compile(r"update-components-actor__sub-description")})
        if time_el:
            hidden = time_el.find("span", {"class": "visually-hidden"})
            date_text = hidden.get_text(strip=True) if hidden else time_el.get_text(strip=True)

    post_date = parse_relative_date(date_text)

    # Content text
    content = ""
    content_el = soup.find("div", {"class": re.compile(r"feed-shared-update-v2__description")})
    if content_el:
        # Get text preserving some structure
        for br in content_el.find_all("br"):
            br.replace_with("\n")
        content = content_el.get_text(strip=False).strip()
    if not content:
        # Fallback: commentary block
        commentary_el = soup.find("div", {"class": re.compile(r"feed-shared-update-v2__commentary")})
        if commentary_el:
            for br in commentary_el.find_all("br"):
                br.replace_with("\n")
            content = commentary_el.get_text(strip=False).strip()
    if not content:
        text_el = soup.find("span", {"class": re.compile(r"update-components-text")})
        if text_el:
            for br in text_el.find_all("br"):
                br.replace_with("\n")
            content = text_el.get_text(strip=False).strip()

    # Post URL from URN
    post_url = ""
    if element_id:
        # Extract activity ID from URN like "urn:li:activity:1234567890"
        urn_match = re.search(r"activity:(\d+)", element_id)
        if urn_match:
            post_url = f"https://www.linkedin.com/feed/update/urn:li:activity:{urn_match.group(1)}/"

    # Media
    media_type, media_link = _extract_media(soup)

    # Engagement
    reactions = _extract_engagement(soup, "reaction")
    comments = _extract_engagement(soup, "comment")
    reposts = _extract_engagement(soup, "repost")

    return Post(
        author=author,
        date=post_date,
        date_raw=date_text,
        content=content,
        post_url=post_url,
        reactions=reactions,
        comments=comments,
        reposts=reposts,
        media_type=media_type,
        media_link=media_link,
        element_id=element_id,
    )

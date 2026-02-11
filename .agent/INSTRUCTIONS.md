# Antigravity Instructions for LinkedIn Post Scraper

This document provides comprehensive guidelines for AI agents (Google Antigravity, Claude, etc.) working on the LinkedIn Post Scraper project.

## Project Overview

**Purpose**: Desktop application that scrapes LinkedIn posts from activity feeds and saves them as organized markdown files.

**Tech Stack**:

- **Language**: Python 3.8+
- **Browser Automation**: Playwright (persistent contexts for session management)
- **HTML Parsing**: BeautifulSoup4
- **UI Framework**: CustomTkinter (modern dark mode interface)
- **File Format**: Markdown with YAML frontmatter

**Key Design Principles**:

1. **Separation of concerns**: Scraping, parsing, storage, and UI are separate modules
2. **Two-phase workflow**: Scan posts first (preview), then scrape selected posts
3. **Human-like behavior**: Random delays to avoid detection
4. **Session persistence**: Login once, reuse cookies via Playwright persistent context

## Project Structure

```
LinkedIn-PostScraper/
├── main.py                 # Entry point - launches CustomTkinter app
├── requirements.txt        # Dependencies
├── config.json            # User settings (created on first run)
├── src/
│   ├── config.py          # Config load/save utilities
│   ├── scraper.py         # Playwright scraping logic
│   ├── parser.py          # HTML → Post dataclass parsing
│   ├── storage.py         # Markdown file I/O
│   └── ui/
│       ├── app.py         # Main window
│       ├── scrape_frame.py # Scraping tab
│       └── browse_frame.py # Browse tab
├── browser_state/         # Playwright session data (gitignored)
├── output/                # Saved posts (gitignored)
└── debug/                 # HTML snapshots for debugging (gitignored)
```

## Module Responsibilities

### `scraper.py` - Web Scraping

- **Class**: `LinkedInScraper`
- **Key Methods**:
  - `open_login()`: Opens browser for manual LinkedIn login
  - `scan_posts()`: Phase 1 - Returns list of `PostPreview` objects
  - `scrape_posts()`: Phase 2 - Downloads full HTML for selected posts
  - `_scroll_feed()`: Scrolls page to load all posts
  - `_human_delay()`: Random delays to simulate human behavior

- **Important Constants**:
  - `DELAY_BETWEEN_SCROLLS = (1.5, 3.0)` - Random delay range
  - `DELAY_AFTER_LOAD = (2.0, 3.5)` - Delay after page loads
  - `DELAY_BETWEEN_CLICKS = (0.8, 1.5)` - Delay between clicks

- **Session Management**: Uses `launch_persistent_context()` with `browser_state_dir`

### `parser.py` - HTML Parsing

- **Dataclass**: `Post` - Structured post data
- **Key Function**: `parse_post(html, date_text, element_id)` → `Post`
- **Extracts**:
  - Author name
  - Post content (text)
  - Date (converts relative dates like "2h" to YYYY-MM-DD)
  - Engagement metrics (reactions, comments, reposts)
  - Media type (Image, Video, Document, Poll, Article, None)
  - Source URL

- **Date Parsing**: `parse_relative_date()` converts LinkedIn's relative dates

### `storage.py` - File Operations

- **Key Functions**:
  - `save_post()`: Saves single post as markdown
  - `save_posts()`: Batch save with progress callback
  - `get_latest_post_date()`: Finds most recent post in folder (for incremental scraping)
  - `_is_duplicate()`: Checks if post already exists by URL

- **Filename Format**: `YYYY-MM-DD_slug.md` (using `python-slugify`)
- **Frontmatter**: YAML with author, date, source, media_type, reactions, comments

### `ui/` - User Interface

- **app.py**: Main window, tabview, About menu
- **scrape_frame.py**: URL input, login, scan, post list, scrape controls
- **browse_frame.py**: File browser and markdown preview

- **Threading**: All long operations run in background threads
- **UI Updates**: Use `self.after(0, lambda: ...)` for thread-safe updates

## Development Guidelines

### Code Style

```python
# Use type hints
def parse_post(html: str, date_text: str, element_id: str) -> Post:
    ...

# Docstrings for all public functions
def save_post(post: Post, output_folder: str) -> Optional[str]:
    """Save a single post as a markdown file.
    
    Args:
        post: Post object to save
        output_folder: Directory to save to
        
    Returns:
        Path to saved file, or None if duplicate
    """
```

### Error Handling

- **Specific exceptions**: Catch `PermissionError` for login issues
- **User-friendly messages**: "Not logged in. Please log in first." not "403 Forbidden"
- **Debug snapshots**: Save HTML to `debug/` when selectors fail

### Scraping Best Practices

1. **Always use human-like delays**: Call `self._human_delay(range)` between actions
2. **Check for login redirects**: `if "login" in self._page.url: raise PermissionError(...)`
3. **Save debug snapshots**: When selectors fail, save HTML for inspection
4. **Multiple fallback selectors**: LinkedIn changes HTML frequently

### UI Threading Rules

```python
# ❌ WRONG - Direct UI update from thread
def worker():
    self.status_label.configure(text="Done")  # Will crash!

# ✅ CORRECT - Use self.after()
def worker():
    self.after(0, lambda: self.status_label.configure(text="Done"))

# Or use helper method
def _set_status(self, msg: str):
    self.after(0, lambda: self.status_label.configure(text=msg))
```

## Common Tasks

### Adding a New Field to Posts

1. **Update `Post` dataclass** in `parser.py`:

```python
@dataclass
class Post:
    # ... existing fields ...
    new_field: str = ""
```

1. **Extract in `parse_post()`**:

```python
post.new_field = soup.select_one(".new-selector")?.get_text(strip=True) or ""
```

1. **Update markdown frontmatter** in `storage.py`:

```python
frontmatter = f"""---
author: {post.author}
new_field: {post.new_field}
---"""
```

### Debugging Selector Issues

1. **Check debug HTML**: `debug/linkedin_page.html` is saved on every scan
2. **Inspect selectors**: Use browser DevTools on saved HTML
3. **Add logging**:

```python
logger.info(f"Found {len(posts)} posts with selector: {selector}")
```

### Adding UI Features

1. **Update frame class** (`scrape_frame.py` or `browse_frame.py`)
2. **Use grid layout**: `widget.grid(row=X, column=Y, sticky="ew")`
3. **Long operations → threads**:

```python
def _on_button_click(self):
    self._set_buttons(False)  # Disable during work
    
    def worker():
        try:
            # Do work...
            self._set_status("Done!")
        finally:
            self._set_buttons(True)  # Re-enable
    
    threading.Thread(target=worker, daemon=True).start()
```

## Testing Guidelines

### TDD Principle

**Always write tests BEFORE implementing features.**

1. Write failing test
2. Implement minimal code to pass
3. Refactor while keeping tests green
4. Repeat

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_parser.py

# Run specific test
pytest tests/test_parser.py::test_parse_relative_date_hours

# Run in verbose mode
pytest -v
```

### Coverage Target

- **Minimum**: 80%+ code coverage for all modules
- **Check coverage**: Open `htmlcov/index.html` after running with `--cov-report=html`

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_parser.py           # Parser unit tests
├── test_storage.py          # Storage unit tests
├── test_scraper.py          # Scraper unit tests
└── test_integration.py      # End-to-end tests
```

### Writing Tests

```python
import pytest
from src.parser import parse_post, Post

def test_parse_post_extracts_author(sample_post_html):
    """Test that parse_post extracts author name correctly."""
    post = parse_post(sample_post_html)
    assert post.author == "John Doe"
```

### CI/CD

- **GitHub Actions** runs tests automatically on every push
- **Coverage reports** uploaded to Codecov
- **Pull requests** require passing tests

## Manual Testing Checklist

Before committing changes:

- [ ] **Automated tests**: `pytest` (all tests pass)
- [ ] **Import test**: `python -c "from src import scraper, parser, storage, ui"`
- [ ] **Launch test**: `python main.py` (window opens without errors)
- [ ] **Login test**: Click Login → authenticate → session saved
- [ ] **Scan test**: Enter URL → Scan Posts → previews appear
- [ ] **Scrape test**: Select posts → Scrape → markdown files created
- [ ] **Browse test**: Switch to Browse tab → files listed → preview works
- [ ] **Multiple profiles**: Test with different LinkedIn profiles
- [ ] **Incremental scraping**: Re-scan same profile → only new posts

## Git Workflow

```bash
# Make changes
git add -A
git commit -m "feat: descriptive message

- Bullet point of change 1
- Bullet point of change 2"

# Update CHANGELOG.md under [Unreleased]
# Push to GitHub
git push
```

### Commit Message Format

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `refactor:` - Code restructuring
- `test:` - Adding tests
- `chore:` - Maintenance

## Known Issues & Gotchas

### LinkedIn Selector Changes

**Problem**: LinkedIn frequently updates HTML structure, breaking selectors.

**Solution**:

1. Check `debug/linkedin_page.html` for current structure
2. Update selectors in `scraper.py` and `parser.py`
3. Use multiple fallback selectors when possible

### Rate Limiting

**Problem**: Scraping too fast triggers LinkedIn's anti-bot measures.

**Solution**:

- Human-like delays are already implemented
- Don't reduce delay ranges below current values
- If blocked, increase delays: `DELAY_BETWEEN_SCROLLS = (2.5, 4.0)`

### Windows Path Issues

**Problem**: Windows uses backslashes, can cause path errors.

**Solution**:

```python
import os
path = os.path.join(base, "folder", "file.md")  # Cross-platform
```

## Future Enhancements (v2.0)

Planned features documented in `CHANGELOG.md`:

1. **Per-person subfolders**: `output/JohnDoe/`, `output/JaneSmith/`
2. **Incremental scraping**: Only download new posts since last scrape
3. **Year-based grouping**: Collapsible sections in UI by year
4. **Engagement columns**: Show reactions/comments in post list
5. **Select All button**: Bulk selection control
6. **AI topic tagging**: Google Gemini integration for auto-categorization

## Resources

- **Playwright Docs**: <https://playwright.dev/python/>
- **CustomTkinter Docs**: <https://customtkinter.tomschimansky.com/>
- **BeautifulSoup Docs**: <https://www.crummy.com/software/BeautifulSoup/bs4/doc/>
- **Project Repo**: <https://github.com/tradmangh/LinkedIn-PostScraper>

## Questions?

When uncertain:

1. Check existing code patterns in the module
2. Review `CHANGELOG.md` for context on recent changes
3. Test changes with `python main.py` before committing
4. Preserve human-like delays and session persistence

---

**Remember**: This tool is for personal archival. Respect LinkedIn's ToS and rate limits. The scraper includes delays to be respectful of LinkedIn's servers.

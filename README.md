# LinkedIn Post Scraper

A Python desktop application that scrapes LinkedIn posts from a person's activity feed and saves them as markdown files.

## Features

- **Playwright-based scraping** with persistent browser session (login once, reuse cookies)
- **Two-phase workflow**: Scan posts → Select range → Scrape
- **Markdown output** with YAML frontmatter
- **Modern Windows UI** using CustomTkinter
- **Post browser** to view saved posts

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
python -m playwright install chromium
```

## Usage

```bash
python main.py
```

1. **Login**: Click "🔑 Login" → log in to LinkedIn in the browser → session is saved
2. **Scan**: Paste a profile URL → Click "📋 Scan Posts"
3. **Select**: Check the posts you want to scrape
4. **Scrape**: Click "⬇ Scrape Selected"
5. **Browse**: View saved posts in the Browse tab

## Output Format

Posts are saved as `YYYY-MM-DD_slug.md`:

```markdown
---
author: Name
date: 2024-02-12
source: https://linkedin.com/...
media_type: Image
---

Post content...

---
*Reactions: 142 | Comments: 23 | Reposts: 5*
```

## Project Structure

```
LinkedIn-PostScraper/
├── main.py              # Entry point
├── requirements.txt     # Dependencies
├── src/
│   ├── config.py        # Config management
│   ├── scraper.py       # Playwright scraper
│   ├── parser.py        # HTML parser
│   ├── storage.py       # Markdown writer
│   └── ui/              # CustomTkinter UI
└── output/              # Saved posts (gitignored)
```

## License

MIT

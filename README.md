# LinkedIn Post Scraper

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Python desktop application that scrapes LinkedIn posts from activity feeds and saves them as organized markdown files. Perfect for archiving thought leadership content, building personal knowledge bases, or analyzing posting patterns.

## ✨ Features

### Core Functionality

- 🔐 **Persistent Sessions** - Login once, scrape forever (Playwright saves cookies)
- 📋 **Smart Scanning** - Preview posts before downloading
- 🎯 **Selective Scraping** - Choose exactly which posts to save
- 📁 **Per-Person Organization** - Automatic subfolders for each LinkedIn profile
- 🔄 **Incremental Updates** - Only scrape new posts, skip duplicates
- 📊 **Engagement Metrics** - Track reactions, comments, and reposts

### User Experience

- 🎨 **Modern UI** - Clean CustomTkinter interface with dark mode
- 📅 **Year Grouping** - Posts organized by year with collapsible sections
- 🔍 **Built-in Browser** - Preview saved posts without leaving the app
- ⚡ **Bulk Actions** - Select/deselect all posts with one click
- 📂 **Quick Access** - Open output folders directly from the UI

### Output

- 📝 **Markdown Format** - Clean, portable, version-control friendly
- 🏷️ **Rich Metadata** - YAML frontmatter with author, date, source, engagement
- 🔗 **Preserved Links** - Original post URLs for reference
- 🖼️ **Media Detection** - Identifies images, videos, documents, polls

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Windows (tested), macOS/Linux (should work)

### Installation

```bash
# Clone the repository
git clone https://github.com/tradmangh/LinkedIn-PostScraper.git
cd LinkedIn-PostScraper

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
python -m playwright install chromium
```

### Usage

```bash
python main.py
```

#### Workflow

1. **🔑 Login** - Click "Login" button → authenticate in browser → session saved
2. **📋 Scan** - Paste LinkedIn profile URL → Click "Scan Posts"
3. **✅ Select** - Review posts, check ones you want (or use "Select All")
4. **⬇️ Scrape** - Click "Scrape Selected" → watch progress bar
5. **📖 Browse** - Switch to Browse tab to view saved posts

## 📄 Output Format

Posts are saved as `YYYY-MM-DD_slug.md` in person-specific subfolders:

```
output/
├── JohnDoe/
│   ├── 2024-02-12_ai-revolution-is-here.md
│   └── 2024-02-10_startup-lessons-learned.md
└── JaneSmith/
    └── 2024-02-11_product-management-tips.md
```

### Markdown Structure

```markdown
---
author: John Doe
date: 2024-02-12
source: https://www.linkedin.com/feed/update/urn:li:activity:123456789/
media_type: Image
reactions: 142
comments: 23
---

The AI revolution isn't coming—it's already here.

Here's what I learned building AI products for the past 3 years...

---
*Reactions: 142 | Comments: 23 | Reposts: 5*
```

## 🏗️ Project Structure

```
LinkedIn-PostScraper/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── config.json            # User configuration (created on first run)
├── LICENSE                # MIT License
├── CHANGELOG.md           # Version history
├── README.md              # This file
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── scraper.py         # Playwright web scraping logic
│   ├── parser.py          # HTML → structured data parsing
│   ├── storage.py         # Markdown file I/O
│   └── ui/
│       ├── __init__.py
│       ├── app.py         # Main application window
│       ├── scrape_frame.py # Scraping tab UI
│       └── browse_frame.py # Browse tab UI
├── browser_state/         # Playwright session data (gitignored)
├── output/                # Saved posts (gitignored)
└── debug/                 # Debug HTML snapshots (gitignored)
```

## ⚙️ Configuration

Edit `config.json` to customize:

```json
{
  "output_folder": "output",
  "browser_state_dir": "browser_state",
  "max_posts": 50
}
```

## 🤝 Contributing

Contributions are welcome! This project was co-created by:

- **Google Antigravity** (AI Agent)
- **Anthropic Claude Opus 4.6 & Sonnet 4.5** (AI Models)

### Development Guidelines

1. **Code Style** - Follow PEP 8, use type hints
2. **Testing** - Test with multiple LinkedIn profiles
3. **Commits** - Descriptive messages, logical units of work
4. **Changelog** - Update `CHANGELOG.md` for user-facing changes

See [CHANGELOG.md](CHANGELOG.md) for detailed AI agent instructions.

## 📋 Roadmap

- [ ] AI-powered topic tagging (Google Gemini integration)
- [ ] Automatic folder organization by topic
- [ ] Export to PDF/HTML
- [ ] Multi-profile batch scraping
- [ ] Scheduled automatic updates
- [ ] Search and filter saved posts

## ⚠️ Disclaimer

This tool is for personal archival purposes only. Please respect LinkedIn's Terms of Service and rate limits. The scraper includes human-like delays to avoid detection, but use responsibly.

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Playwright](https://playwright.dev/) for reliable browser automation
- UI powered by [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- Parsing with [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)

---

**Made with ❤️ by AI agents helping humans organize knowledge**

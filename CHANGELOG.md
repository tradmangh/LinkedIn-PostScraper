# Changelog

All notable changes to LinkedIn Post Scraper will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned for v2.0

- Per-person output subfolders to organize posts by LinkedIn profile
- Incremental scraping to avoid re-downloading existing posts
- Year-based collapsible post groups in UI (current year expanded by default)
- Select All / Deselect All button for bulk post selection
- Open in Explorer button for quick folder access
- AI-powered topic tagging (Google Gemini integration)

## [1.2.0] - 2026-02-11

### Added

- **Cross-platform executables** for Windows, macOS, and Linux using PyInstaller
- **Two build variants**:
  - **Standalone** (~50-80 MB): Downloads browser on first run
  - **Full Bundle** (~350-400 MB): Browser included for offline use
- **Automated builds** via GitHub Actions on release tags
- **Build scripts** for local compilation on each platform
- **BUILDING.md** developer guide for creating executables
- PyInstaller spec files for both build variants
- Application icon placeholders (Windows .ico, macOS .icns, Linux .png)

### Changed

- Updated requirements.txt to include PyInstaller dependency
- Enhanced documentation with download and installation instructions

## [1.1.0] - 2026-02-11

### Added

- **Automated test suite** with pytest, pytest-mock, and pytest-cov
- **40+ unit and integration tests** covering parser, storage, and scraper modules
- **Test fixtures** for LinkedIn HTML samples and mock Playwright pages
- **pytest configuration** with coverage reporting (80%+ target)
- **GitHub Actions CI/CD** workflow for automated testing on push
- **TDD guidelines** in `.agent/INSTRUCTIONS.md` for future development
- Engagement metrics (reactions, comments) in Post dataclass and markdown frontmatter
- Human-like scraping delays to avoid detection (1.5-3s between scrolls, 2-3.5s after loads)

### Changed

- Enhanced `.agent/INSTRUCTIONS.md` with comprehensive testing guidelines
- Updated `requirements.txt` with testing dependencies

## [1.0.0] - 2026-02-11

### Added

- Initial release of LinkedIn Post Scraper
- Playwright-based web scraping with persistent browser sessions
- Two-phase workflow: scan posts → select range → scrape
- CustomTkinter modern Windows UI
- Markdown output with YAML frontmatter
- Post browser tab to view saved posts
- Debug logging and HTML snapshot saving for troubleshooting
- Configuration management via `config.json`
- Duplicate post detection by source URL

### Features

- **Login once, reuse session**: Playwright persistent context saves cookies
- **Smart post selection**: Scan first, then select which posts to scrape
- **Clean markdown output**: Posts saved as `YYYY-MM-DD_slug.md` with metadata
- **Browse saved posts**: Built-in viewer for scraped content

---

## AI Agent Instructions

When working on this project, follow these guidelines:

### Code Style

- Use type hints for all function parameters and return values
- Follow PEP 8 naming conventions
- Add docstrings to all public functions and classes
- Keep functions focused and single-purpose

### Architecture

- **Separation of concerns**: Keep scraping, parsing, storage, and UI logic separate
- **Threading**: Use background threads for long-running operations (scraping, parsing)
- **Error handling**: Catch specific exceptions and provide user-friendly error messages
- **Logging**: Use Python's `logging` module for debug information

### Scraping Best Practices

- **Human-like behavior**: Add random delays between actions (1-3 seconds)
- **Respect rate limits**: Don't scrape too aggressively
- **Selector resilience**: Use multiple fallback selectors for LinkedIn elements
- **Debug snapshots**: Save HTML snapshots when selectors fail

### UI Guidelines

- **Responsive feedback**: Update status labels and progress bars from worker threads
- **Thread safety**: Use `self.after(0, lambda: ...)` for UI updates from threads
- **Disabled states**: Disable buttons during long operations
- **Clear messaging**: Provide specific, actionable status messages

### Testing

- Test with multiple LinkedIn profiles
- Verify incremental scraping doesn't re-download posts
- Test UI responsiveness during scraping
- Verify markdown output format and frontmatter

### Git Workflow

- Commit logical units of work
- Write descriptive commit messages
- Update CHANGELOG.md for all user-facing changes
- Tag releases with semantic version numbers

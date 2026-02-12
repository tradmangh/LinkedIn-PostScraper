# Scripts

This directory contains utility scripts for building and releasing the LinkedIn Post Scraper.

## Release Management

### create_releases.py

This script automates the creation of GitHub releases based on `CHANGELOG.md` entries.

**What it does:**
1. Parses `CHANGELOG.md` to extract version information
2. Creates git tags for each version (v1.0.0, v1.1.0, v1.2.0, etc.)
3. Pushes tags to GitHub
4. Creates GitHub releases with detailed release notes

**Prerequisites:**
- Python 3.8+
- `requests` library installed (`pip install requests`)
- GitHub personal access token with `repo` scope

**Usage:**

```bash
# Set your GitHub token
export GITHUB_TOKEN='your_github_personal_access_token'

# Run the script
python3 scripts/create_releases.py
```

**Creating a GitHub Personal Access Token:**

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select the `repo` scope
4. Copy the generated token
5. Export it as shown above

**Note:** Once tags are pushed to GitHub, the automated build workflow (`.github/workflows/build.yml`) will automatically build and attach the executables to each release.

## Build Scripts

- `build_windows.bat` - Build executables on Windows
- `build_macos.sh` - Build executables on macOS
- `build_linux.sh` - Build executables on Linux

See [BUILDING.md](../BUILDING.md) for detailed build instructions.

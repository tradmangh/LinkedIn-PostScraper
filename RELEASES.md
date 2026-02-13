# Creating Releases from CHANGELOG

This document explains how to create GitHub releases based on the CHANGELOG.md file.

## Automated Process (Recommended)

The easiest way to create releases is using the GitHub Actions workflow:

### Option 1: Manual Workflow Trigger

1. Go to https://github.com/tradmangh/LinkedIn-PostScraper/actions
2. Select "Create Releases" workflow
3. Click "Run workflow"
4. Select the branch (usually `main`)
5. Click "Run workflow" button

The workflow will:
- Parse CHANGELOG.md to extract all version entries
- Create git tags for each version found
- Push tags to GitHub
- Trigger the existing build workflow (build.yml) which automatically:
  - Builds executables for Windows, macOS, and Linux
  - Creates draft releases with the built executables attached
  - Adds installation instructions to each release

### Option 2: Automatic on CHANGELOG Update

The workflow also runs automatically when CHANGELOG.md is updated on the main branch.

## Quick Start (Command Line)

Alternatively, you can use the automated script locally:

```bash
# Option A: Just create and push tags (let build.yml create releases)
python3 scripts/create_releases.py --skip-releases

# Option B: Create tags AND releases directly (requires GitHub token)
export GITHUB_TOKEN='your_github_personal_access_token'
python3 scripts/create_releases.py
```

**Note:** Option A is recommended as it leverages the existing build.yml workflow to create releases with executables attached.

## Manual Process

If you prefer to create releases manually:

### Step 1: Create Tags

```bash
# Tag v1.0.0
git tag -a v1.0.0 -m "Release v1.0.0 - Initial release"

# Tag v1.1.0
git tag -a v1.1.0 -m "Release v1.1.0 - Testing infrastructure"

# Tag v1.2.0
git tag -a v1.2.0 -m "Release v1.2.0 - Cross-platform executables"
```

### Step 2: Push Tags

```bash
git push origin --tags
```

This will trigger the GitHub Actions workflow (`.github/workflows/build.yml`) which will:
- Build executables for Windows, macOS, and Linux
- Create draft releases
- Attach the built executables to the releases

### Step 3: Edit Release Notes

After the workflow completes:
1. Go to https://github.com/tradmangh/LinkedIn-PostScraper/releases
2. Edit each draft release
3. Copy the relevant section from CHANGELOG.md
4. Publish the release

## Getting a GitHub Personal Access Token

If you need to create a token for the automated script:

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a descriptive name (e.g., "LinkedIn-PostScraper Releases")
4. Select the `repo` scope
5. Click "Generate token"
6. Copy the token and export it: `export GITHUB_TOKEN='ghp_...'`

**Security Note:** Never commit your personal access token to the repository!

## Verifying Releases

After creation, verify your releases at:
https://github.com/tradmangh/LinkedIn-PostScraper/releases

Each release should have:
- A tag (v1.0.0, v1.1.0, v1.2.0)
- Release notes from CHANGELOG.md
- Six executable files (once builds complete):
  - LinkedIn-PostScraper-Standalone-Windows.zip
  - LinkedIn-PostScraper-Full-Windows.zip
  - LinkedIn-PostScraper-Standalone-macOS.zip
  - LinkedIn-PostScraper-Full-macOS.zip
  - LinkedIn-PostScraper-Standalone-Linux.tar.gz
  - LinkedIn-PostScraper-Full-Linux.tar.gz

## Troubleshooting

**Problem:** "Authentication failed" when pushing tags

**Solution:** Make sure you have push access to the repository. If using HTTPS, you may need to:
```bash
# Use SSH instead
git remote set-url origin git@github.com:tradmangh/LinkedIn-PostScraper.git
git push origin --tags
```

**Problem:** Builds don't start after pushing tags

**Solution:** Check that:
1. The tag matches the pattern `v*.*.*` (e.g., v1.0.0)
2. The GitHub Actions workflow file exists at `.github/workflows/build.yml`
3. GitHub Actions are enabled for the repository

**Problem:** Script fails with "GITHUB_TOKEN not set"

**Solution:** Export your personal access token:
```bash
export GITHUB_TOKEN='your_token_here'
```

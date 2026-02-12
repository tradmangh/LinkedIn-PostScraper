#!/usr/bin/env python3
"""
Script to create GitHub releases based on CHANGELOG.md entries.

This script:
1. Parses CHANGELOG.md for version entries
2. Creates git tags for each version (optional, can be skipped)
3. Creates GitHub releases using the GitHub API

Usage:
  # Create tags and releases
  python3 scripts/create_releases.py

  # Skip tag creation (e.g., tags already exist)
  python3 scripts/create_releases.py --skip-tags

  # Tag-only mode (create tags but skip GitHub releases)
  python3 scripts/create_releases.py --skip-releases

  # Skip pushing tags (e.g., will push manually)
  python3 scripts/create_releases.py --skip-push
  # Specify different repository
  python3 scripts/create_releases.py --owner=myuser --repo=myrepo
"""

import re
import subprocess
import sys
from typing import List, Tuple
import requests
import os
import textwrap

# Constants
MAX_TAG_MESSAGE_LENGTH = 200  # Maximum length of changelog text included in a tag message before truncation


def _get_default_owner_repo() -> Tuple[str, str]:
    """
    Determine the default GitHub owner and repository.

    Preference order:
      1. GITHUB_REPOSITORY environment variable (owner/repo)
      2. Git remote.origin.url
      3. Hard-coded fallback (original behavior)
    """
    # 1. Try GitHub Actions environment variable
    github_repo = os.getenv("GITHUB_REPOSITORY")
    if github_repo and "/" in github_repo:
        owner, repo = github_repo.split("/", 1)
        if owner and repo:
            return owner, repo

    # 2. Try git remote.origin.url
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=True,
        )
        url = result.stdout.strip()

        # Handle SSH URLs: git@github.com:owner/repo.git
        if url.startswith("git@github.com:"):
            path = url.split("git@github.com:", 1)[1]
        # Handle HTTPS URLs: https://github.com/owner/repo.git
        elif "github.com/" in url:
            path = url.split("github.com/", 1)[1]
        else:
            path = ""

        if path:
            if path.endswith(".git"):
                path = path[:-4]
            if "/" in path:
                owner, repo = path.split("/", 1)
                if owner and repo:
                    return owner, repo
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        # If git is not available, not on PATH, or remote is not configured, fall back
        pass

    # 3. Fallback to original hard-coded defaults
    return "tradmangh", "LinkedIn-PostScraper"


DEFAULT_OWNER, DEFAULT_REPO = _get_default_owner_repo()

def parse_changelog(changelog_path: str) -> List[Tuple[str, str, str]]:
    """
    Parse CHANGELOG.md and extract version information.
    
    Returns:
        List of tuples: (version, date, changelog_text)
    """
    with open(changelog_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all version sections
    # Pattern: ## [X.Y.Z] - YYYY-MM-DD
    version_pattern = r'## \[(\d+\.\d+\.\d+)\] - (\d{4}-\d{2}-\d{2})'
    
    versions = []
    matches = list(re.finditer(version_pattern, content))
    
    for i, match in enumerate(matches):
        version = match.group(1)
        date = match.group(2)
        
        # Get the content between this version and the next
        start_pos = match.end()
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            # Find the end marker (## AI Agent Instructions header or end of file)
            end_marker = content.find('## AI Agent Instructions', start_pos)
            if end_marker != -1:
                end_pos = end_marker
            else:
                end_pos = len(content)
        
        changelog_text = content[start_pos:end_pos].strip()
        versions.append((version, date, changelog_text))
    
    return versions


def create_git_tag(version: str, message: str) -> bool:
    """Create a git tag for the version."""
    tag_name = f"v{version}"
    
    try:
        # Check if tag already exists
        result = subprocess.run(
            ['git', 'tag', '-l', tag_name],
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.stdout.strip():
            print(f"  Tag {tag_name} already exists, skipping...")
            return True
        
        # Create annotated tag
        subprocess.run(
            ['git', 'tag', '-a', tag_name, '-m', message],
            check=True,
            capture_output=True
        )
        print(f"  Created tag: {tag_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Error creating tag {tag_name}: {e}")
        return False


def push_tags() -> bool:
    """Push version tags (v*.*.*) to origin."""
    try:
        # List version tags matching the v*.*.* pattern
        list_result = subprocess.run(
            ['git', 'tag', '-l', 'v*.*.*'],
            capture_output=True,
            text=True,
            check=True
        )
        tags = [tag.strip() for tag in list_result.stdout.splitlines() if tag.strip()]
        if not tags:
            print("No version tags matching 'v*.*.*' found to push")
            return True

        # Push only the matching version tags
        subprocess.run(
            ['git', 'push', 'origin', *tags],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Successfully pushed version tags to origin: {', '.join(tags)}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error pushing tags: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False


def create_github_release(
    owner: str,
    repo: str,
    version: str,
    changelog: str,
    token: str,
    timeout: int = 30
) -> bool:
    """Create a GitHub release using the API."""
    tag_name = f"v{version}"
    
    # Check if release already exists
    check_url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag_name}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    try:
        check_response = requests.get(check_url, headers=headers, timeout=timeout)
    except requests.exceptions.RequestException as e:
        print(f"  Error checking for existing release {tag_name}: {e}")
        return False

    if check_response.status_code == 200:
        print(f"  Release {tag_name} already exists, skipping...")
        return True
    elif check_response.status_code == 404:
        # Release doesn't exist, continue with creation
        pass
    elif check_response.status_code in (401, 403):
        print(
            f"  Authentication/authorization error when checking for existing release {tag_name}: "
            f"HTTP {check_response.status_code}. Please verify your GitHub token has access to "
            f"{owner}/{repo}."
        )
        return False
    else:
        print(
            f"  Unexpected response when checking for existing release {tag_name}: "
            f"HTTP {check_response.status_code} - {check_response.text}"
        )
        return False
    
    # Prepare release body
    release_body = f"""## 📝 What's New in v{version}

{changelog}

---

## 📦 Download Options

### Standalone Builds (~50-80 MB)
Downloads browser on first run. Recommended for most users.
- **Windows**: `LinkedIn-PostScraper-Standalone-Windows.zip`
- **macOS**: `LinkedIn-PostScraper-Standalone-macOS.zip`
- **Linux**: `LinkedIn-PostScraper-Standalone-Linux.tar.gz`

### Full Builds (~350-400 MB)
Browser included. Use if download is blocked or for offline use.
- **Windows**: `LinkedIn-PostScraper-Full-Windows.zip`
- **macOS**: `LinkedIn-PostScraper-Full-macOS.zip`
- **Linux**: `LinkedIn-PostScraper-Full-Linux.tar.gz`

## 🚀 Installation

**Windows:**
1. Download and extract the ZIP file
2. Run `LinkedIn-PostScraper-Standalone.exe` or `LinkedIn-PostScraper-Full.exe`
3. If Windows Defender blocks it, click "More info" → "Run anyway"

**macOS:**
1. Download and extract the ZIP file
2. Right-click the app → "Open" (to bypass Gatekeeper)
3. Or run: `xattr -cr LinkedIn-PostScraper-*.app`

**Linux:**
1. Download and extract the tar.gz file
2. Make executable: `chmod +x linkedin-postscraper-*`
3. Run: `./linkedin-postscraper-standalone` or `./linkedin-postscraper-full`

See [CHANGELOG.md](https://github.com/{owner}/{repo}/blob/main/CHANGELOG.md) for complete details.
"""
    
    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    
    data = {
        "tag_name": tag_name,
        "name": f"v{version}",
        "body": release_body,
        "draft": False,
        "prerelease": False
    }
    
    try:
        response = requests.post(api_url, json=data, headers=headers, timeout=timeout)
        response.raise_for_status()
        print(f"  Created GitHub release: {tag_name}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"  Error creating GitHub release {tag_name}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response: {e.response.text}")
        return False


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create GitHub releases from CHANGELOG.md')
    parser.add_argument('--skip-tags', action='store_true',
                       help='Skip git tag creation')
    parser.add_argument('--skip-push', action='store_true',
                       help='Skip pushing tags to remote')
    parser.add_argument('--skip-releases', action='store_true',
                       help='Skip creating GitHub releases (only create/push tags)')
    parser.add_argument('--owner', default=DEFAULT_OWNER,
                       help=f'Repository owner (default: {DEFAULT_OWNER})')
    parser.add_argument('--repo', default=DEFAULT_REPO,
                       help=f'Repository name (default: {DEFAULT_REPO})')
    parser.add_argument('--changelog', default='CHANGELOG.md',
                       help='Path to CHANGELOG file (default: CHANGELOG.md)')
    args = parser.parse_args()
    
    # Get repository info from args
    owner = args.owner
    repo = args.repo
    changelog_path = args.changelog
    
    # Parse changelog
    print(f"Parsing {changelog_path}...")
    versions = parse_changelog(changelog_path)
    
    if not versions:
        print(f"No versions found in {changelog_path}")
        sys.exit(1)
    
    print(f"Found {len(versions)} versions to release:")
    for version, date, _ in versions:
        print(f"  - v{version} ({date})")
    
    # Create tags
    if not args.skip_tags:
        print("\nCreating git tags...")
        for version, date, changelog in versions:
            # Use textwrap.shorten to truncate at word boundaries
            truncated = textwrap.shorten(
                changelog,
                width=MAX_TAG_MESSAGE_LENGTH,
                placeholder="..."
            )
            message = f"Release v{version}\n\n{truncated}"
            if not create_git_tag(version, message):
                print(f"Failed to create git tag for version v{version}. Aborting before pushing tags or creating releases.")
                sys.exit(1)
    else:
        print("\nSkipping git tag creation (--skip-tags specified)")
    
    # Push tags
    if not args.skip_push and not args.skip_tags:
        print("\nPushing tags to GitHub...")
        if not push_tags():
            print("Failed to push tags. Releases may not be created.")
            sys.exit(1)
    else:
        print("\nSkipping tag push (--skip-push or --skip-tags specified)")
    
    # Create GitHub releases
    if not args.skip_releases:
        # Verify tags were pushed before creating releases
        if args.skip_push:
            print("\nError: Cannot create GitHub releases with --skip-push")
            print("Releases require tags to be pushed to GitHub first.")
            print("Either:")
            print("  1. Remove --skip-push to push tags and create releases")
            print("  2. Add --skip-releases to only create/push tags (recommended)")
            sys.exit(1)
        
        # Get GitHub token from environment
        token = os.environ.get('GITHUB_TOKEN')
        if not token:
            print("Error: GITHUB_TOKEN environment variable not set")
            print("\nTo create releases, you need a GitHub token:")
            print("1. Create a GitHub personal access token with 'repo' scope")
            print("2. Export it: export GITHUB_TOKEN='your_token_here'")
            print("3. Run this script again")
            sys.exit(1)
        
        print("\nCreating GitHub releases...")
        success_count = 0
        for version, date, changelog in versions:
            if create_github_release(owner, repo, version, changelog, token):
                success_count += 1
        
        print(f"\n✅ Created {success_count}/{len(versions)} releases!")
        print(f"Check https://github.com/{owner}/{repo}/releases")
    else:
        print("\nSkipping GitHub release creation (--skip-releases specified)")
        if not args.skip_push and not args.skip_tags:
            print("Tags have been pushed. The build workflow will create releases automatically.")


if __name__ == "__main__":
    main()

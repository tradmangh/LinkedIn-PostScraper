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
  
  # Skip pushing tags (e.g., will push manually)
  python3 scripts/create_releases.py --skip-push
  
  # Specify different repository
  python3 scripts/create_releases.py --owner=myuser --repo=myrepo
"""

import re
import subprocess
import sys
from typing import Dict, List, Tuple
import requests
import os

# Constants
MAX_TAG_MESSAGE_LENGTH = 200  # Maximum length of tag message before truncation
DEFAULT_OWNER = "tradmangh"
DEFAULT_REPO = "LinkedIn-PostScraper"

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
            # Find the end marker (## AI Agent Instructions or end of file)
            end_marker = content.find('---', start_pos)
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
    """Push all tags to origin."""
    try:
        result = subprocess.run(
            ['git', 'push', 'origin', '--tags'],
            capture_output=True,
            text=True,
            check=True
        )
        print("Successfully pushed all tags to origin")
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
    token: str
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
        check_response = requests.get(check_url, headers=headers)
        if check_response.status_code == 200:
            print(f"  Release {tag_name} already exists, skipping...")
            return True
    except requests.exceptions.RequestException:
        pass  # Release doesn't exist, continue with creation
    
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
        response = requests.post(api_url, json=data, headers=headers)
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
    
    # Get GitHub token from environment
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("Error: GITHUB_TOKEN environment variable not set")
        print("\nTo use this script:")
        print("1. Create a GitHub personal access token with 'repo' scope")
        print("2. Export it: export GITHUB_TOKEN='your_token_here'")
        print("3. Run this script again")
        sys.exit(1)
    
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
            message = f"Release v{version}\n\n{changelog[:MAX_TAG_MESSAGE_LENGTH]}"
            create_git_tag(version, message)
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
    print("\nCreating GitHub releases...")
    success_count = 0
    for version, date, changelog in versions:
        if create_github_release(owner, repo, version, changelog, token):
            success_count += 1
    
    print(f"\n✅ Created {success_count}/{len(versions)} releases!")
    print(f"Check https://github.com/{owner}/{repo}/releases")


if __name__ == "__main__":
    main()

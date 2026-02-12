"""
Tests for the create_releases.py script.
"""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from create_releases import parse_changelog


def test_parse_changelog_with_fixture(tmp_path):
    """Test parsing a CHANGELOG with multiple versions."""
    changelog_content = """# Changelog

All notable changes will be documented in this file.

## [1.2.0] - 2026-02-11

### Added

- Feature A
- Feature B

### Changed

- Update C

## [1.1.0] - 2026-02-10

### Added

- Feature D
- Feature E

## [1.0.0] - 2026-02-09

### Added

- Initial release
- Feature F

---

## AI Agent Instructions

Some instructions here.
"""
    
    changelog_file = tmp_path / "CHANGELOG.md"
    changelog_file.write_text(changelog_content, encoding="utf-8")
    
    versions = parse_changelog(str(changelog_file))
    
    assert len(versions) == 3
    
    # Check first version
    assert versions[0][0] == "1.2.0"
    assert versions[0][1] == "2026-02-11"
    assert "Feature A" in versions[0][2]
    assert "Feature B" in versions[0][2]
    
    # Check second version
    assert versions[1][0] == "1.1.0"
    assert versions[1][1] == "2026-02-10"
    assert "Feature D" in versions[1][2]
    
    # Check third version
    assert versions[2][0] == "1.0.0"
    assert versions[2][1] == "2026-02-09"
    assert "Initial release" in versions[2][2]
    
    # Verify content stops at the --- marker
    assert "AI Agent Instructions" not in versions[2][2]


def test_parse_changelog_no_versions(tmp_path):
    """Test parsing a CHANGELOG with no version entries."""
    changelog_content = """# Changelog

This is just a header with no versions.
"""
    
    changelog_file = tmp_path / "CHANGELOG.md"
    changelog_file.write_text(changelog_content, encoding="utf-8")
    
    versions = parse_changelog(str(changelog_file))
    
    assert len(versions) == 0


def test_parse_changelog_single_version(tmp_path):
    """Test parsing a CHANGELOG with a single version."""
    changelog_content = """# Changelog

## [1.0.0] - 2026-01-01

### Added

- Initial feature
"""
    
    changelog_file = tmp_path / "CHANGELOG.md"
    changelog_file.write_text(changelog_content, encoding="utf-8")
    
    versions = parse_changelog(str(changelog_file))
    
    assert len(versions) == 1
    assert versions[0][0] == "1.0.0"
    assert versions[0][1] == "2026-01-01"
    assert "Initial feature" in versions[0][2]


def test_parse_changelog_version_ordering(tmp_path):
    """Test that versions are returned in the order they appear in the file."""
    changelog_content = """# Changelog

## [2.0.0] - 2026-03-01

### Added
- New stuff

## [1.5.0] - 2026-02-01

### Added
- More stuff

## [1.0.0] - 2026-01-01

### Added
- Original stuff
"""
    
    changelog_file = tmp_path / "CHANGELOG.md"
    changelog_file.write_text(changelog_content, encoding="utf-8")
    
    versions = parse_changelog(str(changelog_file))
    
    assert len(versions) == 3
    # Versions should be in order they appear in file
    assert versions[0][0] == "2.0.0"
    assert versions[1][0] == "1.5.0"
    assert versions[2][0] == "1.0.0"

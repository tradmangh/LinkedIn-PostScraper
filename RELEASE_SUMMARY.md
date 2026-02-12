# Release Creation Summary

## What Has Been Prepared

This PR contains complete automation to create GitHub releases based on CHANGELOG.md:

### 1. GitHub Actions Workflow
- **File**: `.github/workflows/create-releases.yml`
- **Triggers**: 
  - Manual trigger via GitHub Actions UI
  - Automatic when CHANGELOG.md is updated on main branch
- **What it does**:
  - Parses CHANGELOG.md to extract all version entries
  - Creates git tags for each version found
  - Pushes tags to GitHub
  - Triggers the existing build.yml workflow which:
    - Builds executables for all platforms
    - Creates draft releases with executables attached

### 2. Python Script
- **File**: `scripts/create_releases.py`
- Parses CHANGELOG.md using regex to extract versions and release notes
- Creates tags dynamically from CHANGELOG entries (not hard-coded)
- Can create tags only (`--skip-releases`) or tags + releases
- Supports custom owner/repo via CLI args or auto-detection

### 3. Documentation
- **RELEASES.md**: Complete guide for creating releases
- **scripts/README.md**: Documentation for all scripts

## How to Create the Releases

### Option 1: Merge This PR (Recommended)

1. Merge this PR to the main branch
2. Go to: https://github.com/tradmangh/LinkedIn-PostScraper/actions
3. Select "Create Releases" workflow
4. Click "Run workflow" → Select "main" branch → Click "Run workflow"
5. Wait for the workflow to complete
6. Check releases at: https://github.com/tradmangh/LinkedIn-PostScraper/releases

The workflow will:
- Parse CHANGELOG.md to find all versions
- Create and push tags for each version
- Trigger build.yml which creates draft releases with executables
- Download links for executables (attached after build completes)

### Option 2: Manual Process

If you prefer to create releases manually without merging:

1. Create the tags locally:
```bash
git tag -a v1.0.0 -m "Release v1.0.0 - Initial release"
git tag -a v1.1.0 -m "Release v1.1.0 - Testing infrastructure"  
git tag -a v1.2.0 -m "Release v1.2.0 - Cross-platform executables"
```

2. Push the tags:
```bash
git push origin --tags
```

3. The build workflow will run automatically and create draft releases
4. Edit each release and publish it

### Option 3: Use the Script Locally

```bash
export GITHUB_TOKEN='your_github_personal_access_token'
python3 scripts/create_releases.py
```

## What Releases Will Be Created

Based on CHANGELOG.md, three releases will be created:

- **v1.0.0** (2026-02-11): Initial release
  - Playwright-based scraping
  - CustomTkinter UI
  - Markdown output

- **v1.1.0** (2026-02-11): Testing infrastructure
  - Pytest suite with 40+ tests
  - GitHub Actions CI/CD
  - Engagement metrics

- **v1.2.0** (2026-02-11): Cross-platform executables
  - Windows, macOS, Linux builds
  - Standalone and Full Bundle variants
  - Automated builds via GitHub Actions

Each release includes:
- Detailed changelog from CHANGELOG.md
- Installation instructions for all platforms
- Download links for 6 executable files (after builds complete)

## Next Steps

1. Review and merge this PR
2. Trigger the "Create Releases" workflow manually
3. Monitor the workflow execution
4. Verify releases at https://github.com/tradmangh/LinkedIn-PostScraper/releases
5. Wait for builds to complete and attach executables
6. Publish or announce the releases as needed

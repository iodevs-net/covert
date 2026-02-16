#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Current version in covert/__init__.py:"
    grep "__version__" covert/__init__.py
    echo ""
    read -p "Enter new version (e.g. 1.2.0): " VERSION
else
    VERSION=$1
fi

if [ -z "$VERSION" ]; then
    echo "Error: Version is required."
    exit 1
fi

# Validate version format (simple regex)
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version must be in format X.Y.Z (e.g., 1.1.1)"
    exit 1
fi

# Ensure git is clean
if [[ -n $(git status -s) ]]; then
    echo "Error: Git working directory is not clean. Commit or stash changes first."
    exit 1
fi

echo "🚀 Preparing release v$VERSION..."

# Update version in __init__.py
# Assuming __version__ = "..." format
sed -i "s/__version__ = \".*\"/__version__ = \"$VERSION\"/" covert/__init__.py

# Verify change
if grep -q "__version__ = \"$VERSION\"" covert/__init__.py; then
    echo "Updated __init__.py to $VERSION"
else
    echo "Error: Failed to update version in covert/__init__.py"
    exit 1
fi

# Update version in pyproject.toml
sed -i "s/^version = \".*\"/version = \"$VERSION\"/" pyproject.toml

# Verify pyproject.toml change
if grep -q "version = \"$VERSION\"" pyproject.toml; then
    echo "Updated pyproject.toml to $VERSION"
else
    echo "Error: Failed to update version in pyproject.toml"
    exit 1
fi

# Commit
git add covert/__init__.py pyproject.toml
git commit -m "chore(release): v$VERSION"

# Tag
git tag -a "v$VERSION" -m "Release v$VERSION"

# Push
echo "Pushing to origin..."
git push origin main
git push origin "v$VERSION"

echo "✅ Release v$VERSION pushed!"
echo "GitHub Actions should now be triggering the build and publish process."

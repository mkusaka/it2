#!/usr/bin/env python3
"""Version bumping script for it2."""

import re
import shutil
import subprocess
import sys
from pathlib import Path


def get_current_version():
    """Get the current version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()
    match = re.search(r'version = "(\d+\.\d+\.\d+)"', content)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")
    return match.group(1)


def bump_version(version: str, bump_type: str) -> str:
    """Bump the version based on the bump type."""
    major, minor, patch = map(int, version.split("."))

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

    return f"{major}.{minor}.{patch}"


def update_version_in_file(file_path: Path, old_version: str, new_version: str):
    """Update version in a file."""
    content = file_path.read_text()

    # For pyproject.toml
    if file_path.name == "pyproject.toml":
        content = re.sub(r'version = "\d+\.\d+\.\d+"', f'version = "{new_version}"', content)
    # For __init__.py
    elif file_path.name == "__init__.py":
        content = re.sub(
            r'__version__ = "\d+\.\d+\.\d+"', f'__version__ = "{new_version}"', content
        )

    file_path.write_text(content)


def main():
    """Main function."""
    if len(sys.argv) != 2 or sys.argv[1] not in ["major", "minor", "patch"]:
        print("Usage: python bump_version.py [major|minor|patch]")
        sys.exit(1)

    bump_type = sys.argv[1]

    # Get current version
    current_version = get_current_version()
    print(f"Current version: {current_version}")

    # Calculate new version
    new_version = bump_version(current_version, bump_type)
    print(f"New version: {new_version}")

    # Update version in files
    update_version_in_file(Path("pyproject.toml"), current_version, new_version)

    init_file = Path("src/it2/__init__.py")
    if init_file.exists():
        update_version_in_file(init_file, current_version, new_version)

    # Find executables using full paths
    uv_path = shutil.which("uv")
    git_path = shutil.which("git")

    if not uv_path:
        raise FileNotFoundError("uv not found in PATH")
    if not git_path:
        raise FileNotFoundError("git not found in PATH")

    # Run uv sync to update lock file
    print("Updating lock file...")
    subprocess.run([uv_path, "sync"], check=True)

    # Create git commit
    print("Creating git commit...")
    subprocess.run([git_path, "add", "pyproject.toml", "uv.lock"], check=True)
    if init_file.exists():
        subprocess.run([git_path, "add", str(init_file)], check=True)

    subprocess.run([git_path, "commit", "-m", f"chore: bump version to {new_version}"], check=True)

    # Create git tag
    print("Creating git tag...")
    subprocess.run([git_path, "tag", f"v{new_version}"], check=True)

    print(f"\nVersion bumped to {new_version}")
    print("To publish, run:")
    print("  git push")
    print(f"  git push origin v{new_version}")


if __name__ == "__main__":
    main()

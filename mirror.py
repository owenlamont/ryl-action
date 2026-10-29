# /// script
# requires-python = ">=3.15"
# dependencies = [
#   "packaging==26.3",
#   "urllib3==2.8.0",
# ]
# ///
"""Pin ryl-action to each new ryl release, committing and tagging it to match."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess  # ruff: ignore[suspicious-subprocess-import]

from packaging.version import InvalidVersion, Version
import urllib3


RELEASES_URL = "https://api.github.com/repos/owenlamont/ryl/releases?per_page=100"
ACTION_DEFAULT = re.compile(r"(?<=^    default: )\d+\.\d+\.\d+$", re.MULTILINE)
README_REF = re.compile(r"(?<=ryl-action@v)\d+\.\d+\.\d+")
PINS = {"action.yml": ACTION_DEFAULT, "README.md": README_REF}


def main() -> None:
    """Commit and tag every published ryl release newer than the pinned one.

    Raises:
        RuntimeError: A dispatched version has no published release.
    """
    current = _pinned_version()
    published = _published_versions()
    requested = _dispatch_version()
    if requested is not None and requested not in published:
        raise RuntimeError(f"ryl {requested} has no published release with SHA256SUMS")

    newer = [version for version in published if version > current]
    if not newer:
        print(f"Pinned ryl {current} is the latest published release.")
        return
    for version in newer:
        _pin(version)
        _git("add", *PINS)
        _git("commit", "-m", f"Mirror: {version}")
        _git("tag", f"v{version}")


def _git(*args: str) -> None:
    subprocess.run(["git", *args], check=True)  # ruff: ignore[subprocess-without-shell-equals-true, start-process-with-partial-path]


def _pinned_version() -> Version:
    matches = ACTION_DEFAULT.findall(Path("action.yml").read_text())
    if len(matches) != 1:
        raise RuntimeError(f"Expected one X.Y.Z input default in action.yml: {matches}")
    return Version(matches[0])


def _published_versions() -> list[Version]:
    """Return the ascending ryl releases whose binaries have all been uploaded.

    ryl uploads SHA256SUMS with its archives before publishing a draft release,
    so a published release listing it has every asset the action downloads.

    Raises:
        RuntimeError: The GitHub API did not return the release list.
    """
    headers = {"Accept": "application/vnd.github+json"}
    if token := os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    response = urllib3.request("GET", RELEASES_URL, headers=headers)
    if response.status != 200:
        raise RuntimeError(f"Failed to list ryl releases: HTTP {response.status}")
    return sorted(
        Version(release["tag_name"].removeprefix("v"))
        for release in response.json()
        if not release["draft"]
        and not release["prerelease"]
        and any(asset["name"] == "SHA256SUMS" for asset in release["assets"])
    )


def _dispatch_version() -> Version | None:
    raw = os.getenv("DISPATCH_VERSION", "").strip()
    if not raw:
        return None
    try:
        return Version(raw.removeprefix("v"))
    except InvalidVersion as exc:
        raise RuntimeError(f"Invalid DISPATCH_VERSION: {raw}") from exc


def _pin(version: Version) -> None:
    for name, pattern in PINS.items():
        path = Path(name)
        path.write_text(pattern.sub(str(version), path.read_text()))


if __name__ == "__main__":
    main()

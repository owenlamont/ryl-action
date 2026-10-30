# /// script
# requires-python = ">=3.15"
# dependencies = [
#   "httpx2==2.16.0",
#   "orjson==3.13.0",
#   "packaging==26.3",
# ]
# ///
"""Pin ryl-action to each new ryl release, committing and tagging it to match."""

import os
from pathlib import Path
import re
import subprocess  # ruff: ignore[suspicious-subprocess-import]
from types import MappingProxyType
from typing import Final

import httpx2
import orjson
from packaging.version import InvalidVersion, Version


_RELEASES_URL: Final = "https://api.github.com/repos/owenlamont/ryl/releases"
_TIMEOUT_SECONDS: Final = 30.0
_ACTION_DEFAULT: Final = re.compile(r"(?<=^    default: )\d+\.\d+\.\d+$", re.MULTILINE)
_README_REF: Final = re.compile(r"(?<=ryl-action@v)\d+\.\d+\.\d+")
_PINS: Final = MappingProxyType(
    {"action.yml": _ACTION_DEFAULT, "README.md": _README_REF}
)


class MirrorError(Exception):
    """The ryl release state or this repo's pins are not what mirroring needs."""


def main() -> None:
    """Commit and tag every published ryl release newer than the pinned one.

    Raises:
        MirrorError: A dispatched version has no published release.
    """
    current = _pinned_version()
    published = _published_versions()
    requested = _dispatch_version()
    if requested is not None and requested not in published:
        raise MirrorError(f"ryl {requested} has no published release with SHA256SUMS")

    newer = [version for version in published if version > current]
    if not newer:
        print(f"Pinned ryl {current} is the latest published release.")
        return
    for version in newer:
        _pin(version)
        _git("add", *_PINS)
        _git("commit", "-m", f"Mirror: {version}")
        _git("tag", f"v{version}")


def _git(*args: str) -> None:
    subprocess.run(["git", *args], check=True)  # ruff: ignore[subprocess-without-shell-equals-true, start-process-with-partial-path]


def _pinned_version() -> Version:
    matches = _ACTION_DEFAULT.findall(Path("action.yml").read_text())
    if len(matches) != 1:
        raise MirrorError(f"Expected one X.Y.Z input default in action.yml: {matches}")
    return Version(matches[0])


def _published_versions() -> list[Version]:
    """Return the ascending ryl releases whose binaries have all been uploaded.

    ryl uploads SHA256SUMS with its archives before publishing a draft release,
    so a published release listing it has every asset the action downloads.
    """
    headers = {"Accept": "application/vnd.github+json"}
    if token := os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    response = httpx2.get(
        _RELEASES_URL,
        params={"per_page": 100},
        headers=headers,
        timeout=_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return sorted(
        Version(release["tag_name"].removeprefix("v"))
        for release in orjson.loads(response.content)
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
        raise MirrorError(f"Invalid DISPATCH_VERSION: {raw}") from exc


def _pin(version: Version) -> None:
    for name, pattern in _PINS.items():
        path = Path(name)
        path.write_text(pattern.sub(str(version), path.read_text()))


if __name__ == "__main__":
    main()

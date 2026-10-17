"""Authenticate Core v0.6.6 release wheel without altering Concord's environment."""

from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path

CORE_RELEASE_WHEEL_SHA256 = (
    "d6d21e426092b0329bcfd69b6fbee44c345edc46794a914d847d5ea73a2b7301"
)

EXPECTED_NAME = "pds_core-0.6.6-py3-none-any.whl"
EXPECTED_METADATA = "pds_core-0.6.6.dist-info/METADATA"


def verify_core_release_input(path: Path) -> str:
    if path.name != EXPECTED_NAME or not path.is_file():
        raise ValueError(f"Expected the published Core wheel named {EXPECTED_NAME}.")
    actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual_sha != CORE_RELEASE_WHEEL_SHA256:
        raise ValueError("Core wheel SHA-256 differs from published v0.6.6.")
    try:
        with zipfile.ZipFile(path) as wheel:
            metadata = wheel.read(EXPECTED_METADATA).decode("utf-8")
    except (OSError, KeyError, UnicodeError, zipfile.BadZipFile) as exc:
        raise ValueError("Core wheel metadata cannot be verified.") from exc
    if not any(line.strip() == "Version: 0.6.6" for line in metadata.splitlines()):
        raise ValueError("Core wheel metadata version is not 0.6.6.")
    if not any(
        line.strip().casefold() in {"name: pds-core", "name: pds_core"}
        for line in metadata.splitlines()
    ):
        raise ValueError("Core wheel metadata distribution name is incorrect.")
    return actual_sha


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    args = parser.parse_args()
    actual = verify_core_release_input(args.wheel)
    print(f"Core v0.6.6 immutable wheel input: VERIFIED sha256={actual}")
    print("This is wheel authentication, NOT installed Core viewer qualification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

FILES = {
    Path("docs/design/examples/seminar-contract-example.md"): 2,
    Path("docs/design/examples/laboratory-contract-example.md"): 1,
    Path("docs/design/examples/project-contract-example.md"): 3,
}

JSON_BLOCK = re.compile(
    r"```json\n(?P<body>\{.*?\}\n)```",
    flags=re.DOTALL,
)

RECORD_KIND_LINE = (
    '  "record_kind": "concord_academic_result_manifest",\n'
)

RECORD_OWNER_LINE = (
    '  "record_owner": "concord",\n'
)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def process_file(path: Path, expected_manifest_count: int) -> None:
    original_text = path.read_text(encoding="utf-8")
    digest_replacements: dict[str, str] = {}
    changed_count = 0

    def correct_manifest(match: re.Match[str]) -> str:
        nonlocal changed_count

        body = match.group("body")

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            # Leave unrelated illustrative JSON blocks unchanged.
            return match.group(0)

        if (
            parsed.get("producer_module_id") != "concord"
            or "record_set_id" not in parsed
            or "record_set_revision" not in parsed
        ):
            return match.group(0)

        if parsed.get("record_kind") != "concord_academic_result_manifest":
            raise RuntimeError(
                f"{path}: expected top-level manifest record_kind"
            )

        if parsed.get("record_owner") != "concord":
            raise RuntimeError(
                f"{path}: expected top-level manifest record_owner"
            )

        old_digest = sha256_text(body)

        corrected = body.replace(RECORD_KIND_LINE, "", 1)
        corrected = corrected.replace(RECORD_OWNER_LINE, "", 1)

        corrected_parsed = json.loads(corrected)

        if "record_kind" in corrected_parsed:
            raise RuntimeError(
                f"{path}: top-level record_kind was not removed"
            )

        if "record_owner" in corrected_parsed:
            raise RuntimeError(
                f"{path}: top-level record_owner was not removed"
            )

        if not corrected.endswith("\n"):
            raise RuntimeError(
                f"{path}: corrected manifest must end with one LF"
            )

        new_digest = sha256_text(corrected)
        digest_replacements[old_digest] = new_digest
        changed_count += 1

        return f"```json\n{corrected}```"

    corrected_text = JSON_BLOCK.sub(correct_manifest, original_text)

    if changed_count != expected_manifest_count:
        raise RuntimeError(
            f"{path}: corrected {changed_count} manifests; "
            f"expected {expected_manifest_count}"
        )

    for old_digest, new_digest in digest_replacements.items():
        if old_digest not in corrected_text:
            raise RuntimeError(
                f"{path}: documented old digest {old_digest} not found"
            )

        corrected_text = corrected_text.replace(
            old_digest,
            new_digest,
        )

        print(f"{path}: {old_digest} -> {new_digest}")

    with path.open("w", encoding="utf-8", newline="\n") as file:
        file.write(corrected_text)


def main() -> None:
    for path, expected_manifest_count in FILES.items():
        process_file(path, expected_manifest_count)

    print("Corrected six exact manifests and their documented digests.")


if __name__ == "__main__":
    main()
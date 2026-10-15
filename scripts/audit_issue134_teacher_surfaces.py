"""Issue #134 Slice 0: deterministic, source-only teacher-surface inventory.

The output describes source-code sites, never a teacher workspace or student data.
It intentionally finds *candidates*, not a claim that every match is a UI leak.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Final

AUDIT_SCHEMA: Final[int] = 1
BASELINE_COMMIT: Final[str] = "65823415f03ab1d5209ad62d48859c02a33fb8a0"
CORE_RELEASE_TAG: Final[str] = "v0.6.6"
CORE_RELEASE_COMMIT: Final[str] = "35af5d0642e84a625cd143285c4ef6de98dbcca4"
CORE_RELEASE_WHEEL_SHA256: Final[str] = (
    "d6d21e426092b0329bcfd69b6fbee44c345edc46794a914d847d5ea73a2b7301"
)

# Broad by design: include even internal references so the audit can classify them.
IDENTITY_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?i)(?:sha[-_ ]?256|\bdigest\b|\bhash\b|\b[A-Za-z_]*_id\b|"
    r"\bID\b|\brevision\b|\bmanifest\b|\btimestamp\b|\bcreated_at\b|"
    r"\bsource_scan\b|\bscan_reference\b|\btarget_key\b)"
)
FUNCTION_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^def ([a-zA-Z_][a-zA-Z_0-9]*)\("
)
TECHNICAL_FUNCTIONS: Final[frozenset[str]] = frozenset(
    {"_routing_technical_detail_lines", "_show_routing_technical_details"}
)
ENTRYPOINTS: Final[tuple[str, ...]] = (
    "concord/menu_artifact.py",
    "concord/menu_scoring.py",
    "concord/menu_packet_generation.py",
    "concord/menu_scan.py",
    "concord/menu_publication.py",
    "concord/menu_template.py",
    "concord/menu_packet.py",
    "concord/menu_group.py",
    "concord/menu_session.py",
    "concord/menu_activity.py",
)


def classify(line: str, function: str) -> str:
    """Conservative triage, NOT an assertion that a site is safe."""
    if function in TECHNICAL_FUNCTIONS or "technical" in function:
        return "advanced_technical_candidate"
    if '"' in line or "'" in line or "print(" in line:
        if "prompt_text(" in line or (" ID" in line and "= " not in line):
            return "teacher_input_candidate"
        return "teacher_display_candidate"
    return "internal_reference_review"


def source_files(root: Path) -> tuple[Path, ...]:
    directory = root / "concord"
    return tuple(sorted(directory.glob("menu_*.py"))) + (directory / "menu.py",)


def collect(root: Path) -> dict[str, Any]:
    """Inventory every menu module and every identity-like source occurrence."""
    root = root.resolve()
    result: list[dict[str, object]] = []
    source_checksums: dict[str, str] = {}
    counts: dict[str, dict[str, int]] = {}
    for path in source_files(root):
        if not path.is_file():
            raise FileNotFoundError(f"Expected teacher menu source absent: {path.name}")
        relative = path.relative_to(root).as_posix()
        raw = path.read_bytes()
        source_checksums[relative] = hashlib.sha256(raw).hexdigest()
        current_function = "<module>"
        for line_number, source_line in enumerate(
            raw.decode("utf-8-sig").splitlines(), start=1
        ):
            match = FUNCTION_PATTERN.match(source_line)
            if match:
                current_function = match.group(1)
            if not IDENTITY_PATTERN.search(source_line):
                continue
            label = classify(source_line, current_function)
            result.append(
                {
                    "path": relative,
                    "line": line_number,
                    "function": current_function,
                    "triage": label,
                    "source": source_line.strip()[:240],
                }
            )
            file_counts = counts.setdefault(relative, {})
            file_counts[label] = file_counts.get(label, 0) + 1
    return {
        "schema": AUDIT_SCHEMA,
        "baseline_commit": BASELINE_COMMIT,
        "core_release": CORE_RELEASE_TAG,
        "core_release_commit": CORE_RELEASE_COMMIT,
        "core_wheel_sha256": CORE_RELEASE_WHEEL_SHA256,
        "scope": "source-only; no workspace records; classifications are triage",
        "source_checksums": source_checksums,
        "counts": counts,
        "findings": result,
    }


def canonical_bytes(result: dict[str, Any]) -> bytes:
    return (json.dumps(result, indent=2, ensure_ascii=True) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root: Path = args.root.resolve()
    output: Path = args.output or (
        root / "docs" / "validation" / "issue134_teacher_surface_inventory.json"
    )
    inventory = collect(root)
    missing = set(ENTRYPOINTS) - set(inventory["source_checksums"])
    if missing:
        raise RuntimeError(
            f"Issue #134 inventory omitted required entry points: {sorted(missing)}"
        )
    encoded = canonical_bytes(inventory)
    if args.check:
        if not output.is_file() or output.read_bytes() != encoded:
            raise RuntimeError(
                "Issue #134 source inventory drifted; "
                "review and regenerate deliberately."
            )
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(encoded)
    print(
        "Issue #134 teacher source inventory: "
        f"{len(inventory['source_checksums'])} files; "
        f"{len(inventory['findings'])} candidate lines; "
        f"{'CHECK PASS' if args.check else 'WRITTEN'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Manual Windows Core v0.6.6 long-path viewer acceptance (synthetic PDF).

Run only in an environment with published Core 0.6.6 installed. The dispatch
mode intercepts the shell call; physical mode requires a human-confirmed viewer.
Both modes use an intentionally generated, non-student PDF over 296 WCHARs.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


def _check_environment() -> None:
    installed = importlib.metadata.version("pds-core")
    if installed != "0.6.6":
        raise RuntimeError(f"Expected installed pds-core 0.6.6; found {installed}.")
    import pds_core

    if pds_core.__version__ != installed:
        raise RuntimeError("Imported Core version and installed metadata differ.")
    root = Path(sys.prefix).resolve()
    if pds_core.__file__ is None:
        raise RuntimeError("Imported Core has no package file.")
    if not Path(pds_core.__file__).resolve().is_relative_to(root):
        raise RuntimeError("Imported Core comes from outside the active environment.")
    if sys.platform != "win32":
        raise RuntimeError("Physical Windows viewer qualification requires Windows.")


def _path_units(path: Path) -> int:
    return len(str(path).encode("utf-16-le")) // 2


def _write_synthetic_pdf(root: Path) -> Path:
    from PIL import Image

    folder = root
    while _path_units(folder / "issue134_test.pdf") < 300:
        folder /= "issue134-longpath-verified-viewer-fixture"
    folder.mkdir(parents=True)
    pdf = folder / "issue134_test.pdf"
    with Image.new("RGB", (400, 220), "white") as page:
        page.save(pdf, format="PDF")
    if _path_units(pdf) < 296 or not pdf.is_file():
        raise RuntimeError("Deep synthetic PDF fixture was not created.")
    return pdf


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _probe_dispatch(pdf: Path) -> None:
    from pds_core.local_open import open_local_path

    seen: list[Path] = []

    def capture(target: str | os.PathLike[str]) -> None:
        candidate = Path(target)
        if _path_units(candidate) > 240:
            raise AssertionError("Core did not shorten the Windows viewer handoff.")
        if not candidate.is_file() or not os.path.samefile(candidate, pdf):
            raise AssertionError("The viewer alias is not the exact source PDF.")
        seen.append(candidate)

    # Intercept only the operating-system handoff, not Core's junction creation.
    with patch.object(os, "startfile", capture):
        result = open_local_path(pdf)
    if result != pdf.resolve() or len(seen) != 1:
        raise AssertionError("Core did not dispatch the exact canonical PDF once.")
    print("Core 0.6.6 Windows viewer alias dispatch: VERIFIED")
    print("This intercepts the shell call; it does NOT prove the PDF viewer displayed.")


def _probe_physical(pdf: Path) -> None:
    from pds_core.local_open import open_local_path

    result = open_local_path(pdf)
    if result != pdf.resolve():
        raise AssertionError("Core did not return the exact canonical PDF path.")
    print("Operating-system viewer request submitted for a deep synthetic PDF.")
    answer = input(
        "Did the default PDF viewer actually display the test page? [yes/no] "
    )
    if answer.strip().casefold() != "yes":
        raise RuntimeError("Physical PDF-viewer acceptance NOT confirmed.")
    print("Core 0.6.6 real Windows PDF viewer: PHYSICALLY CONFIRMED")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("dispatch", "physical"), required=True)
    args = parser.parse_args()
    _check_environment()
    with tempfile.TemporaryDirectory(prefix="concord-issue134-viewer-") as raw:
        pdf = _write_synthetic_pdf(Path(raw))
        before = _digest(pdf)
        if args.mode == "dispatch":
            _probe_dispatch(pdf)
        else:
            _probe_physical(pdf)
        if _digest(pdf) != before:
            raise RuntimeError("Opening changed the canonical fixture PDF.")
        print("Canonical PDF SHA-256 preserved; no Concord records written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

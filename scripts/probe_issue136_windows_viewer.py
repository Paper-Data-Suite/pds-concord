"""Synthetic Windows Core 0.6.6 viewer acceptance for PDF, HTML and folder.

Dispatch intercepts the Windows shell call and checks short junction aliases.
Physical mode additionally REQUIRES a human to confirm all three viewers.
Neither mode accesses a Paper Data Suite workspace or student records.
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


class ViewerQualificationError(RuntimeError):
    """A viewer acceptance precondition or requested check failed."""


def _units(path: Path) -> int:
    return len(str(path).encode("utf-16-le")) // 2


def _validate_core() -> None:
    if sys.platform != "win32":
        raise ViewerQualificationError("A real Windows host is required.")
    version = importlib.metadata.version("pds-core")
    if version != "0.6.6":
        raise ViewerQualificationError("The installed Core must be exactly 0.6.6.")
    import pds_core

    if pds_core.__version__ != version or pds_core.__file__ is None:
        raise ViewerQualificationError("Core package/version provenance disagrees.")
    if not Path(pds_core.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()):
        raise ViewerQualificationError("Core was not imported from this environment.")


def _fixtures(root: Path) -> tuple[Path, Path, Path]:
    from PIL import Image, ImageDraw

    folder = root
    while _units(folder) < 310:
        folder /= "concord136-longpath-synthetic-viewer-fixture"
    if _units(folder) < 296:
        raise ViewerQualificationError("Fixture directory path was not deep enough.")
    folder.mkdir(parents=True)
    pdf = folder / "concord136_viewer_test.pdf"
    html = folder / "concord136_viewer_test.html"
    with Image.new("RGB", (650, 250), "white") as canvas:
        draw = ImageDraw.Draw(canvas)
        draw.text((45, 88), "CONCORD #136  --  SYNTHETIC PDF VIEWER TEST", fill="black")
        draw.text(
            (45, 130), "Confirm this page is visible in your PDF viewer.", fill="black"
        )
        canvas.save(pdf, format="PDF")
    html.write_text(
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<title>Concord #136 synthetic HTML viewer test</title></head>"
        "<body style='font:24px sans-serif;padding:40px'>"
        "<h1>CONCORD #136 -- SYNTHETIC HTML VIEWER TEST</h1>"
        "<p>Confirm this page is visible in your browser.</p></body></html>",
        encoding="utf-8",
    )
    if (
        not pdf.is_file()
        or not html.is_file()
        or min(_units(folder), _units(pdf), _units(html)) < 296
    ):
        raise ViewerQualificationError("All three synthetic targets must be deep.")
    return pdf, html, folder


def _files_digest(pdf: Path, html: Path) -> tuple[str, str]:
    return (
        hashlib.sha256(pdf.read_bytes()).hexdigest(),
        hashlib.sha256(html.read_bytes()).hexdigest(),
    )


def _dispatch(targets: tuple[Path, Path, Path]) -> None:
    from pds_core.local_open import open_local_path

    for target in targets:
        captured: list[Path] = []

        def capture(raw: str | os.PathLike[str]) -> None:
            short = Path(raw)
            if _units(short) > 240:
                raise ViewerQualificationError("Core handoff exceeded 240 WCHARs.")
            if not short.exists() or not os.path.samefile(short, target):
                raise ViewerQualificationError("Alias did not identify exact target.")
            if short.resolve() != target.resolve():
                raise ViewerQualificationError("Alias resolved to a different target.")
            captured.append(short)

        with patch.object(os, "startfile", capture):
            result = open_local_path(target)
        if result != target.resolve() or len(captured) != 1:
            raise ViewerQualificationError("Core did not dispatch exactly once.")
        kind = "folder" if target.is_dir() else target.suffix
        print(f"Core alias dispatch, {kind}: PASS", flush=True)
    print("Alias dispatch is NOT human-confirmed application display.", flush=True)


def _physical(targets: tuple[Path, Path, Path]) -> None:
    from pds_core.local_open import open_local_path

    for target, label in zip(targets, ("PDF viewer", "HTML browser", "file Explorer")):
        print(f"Opening synthetic {label} target with Core 0.6.6.", flush=True)
        result = open_local_path(target)
        if result != target.resolve():
            raise ViewerQualificationError("Core returned an unexpected source.")
        confirmed = input(
            f"Did {label} ACTUALLY display the synthetic target? [YES/no] "
        )
        if confirmed.strip() != "YES":
            raise ViewerQualificationError(
                f"{label} physical display was not explicitly confirmed."
            )
        print(f"Core 0.6.6 physical {label}: HUMAN CONFIRMED", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("dispatch", "physical"), required=True)
    args = parser.parse_args()
    _validate_core()
    with tempfile.TemporaryDirectory(prefix="concord-issue136-viewer-") as raw:
        targets = _fixtures(Path(raw))
        pdf, html, folder = targets
        before = _files_digest(pdf, html)
        entries = tuple(sorted(child.name for child in folder.iterdir()))
        if args.mode == "dispatch":
            _dispatch(targets)
        else:
            _physical(targets)
        if (
            _files_digest(pdf, html) != before
            or tuple(sorted(child.name for child in folder.iterdir())) != entries
        ):
            raise ViewerQualificationError("Synthetic source bytes or entries changed.")
        print("Canonical PDF/HTML SHA-256 and folder contents unchanged: PASS")
    if args.mode == "physical":
        print("Core 0.6.6 human-confirmed PDF/HTML/folder acceptance: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

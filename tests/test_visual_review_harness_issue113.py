from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_visual_review_issue113.py"
DOC = ROOT / "docs" / "v0.3.1-starter-subject-relationships.md"


def _source() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_issue113_visual_harness_compiles_and_has_prepare_approve_stages() -> None:
    source = _source()
    ast.parse(source)
    assert 'subparsers.add_parser("prepare")' in source
    assert 'subparsers.add_parser("approve")' in source
    assert "--visual-inspection-confirmed" in source
    assert "OWNER CLASSIFICATION REQUIRED" in source


def test_issue113_visual_harness_covers_exact_five_v2_starters() -> None:
    source = _source()
    for starter_key in (
        "fishbowl_observer",
        "talk_moves_observer",
        "peer_review_writing",
        "peer_review_presentation",
        "peer_design_code_review",
    ):
        assert f'starter_key="{starter_key}"' in source
    assert source.count("VisualCase(") == 5
    assert 'expected_orientation="landscape"' in source
    assert source.count('expected_orientation="portrait"') == 4
    assert 'expected_page_count=2' in source
    assert 'subject_mode="group"' in source
    assert source.count('subject_mode="student"') == 2
    assert source.count('subject_mode="session"') == 2


def test_issue113_visual_harness_stresses_long_realistic_identity_text() -> None:
    source = _source()
    required = (
        "english12-advanced-composition-period-2-2026",
        "Alexandria",
        "Montgomery-Williams",
        "Christopher",
        "Van-Der-Meer-Santiago",
        (
            "Socratic Seminar — Evidence, Memory, Responsibility, and "
            "Competing Interpretations"
        ),
        "Community Accessibility Design Team — Prototype Alpha",
    )
    for fragment in required:
        assert fragment in source


def test_issue113_visual_harness_uses_real_packet_rendering_and_qr_gate() -> None:
    source = _source()
    required = (
        "prepare_packet_instantiation(",
        "commit_packet_instantiation(",
        "render_packet_instance(",
        "load_route_registration(",
        "parse_pds2_payload(",
        "pypdfium2.PdfDocument(",
        "page.render(scale=2).to_pil()",
        "zxingcpp.read_barcodes(image)",
        "pds2_qr_decode_verified",
        "route module_details contract changed",
        "physical fallback leaked student IDs",
    )
    for fragment in required:
        assert fragment in source


def test_issue113_visual_harness_persists_shareable_bundle() -> None:
    source = _source()
    required = (
        'BUNDLE_ZIP = "issue113-visual-review-bundle.zip"',
        'MANIFEST = "manifest.json"',
        'CHECKLIST = "visual-review-checklist.md"',
        'PDF_DIR = "pdfs"',
        'PREVIEW_DIR = "previews"',
        "_require_clean_checkout(source_root)",
        "_require_fresh_run_root(run_root)",
        "workspace",
    )
    for fragment in required:
        assert fragment in source
    assert "git add" not in source
    assert "git commit" not in source


def test_issue113_visual_harness_requires_explicit_owner_classification() -> None:
    source = _source()
    for argument in (
        "--fishbowl",
        "--talk-moves",
        "--writing",
        "--presentation",
        "--design-code",
        "--overall",
    ):
        assert argument in source
    assert "classification_source" in source
    assert "explicit owner/tester CLI input" in source
    assert "overall PASS is invalid while any starter case is not PASS" in source
    assert "overall visual review: PASS" not in source


def test_issue113_visual_documentation_points_to_persistent_harness() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = (
        "## Issue #113 visual-review qualification",
        "scripts/run_visual_review_issue113.py prepare",
        "scripts/run_visual_review_issue113.py approve",
        "issue113-visual-review-bundle.zip",
        "OWNER CLASSIFICATION REQUIRED",
        "generated PDFs",
        "raster previews",
        "must not be committed",
    )
    for fragment in required:
        assert fragment in text

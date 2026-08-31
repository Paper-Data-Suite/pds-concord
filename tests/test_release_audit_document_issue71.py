from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs" / "v0.3.0-release-audit.md"
DOCS_INDEX = ROOT / "docs" / "README.md"


def test_issue71_release_audit_records_required_baseline_and_boundaries() -> None:
    text = AUDIT.read_text(encoding="utf-8")

    required = (
        "Status:** COMPLETE",
        "33bd916978da21f4a317a1509adc77981a25aa26",
        "pds-core>=0.6.3,<0.7",
        "98d7596ce0eed26e4d56a17bbbbd644db3014259b56a45783a173fe8237af5e5",
        "GroupPlan != Group != GroupMembership",
        "TemplateDefinition != TemplateVersion",
        "PacketVersion != PacketInstance",
        "Role preset != RoleAssignment",
        "Score != reusable configuration",
        "scan return != Artifact Review",
        "missing signal != lowest band",
        "attention != readiness",
        "paper_data_suite.module_operations",
        "concord = concord.pds_operations:get_module_operations_profile",
        "0001 — Concord Module Boundaries",
        "0004 — Contextual Groups, Memberships, and Roles",
        "0013 — Keep Activity-Specific Structures Optional",
        "0015 — Publish Versioned Concord Academic Result Manifests "
    "Through the Core Registry",
        "11 CONFORMS",
        "4 CONFORMS — DEFERRED SURFACE NOT REQUIRED BY v0.3.0",
        "0 BLOCKERS",
        "540.941s",
        "TEACHER USABILITY: CONFORMS",
        "ATTENTION / NEXT ACTIONS: CONFORMS",
        "INSTALLED INTEROPERABILITY: CONFORMS",
        "ARCHITECTURE AUDIT: CONFORMS — 0 BLOCKERS",
        "PRIVACY AUDIT: CONFORMS — 0 BLOCKERS",
        "USABILITY AUDIT: CONFORMS — 0 BLOCKERS",
        "INTEROPERABILITY AUDIT: CONFORMS — 0 BLOCKERS",
        "RELEASE ARTIFACT AUDIT: PASS — EXACT ARTIFACTS FROZEN AND "
        "PUBLISHED",
        "PHYSICAL PATH: PASS — ISSUE #70 QUALIFICATION INHERITED; "
        "NO RERUN REQUIRED",
        "1,947.167s",
        "BEHAVIOR-CHANGING PHYSICAL-PATH DELTA: NO",
        "FRESH-DOWNLOAD VERIFICATION: PASS",
        "FINAL RELEASE VERDICT: PASS",
        "fe37f9fca3dd7894a86f5a5c4e74bbe09c1e84ed",
        "dd827f7059c91c79bd69b6190b3c673d6b3bbc02bc25fa666286bbf5883c5e12",
        "454ecb87bee50ec6a54b6e17c0d38ea14c3c7fb417a8926e2b32090dba0dc3db",
        "869cb7d6247cc8ff9e7136cad7b0e775015b64c7ef33c868a51bdf73b9d4e6f9",
        "installed provenance: PASS",
        "installed module-operations smoke: PASS",
    )
    for phrase in required:
        assert phrase in text


def test_issue71_release_audit_carries_forward_issue70_physical_evidence() -> None:
    text = AUDIT.read_text(encoding="utf-8")

    required = (
        "94b9b2ef1b65a256b079cd71fb1ce09c83a677e42a41bbdc09c22f52b1514dbe",
        "804bfee0c1df02788fd992784a032b8271c13c7a51746ae1eb1beab1cbbe25aa",
        "6 packets",
        "10 physical pages",
        "NO RERUN REQUIRED",
    )
    for phrase in required:
        assert phrase in text

    assert "FINAL RELEASE VERDICT: PASS" in text


def test_docs_index_links_current_issue71_release_audit() -> None:
    index = DOCS_INDEX.read_text(encoding="utf-8")
    assert "v0.3.0-release-audit.md" in index
    assert "PENDING OWNER" not in index

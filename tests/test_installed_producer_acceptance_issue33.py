from __future__ import annotations

import inspect
from dataclasses import replace
from pathlib import Path

import pytest
from pds_core.routing_models import ModuleWorkRef

import concord.academic_result_publication as publication_module
from concord.academic_result_manifest import EvidenceReferenceProjection
from scripts import smoke_test_wheel
from scripts import verify_installed_producer_acceptance as acceptance

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_installed_producer_acceptance.py"


def test_issue33_stage_contract_is_bounded_and_complete() -> None:
    assert acceptance.STAGES == (
        "installed provenance",
        "synthetic native workflow",
        "academic-work registration",
        "manifest revision 1",
        "public reader revision 1",
        "initial publication",
        "publication replay",
        "catalog revision 1",
        "Core verification revision 1",
        "authorized artifact revision 1",
        "native correction",
        "manifest revision 2",
        "supersession",
        "catalog revision 2",
        "Core verification revision 2",
        "historical artifact",
        "withdrawal",
        "final catalog",
        "registry audit",
        "immutability",
    )
    failure = acceptance.AcceptanceFailure(
        "registry audit", "synthetic bounded failure"
    )
    assert str(failure) == "registry audit: synthetic bounded failure"
    with pytest.raises(ValueError):
        acceptance.AcceptanceFailure("registry audit", "private\npayload")


def test_issue33_uses_only_synthetic_fixed_identities() -> None:
    assert acceptance.CLASS_ID == "acceptance_class"
    assert acceptance.ACTIVITY_ID == "acceptance_activity"
    assert acceptance.SESSION_ID == "acceptance_session"
    assert acceptance.GROUP_ID == "acceptance_group"
    assert acceptance.STUDENT_1 == "synthetic_student_1"
    assert acceptance.STUDENT_2 == "synthetic_student_2"
    assert acceptance.STUDENT_1 != acceptance.STUDENT_2


def test_issue33_rejects_an_unexpected_inferred_score() -> None:
    unexpected = (
        *acceptance.REVISION_ONE_SCORE_POPULATION,
        (
            "unexpected_membership_score",
            ("core_student", acceptance.STUDENT_1, "core"),
        ),
    )
    with pytest.raises(
        acceptance.AcceptanceFailure,
        match="unexpected, missing, duplicate, or inferred Score target",
    ):
        acceptance._require_exact_score_population(
            unexpected,
            acceptance.REVISION_ONE_SCORE_POPULATION,
            stage="synthetic native workflow",
        )


def test_synthetic_artifact_gate_requires_the_complete_exact_request() -> None:
    evidence = EvidenceReferenceProjection(
        evidence_kind="artifact_instance",
        owning_system="concord",
        record_id=acceptance.ARTIFACT_ID,
        contract_version=None,
        source_publication_reference=None,
        immutable_source_version=None,
        locator=None,
        subject_context=(),
        moderation_requirement="not_required",
    )
    request = acceptance.AcademicResultArtifactAuthorizationRequest(
        work=acceptance._work(),
        record_set_id="academic_results",
        record_set_revision=1,
        source_snapshot_revision=17,
        score_record_id=acceptance.STUDENT_SCORE,
        score_evidence_link_id=acceptance.EVIDENCE_LINK_ID,
        evidence_reference=evidence,
        purpose=acceptance.PURPOSE,
    )
    gate = acceptance._ExactAuthorizationGate(request)
    assert gate.authorize(request).status == "allowed"

    changed = (
        replace(request, record_set_revision=2),
        replace(request, source_snapshot_revision=18),
        replace(
            request,
            work=ModuleWorkRef(
                "concord", acceptance.CLASS_ID, "changed_activity"
            ),
        ),
        replace(request, score_record_id="changed_score"),
        replace(request, score_evidence_link_id="changed_link"),
        replace(
            request,
            evidence_reference=replace(evidence, record_id="changed_artifact"),
        ),
        replace(request, purpose="changed purpose"),
    )
    assert all(gate.authorize(candidate).status == "denied" for candidate in changed)


def test_issue33_harness_has_no_sibling_or_direct_registry_dependency() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    for forbidden_import in (
        "import scoreform",
        "import quillan",
        "import portia",
        "import meridian",
        "import vitrine",
        "import sqlite3",
        "unittest.mock",
    ):
        assert forbidden_import not in source
    assert ".write_text(" not in source
    assert ".write_bytes(" not in source
    assert "audit_academic_registry(" in source
    assert "discover_installed_producer_profiles=True" in source
    assert "require_producer_profiles=True" in source
    assert "require_catalog=True" in source


def test_wheel_smoke_runs_read_only_checks_before_issue33_acceptance() -> None:
    source = inspect.getsource(smoke_test_wheel.smoke_test)
    acceptance_call = source.index("verify_installed_producer_acceptance.py")
    assert source.index("Publication-profile discovery") < acceptance_call
    assert source.index("Public reader smoke") < acceptance_call
    assert source.index("Read-only CLI smoke") < acceptance_call
    assert source.index("_workflow_smoke_code()") < acceptance_call
    assert "_wheel_version(concord_wheel)" in source


def test_publication_verification_uses_core_canonical_capability_order() -> None:
    verify_source = inspect.getsource(publication_module._verify_publication)
    reload_source = inspect.getsource(
        publication_module._stored_manifest_for_publication
    )
    expected = "tuple(sorted(derive_manifest_capabilities"
    assert expected in "".join(verify_source.split())
    assert expected in "".join(reload_source.split())

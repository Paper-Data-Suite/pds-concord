from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.academic_result_share_attention as share
from concord.academic_result_manifest_generation import (
    ConcordManifestGenerationValidationError,
)
from concord.academic_result_publication import (
    ConcordAcademicResultPublicationIntegrityError,
)
from concord.academic_work_registration import (
    ConcordAcademicWorkRegistrationIntegrityError,
)


def _registration() -> SimpleNamespace:
    return SimpleNamespace(registration_revision=2)


def _context() -> SimpleNamespace:
    return SimpleNamespace(snapshot_revision=9)


def _producer_head(revision: int = 1) -> SimpleNamespace:
    return SimpleNamespace(revision=revision)


def _core_head(
    revision: int,
    *,
    digest: str,
) -> SimpleNamespace:
    return SimpleNamespace(
        record_set_revision=revision,
        manifest_digest=digest,
    )


def _series(
    *,
    producer_revision: int | None,
    core_head: object | None = None,
    withdrawn: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        producer_head=(
            None if producer_revision is None else _producer_head(producer_revision)
        ),
        core_head=core_head,
        core_head_withdrawal=(object() if withdrawn else None),
    )


def _preview(
    disposition: str,
    revision: int,
    digest: str,
) -> SimpleNamespace:
    return SimpleNamespace(
        disposition=disposition,
        revision=revision,
        sha256=digest,
    )


def _patch_common(
    monkeypatch: pytest.MonkeyPatch,
    *,
    series: object,
    preview: object,
) -> None:
    monkeypatch.setattr(
        share,
        "load_current_concord_academic_work_registration",
        lambda *_a, **_k: _registration(),
    )
    monkeypatch.setattr(
        share,
        "load_managed_activity_registration_context",
        lambda *_a, **_k: _context(),
    )
    monkeypatch.setattr(
        share,
        "load_concord_publication_series_status",
        lambda *_a, **_k: series,
    )
    monkeypatch.setattr(
        share,
        "preview_academic_result_manifest",
        lambda *_a, **_k: preview,
    )


def test_no_registration_means_share_workflow_is_inactive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        share,
        "load_current_concord_academic_work_registration",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        share,
        "load_concord_publication_series_status",
        lambda *_a, **_k: pytest.fail("publication state must not be read"),
    )
    monkeypatch.setattr(
        share,
        "preview_academic_result_manifest",
        lambda *_a, **_k: pytest.fail("manifest preview must not be built"),
    )
    result = share.inspect_academic_result_share_attention_state(
        "class-1", "activity-1", workspace_root=Path("workspace")
    )
    assert result.status == "inactive"


def test_registered_changed_result_needs_manifest_before_publication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_common(
        monkeypatch,
        series=_series(producer_revision=1),
        preview=_preview("would_create", 2, "b" * 64),
    )
    result = share.inspect_academic_result_share_attention_state(
        "class-1", "activity-1"
    )
    assert result.status == "manifest_needed"


def test_current_manifest_without_publication_is_ready_for_explicit_publish(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    digest = "c" * 64
    _patch_common(
        monkeypatch,
        series=_series(producer_revision=1),
        preview=_preview("would_reuse", 1, digest),
    )
    result = share.inspect_academic_result_share_attention_state(
        "class-1", "activity-1"
    )
    assert result.status == "publish_ready"


def test_newer_current_manifest_is_ready_for_explicit_supersession(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_common(
        monkeypatch,
        series=_series(
            producer_revision=2,
            core_head=_core_head(1, digest="d" * 64),
        ),
        preview=_preview("would_reuse", 2, "e" * 64),
    )
    result = share.inspect_academic_result_share_attention_state(
        "class-1", "activity-1"
    )
    assert result.status == "supersede_ready"


def test_exact_current_publication_produces_no_share_attention_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    digest = "f" * 64
    _patch_common(
        monkeypatch,
        series=_series(
            producer_revision=3,
            core_head=_core_head(3, digest=digest),
        ),
        preview=_preview("would_reuse", 3, digest),
    )
    result = share.inspect_academic_result_share_attention_state(
        "class-1", "activity-1"
    )
    assert result.status == "current"


def test_withdrawn_head_is_explicit_recovery_state_without_preview(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_common(
        monkeypatch,
        series=_series(
            producer_revision=1,
            core_head=_core_head(1, digest="1" * 64),
            withdrawn=True,
        ),
        preview=_preview("would_reuse", 1, "1" * 64),
    )
    monkeypatch.setattr(
        share,
        "preview_academic_result_manifest",
        lambda *_a, **_k: pytest.fail("withdrawal state should short-circuit preview"),
    )
    result = share.inspect_academic_result_share_attention_state(
        "class-1", "activity-1"
    )
    assert result.status == "withdrawn"


@pytest.mark.parametrize(
    "source",
    ("registration", "series", "preview"),
)
def test_inconsistent_existing_share_state_requires_inspection(
    monkeypatch: pytest.MonkeyPatch,
    source: str,
) -> None:
    _patch_common(
        monkeypatch,
        series=_series(producer_revision=1),
        preview=_preview("would_reuse", 1, "2" * 64),
    )
    if source == "registration":
        monkeypatch.setattr(
            share,
            "load_current_concord_academic_work_registration",
            lambda *_a, **_k: (_ for _ in ()).throw(
                ConcordAcademicWorkRegistrationIntegrityError("synthetic")
            ),
        )
    elif source == "series":
        monkeypatch.setattr(
            share,
            "load_concord_publication_series_status",
            lambda *_a, **_k: (_ for _ in ()).throw(
                ConcordAcademicResultPublicationIntegrityError("synthetic")
            ),
        )
    else:
        monkeypatch.setattr(
            share,
            "preview_academic_result_manifest",
            lambda *_a, **_k: (_ for _ in ()).throw(
                ConcordManifestGenerationValidationError("synthetic")
            ),
        )
    result = share.inspect_academic_result_share_attention_state(
        "class-1", "activity-1"
    )
    assert result.status == "needs_inspection"


def test_backward_or_digest_inconsistent_series_requires_inspection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_common(
        monkeypatch,
        series=_series(
            producer_revision=1,
            core_head=_core_head(2, digest="3" * 64),
        ),
        preview=_preview("would_reuse", 1, "4" * 64),
    )
    result = share.inspect_academic_result_share_attention_state(
        "class-1", "activity-1"
    )
    assert result.status == "needs_inspection"


def test_share_projection_exposes_no_publication_or_manifest_internals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "student-secret-publication-id"
    _patch_common(
        monkeypatch,
        series=SimpleNamespace(
            producer_head=_producer_head(2),
            core_head=SimpleNamespace(
                record_set_revision=1,
                manifest_digest="5" * 64,
                publication_id=secret,
            ),
            core_head_withdrawal=None,
        ),
        preview=_preview("would_reuse", 2, "6" * 64),
    )
    result = share.inspect_academic_result_share_attention_state(
        "class-1", "activity-1"
    )
    assert result.status == "supersede_ready"
    assert secret not in repr(result)
    assert "5" * 64 not in repr(result)
    assert "6" * 64 not in repr(result)

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    ClassMetadataReadError,
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.module_operations import ModuleOperationsRequest
from pds_core.routing_models import ModuleWorkRef, RoutingModelError

import concord.readiness_provider as provider
from concord.storage_errors import (
    ConcordStorageIntegrityError,
    ConcordStorageReadError,
)


def _workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    root.mkdir()
    return root


def _class(root: Path, class_id: str = "class-1") -> None:
    timestamp = datetime(2026, 8, 28, tzinfo=timezone.utc)
    metadata = create_class_metadata(
        class_id,
        "2026-2027",
        created_at=timestamp,
    )
    write_class_metadata_for_class(root, metadata)


def _snapshot(root: Path) -> tuple[tuple[str, bytes | None], ...]:
    result: list[tuple[str, bytes | None]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        result.append((relative, path.read_bytes() if path.is_file() else None))
    return tuple(result)


def test_missing_explicit_workspace_is_unavailable() -> None:
    report = provider.evaluate_concord_readiness(ModuleOperationsRequest())

    assert report.evaluation == "unavailable"
    assert report.ready is None
    assert [notice.code for notice in report.notices] == [
        "concord_readiness_unavailable"
    ]


def test_missing_workspace_is_unavailable_and_not_created(tmp_path: Path) -> None:
    missing = tmp_path / "missing-workspace"

    report = provider.evaluate_concord_readiness(
        ModuleOperationsRequest(workspace_root=missing)
    )

    assert report.evaluation == "unavailable"
    assert report.ready is None
    assert not missing.exists()


def test_uninspectable_workspace_is_unavailable_without_private_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_detail = "C:/private/student/location"

    def _broken(_root: object) -> Path:
        raise OSError(private_detail)

    monkeypatch.setattr(provider, "resolve_read_workspace_root", _broken)

    report = provider.evaluate_concord_readiness(
        ModuleOperationsRequest(workspace_root=tmp_path)
    )

    assert report.evaluation == "unavailable"
    assert report.ready is None
    assert private_detail not in repr(report)


def test_valid_workspace_without_class_is_ready_and_read_only(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    sentinel = root / "sentinel.txt"
    sentinel.write_text("unchanged", encoding="utf-8")
    before = _snapshot(root)

    report = provider.evaluate_concord_readiness(
        ModuleOperationsRequest(workspace_root=root)
    )

    assert report.evaluation == "evaluated"
    assert report.ready is True
    assert report.notices == ()
    assert _snapshot(root) == before


def test_safe_missing_exact_class_is_not_ready(tmp_path: Path) -> None:
    root = _workspace(tmp_path)

    report = provider.evaluate_concord_readiness(
        ModuleOperationsRequest(
            workspace_root=root,
            class_id="missing-class",
        )
    )

    assert report.evaluation == "evaluated"
    assert report.ready is False
    assert [notice.code for notice in report.notices] == [
        "concord_class_not_ready"
    ]


def test_valid_exact_class_without_roster_or_activities_is_ready(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _class(root)
    before = _snapshot(root)

    report = provider.evaluate_concord_readiness(
        ModuleOperationsRequest(
            workspace_root=root,
            class_id="class-1",
        )
    )

    assert report.evaluation == "evaluated"
    assert report.ready is True
    assert report.notices == ()
    assert _snapshot(root) == before


def test_malformed_class_metadata_is_not_ready(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    metadata_path = root / "classes" / "class-1" / "class.json"
    metadata_path.parent.mkdir(parents=True)
    metadata_path.write_text("{not-json}\n", encoding="utf-8")

    report = provider.evaluate_concord_readiness(
        ModuleOperationsRequest(
            workspace_root=root,
            class_id="class-1",
        )
    )

    assert report.evaluation == "evaluated"
    assert report.ready is False
    assert report.notices[0].code == "concord_class_not_ready"


def test_unreadable_class_metadata_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    _class(root)
    private_detail = "private metadata read failure"

    def _broken(*_args: object, **_kwargs: object) -> object:
        try:
            raise PermissionError(private_detail)
        except PermissionError as error:
            raise ClassMetadataReadError("bounded") from error

    monkeypatch.setattr(provider, "load_class_metadata_for_class", _broken)

    report = provider.evaluate_concord_readiness(
        ModuleOperationsRequest(
            workspace_root=root,
            class_id="class-1",
        )
    )

    assert report.evaluation == "unavailable"
    assert report.ready is None
    assert private_detail not in repr(report)


def test_symlink_class_path_is_unavailable_when_supported(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    target = tmp_path / "target-class"
    target.mkdir()
    class_path = root / "classes" / "class-1"
    class_path.parent.mkdir(parents=True)
    try:
        class_path.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlinks are unavailable on this test host")

    report = provider.evaluate_concord_readiness(
        ModuleOperationsRequest(
            workspace_root=root,
            class_id="class-1",
        )
    )

    assert report.evaluation == "unavailable"
    assert report.ready is None


def test_malformed_concord_work_collection_is_not_ready(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    _class(root)

    def _broken(*_args: object) -> tuple[ModuleWorkRef, ...]:
        raise ConcordStorageIntegrityError("private canonical detail")

    monkeypatch.setattr(provider, "list_activity_work_refs", _broken)

    report = provider.evaluate_concord_readiness(
        ModuleOperationsRequest(
            workspace_root=root,
            class_id="class-1",
        )
    )

    assert report.evaluation == "evaluated"
    assert report.ready is False
    assert "private canonical detail" not in repr(report)


def test_invalid_concord_work_identity_is_not_ready(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    _class(root)

    def _broken(*_args: object) -> tuple[ModuleWorkRef, ...]:
        raise RoutingModelError("invalid work identity")

    monkeypatch.setattr(provider, "list_activity_work_refs", _broken)

    report = provider.evaluate_concord_readiness(
        ModuleOperationsRequest(
            workspace_root=root,
            class_id="class-1",
        )
    )

    assert report.evaluation == "evaluated"
    assert report.ready is False


def test_unreadable_concord_work_collection_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    _class(root)
    private_detail = "C:/private/concord/work"

    def _broken(*_args: object) -> tuple[ModuleWorkRef, ...]:
        raise ConcordStorageReadError(private_detail)

    monkeypatch.setattr(provider, "list_activity_work_refs", _broken)

    report = provider.evaluate_concord_readiness(
        ModuleOperationsRequest(
            workspace_root=root,
            class_id="class-1",
        )
    )

    assert report.evaluation == "unavailable"
    assert report.ready is None
    assert private_detail not in repr(report)


def test_unexpected_provider_failure_is_not_flattened(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    _class(root)

    def _bug(*_args: object) -> tuple[ModuleWorkRef, ...]:
        raise RuntimeError("synthetic programming failure")

    monkeypatch.setattr(provider, "list_activity_work_refs", _bug)

    with pytest.raises(RuntimeError, match="synthetic programming failure"):
        provider.evaluate_concord_readiness(
            ModuleOperationsRequest(
                workspace_root=root,
                class_id="class-1",
            )
        )


def test_active_school_year_does_not_invent_readiness_semantics(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _class(root)

    report = provider.evaluate_concord_readiness(
        ModuleOperationsRequest(
            workspace_root=root,
            active_school_year="2030-2031",
            class_id="class-1",
        )
    )

    assert report.evaluation == "evaluated"
    assert report.ready is True

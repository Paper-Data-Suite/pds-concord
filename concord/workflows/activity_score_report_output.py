"""Deterministic JSON/CSV/PDF rendering and bounded local report installation."""

from __future__ import annotations

import csv
import io
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from concord.generated_paths import validate_generated_output_token
from concord.workflows.activity_score_analysis import (
    CriterionScaleTargetAnalysis,
    StandardScoreAnalysis,
)
from concord.workflows.activity_score_reports import (
    REPORT_SCOPE_ACTIVITY_ANALYSIS,
    REPORT_SCOPE_TARGET_DETAIL,
    ActivityAnalysisReport,
    PreparedScoreAnalysisReport,
    TargetDetailReport,
)

LOCAL_REPORT_SCHEMA_VERSION: Final[str] = "concord_activity_score_analysis_v1"
JSON_MEDIA_TYPE: Final[str] = "application/json; charset=utf-8"
CSV_MEDIA_TYPE: Final[str] = "text/csv; charset=utf-8"

_ACTIVITY_ALLOWED_LEAVES: Final[frozenset[str]] = frozenset(
    {
        "report.json",
        "activity_analysis.pdf",
        "activity_overview.csv",
        "criterion_distributions.csv",
        "score_dispositions.csv",
        "standards_criteria.csv",
    }
)
_TARGET_ALLOWED_LEAVES: Final[frozenset[str]] = frozenset(
    {
        "report.json",
        "target_detail.pdf",
        "target_scores.csv",
    }
)


class ScoreAnalysisReportOutputError(ValueError):
    """A rendered report or bounded local output violates the report contract."""


@dataclass(frozen=True, slots=True, kw_only=True)
class RenderedScoreAnalysisArtifact:
    """One deterministic in-memory report artifact."""

    filename: str
    media_type: str
    content: bytes


@dataclass(frozen=True, slots=True, kw_only=True)
class RenderedScoreAnalysisReport:
    """One deterministic rendered report set."""

    report_scope: str
    report_format: str
    artifacts: tuple[RenderedScoreAnalysisArtifact, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class InstalledScoreAnalysisReport:
    """Result of bounded create-or-reuse report installation."""

    package_path: Path
    output_paths: tuple[Path, ...]
    created_output_paths: tuple[Path, ...]
    reused_output_paths: tuple[Path, ...]

    @property
    def reused(self) -> bool:
        return bool(self.reused_output_paths) and not self.created_output_paths


def _target_reference(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    target = value
    return {
        "target_kind": getattr(target, "target_kind"),
        "target_id": getattr(target, "target_id"),
        "owning_system": getattr(target, "owning_system"),
        "contract_version": getattr(target, "contract_version"),
    }


def _metadata(payload: object) -> dict[str, object]:
    metadata = getattr(payload, "metadata")
    result: dict[str, object] = {
        "class_id": metadata.class_id,
        "activity_id": metadata.activity_id,
        "snapshot_revision": metadata.snapshot_revision,
        "snapshot_sha256": metadata.snapshot_sha256,
        "generated_at": metadata.generated_at,
        "report_scope": metadata.report_scope,
        "score_basis": metadata.score_basis,
    }
    target = _target_reference(metadata.target_reference)
    if target is not None:
        result["target_reference"] = target
    return result


def _slice(item: CriterionScaleTargetAnalysis) -> dict[str, object]:
    return {
        "criterion_id": item.criterion_id,
        "criterion_label": item.criterion_label,
        "criterion_kind": item.criterion_kind,
        "standard_id": item.standard_id,
        "scoring_scale_id": item.scoring_scale_id,
        "scoring_scale_lineage_id": item.scoring_scale_lineage_id,
        "scoring_scale_name": item.scoring_scale_name,
        "scoring_scale_revision": item.scoring_scale_revision,
        "scoring_scale_type": item.scoring_scale_type,
        "target_kind": item.target_kind,
        "current_judgment_count": item.current_judgment_count,
        "scored_count": item.scored_count,
        "non_score_count": item.non_score_count,
        "value_distributions": [
            {
                "value": value.value,
                "label": value.label,
                "count": value.count,
                "denominator": value.denominator,
                "percentage": value.percentage,
            }
            for value in item.value_distributions
        ],
        "disposition_distributions": [
            {
                "disposition": value.disposition,
                "count": value.count,
                "denominator": value.denominator,
                "percentage": value.percentage,
            }
            for value in item.disposition_distributions
        ],
    }


def _standard(item: StandardScoreAnalysis) -> dict[str, object]:
    return {
        "standard_id": item.standard_id,
        "standard_label": item.standard_label,
        "standard_code": item.standard_code,
        "standard_short_name": item.standard_short_name,
        "criteria": [
            {
                "criterion_id": criterion.criterion_id,
                "criterion_label": criterion.criterion_label,
                "current_judgment_count": criterion.current_judgment_count,
                "slices": [_slice(value) for value in criterion.slices],
            }
            for criterion in item.criteria
        ],
    }


def _activity_json(payload: ActivityAnalysisReport) -> dict[str, object]:
    return {
        "schema_version": LOCAL_REPORT_SCHEMA_VERSION,
        "report_kind": "local_descriptive_analysis",
        "metadata": _metadata(payload),
        "activity": {
            "activity_id": payload.metadata.activity_id,
            "activity_title": payload.activity_title,
        },
        "summary": {
            "current_score_count": payload.current_score_count,
            "target_kind_counts": [
                {
                    "target_kind": item.target_kind,
                    "score_count": item.score_count,
                }
                for item in payload.target_kind_counts
            ],
            "represented_criterion_count": payload.represented_criterion_count,
            "represented_scoring_scale_count": (
                payload.represented_scoring_scale_count
            ),
        },
        "criterion_analysis": [
            {
                "criterion_id": item.criterion_id,
                "criterion_label": item.criterion_label,
                "criterion_kind": item.criterion_kind,
                "standard_id": item.standard_id,
                "current_judgment_count": item.current_judgment_count,
                "slices": [_slice(value) for value in item.slices],
            }
            for item in payload.criterion_analyses
        ],
        "standards_criterion_view": [
            _standard(item) for item in payload.standard_analyses
        ],
        "report_boundary": {
            "statements": list(payload.boundary_statements),
        },
    }


def _target_json(payload: TargetDetailReport) -> dict[str, object]:
    detail = payload.target_detail
    return {
        "schema_version": LOCAL_REPORT_SCHEMA_VERSION,
        "report_kind": "local_descriptive_analysis",
        "metadata": _metadata(payload),
        "activity": {
            "activity_id": payload.metadata.activity_id,
            "activity_title": payload.activity_title,
        },
        "target_detail": {
            "target_kind": detail.target_reference.target_kind,
            "target_display": detail.target_label,
            "sharing_scope": detail.sharing_scope,
            "current_score_count": detail.current_score_count,
            "scores": [
                {
                    "score_record_id": item.score_record_id,
                    "criterion_id": item.criterion_id,
                    "criterion_label": item.criterion_label,
                    "criterion_kind": item.criterion_kind,
                    "standard_id": item.standard_id,
                    "scoring_scale_id": item.scoring_scale_id,
                    "scoring_scale_name": item.scoring_scale_name,
                    "scoring_scale_revision": item.scoring_scale_revision,
                    "scoring_scale_type": item.scoring_scale_type,
                    "disposition": item.disposition,
                    "value": item.value,
                    "value_label": item.value_label,
                    "basis": item.basis,
                    "session_id": item.session_id,
                    "scored_at": item.scored_at,
                }
                for item in detail.results
            ],
        },
        "report_boundary": {
            "statements": list(payload.boundary_statements),
        },
    }


def render_score_analysis_report_json(
    prepared: PreparedScoreAnalysisReport,
) -> RenderedScoreAnalysisReport:
    """Render one prepared report as deterministic versioned JSON."""
    if prepared.report_format != "json":
        raise ScoreAnalysisReportOutputError(
            "JSON rendering requires a prepared JSON report."
        )
    payload = prepared.payload
    if isinstance(payload, ActivityAnalysisReport):
        value = _activity_json(payload)
    elif isinstance(payload, TargetDetailReport):
        value = _target_json(payload)
    else:
        raise ScoreAnalysisReportOutputError(
            "Prepared report payload is unsupported."
        )
    content = (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    return RenderedScoreAnalysisReport(
        report_scope=prepared.report_scope,
        report_format="json",
        artifacts=(
            RenderedScoreAnalysisArtifact(
                filename="report.json",
                media_type=JSON_MEDIA_TYPE,
                content=content,
            ),
        ),
    )


def _csv_bytes(
    header: tuple[str, ...],
    rows: tuple[tuple[object, ...], ...],
) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _scalar_cell(value: object) -> str:
    if value is None:
        return ""
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _artifact(filename: str, content: bytes) -> RenderedScoreAnalysisArtifact:
    return RenderedScoreAnalysisArtifact(
        filename=filename,
        media_type=CSV_MEDIA_TYPE,
        content=content,
    )


def _activity_csv(
    payload: ActivityAnalysisReport,
) -> tuple[RenderedScoreAnalysisArtifact, ...]:
    overview_rows = tuple(
        (
            payload.metadata.activity_id,
            payload.activity_title,
            payload.current_score_count,
            item.target_kind,
            item.score_count,
            payload.represented_criterion_count,
            payload.represented_scoring_scale_count,
            payload.metadata.score_basis,
            payload.metadata.snapshot_revision,
        )
        for item in payload.target_kind_counts
    )
    if not overview_rows:
        overview_rows = (
            (
                payload.metadata.activity_id,
                payload.activity_title,
                payload.current_score_count,
                "",
                0,
                payload.represented_criterion_count,
                payload.represented_scoring_scale_count,
                payload.metadata.score_basis,
                payload.metadata.snapshot_revision,
            ),
        )

    distribution_rows = tuple(
        (
            criterion.criterion_id,
            criterion.criterion_label,
            item.target_kind,
            item.scoring_scale_id,
            item.scoring_scale_name,
            item.scoring_scale_revision,
            _scalar_cell(value.value),
            value.label,
            value.count,
            value.denominator,
            value.percentage,
        )
        for criterion in payload.criterion_analyses
        for item in criterion.slices
        for value in item.value_distributions
    )
    disposition_rows = tuple(
        (
            criterion.criterion_id,
            criterion.criterion_label,
            item.target_kind,
            item.scoring_scale_id,
            item.scoring_scale_name,
            item.scoring_scale_revision,
            value.disposition,
            value.count,
            value.denominator,
            value.percentage,
        )
        for criterion in payload.criterion_analyses
        for item in criterion.slices
        for value in item.disposition_distributions
    )
    standards_rows = tuple(
        (
            standard.standard_id,
            standard.standard_label,
            criterion.criterion_id,
            criterion.criterion_label,
            item.target_kind,
            item.scoring_scale_id,
            item.scoring_scale_name,
            item.scoring_scale_revision,
            item.current_judgment_count,
        )
        for standard in payload.standard_analyses
        for criterion in standard.criteria
        for item in criterion.slices
    )

    return (
        _artifact(
            "activity_overview.csv",
            _csv_bytes(
                (
                    "activity_id",
                    "activity_title",
                    "current_score_heads",
                    "target_kind",
                    "target_kind_score_count",
                    "criterion_count",
                    "scale_count",
                    "score_basis",
                    "snapshot_revision",
                ),
                overview_rows,
            ),
        ),
        _artifact(
            "criterion_distributions.csv",
            _csv_bytes(
                (
                    "criterion_id",
                    "criterion_label",
                    "target_kind",
                    "scoring_scale_id",
                    "scale_label",
                    "scale_revision",
                    "value",
                    "value_label",
                    "count",
                    "scored_denominator",
                    "percent",
                ),
                distribution_rows,
            ),
        ),
        _artifact(
            "score_dispositions.csv",
            _csv_bytes(
                (
                    "criterion_id",
                    "criterion_label",
                    "target_kind",
                    "scoring_scale_id",
                    "scale_label",
                    "scale_revision",
                    "disposition",
                    "count",
                    "current_score_denominator",
                    "percent",
                ),
                disposition_rows,
            ),
        ),
        _artifact(
            "standards_criteria.csv",
            _csv_bytes(
                (
                    "standard_id",
                    "standard_label",
                    "criterion_id",
                    "criterion_label",
                    "target_kind",
                    "scoring_scale_id",
                    "scale_label",
                    "scale_revision",
                    "recorded_current_scores",
                ),
                standards_rows,
            ),
        ),
    )


def _target_csv(
    payload: TargetDetailReport,
) -> tuple[RenderedScoreAnalysisArtifact, ...]:
    detail = payload.target_detail
    rows = tuple(
        (
            detail.target_reference.target_kind,
            detail.target_label,
            item.criterion_id,
            item.criterion_label,
            item.scoring_scale_id,
            item.scoring_scale_name,
            item.scoring_scale_revision,
            item.disposition,
            _scalar_cell(item.value),
            item.value_label or "",
            item.scored_at,
        )
        for item in detail.results
    )
    return (
        _artifact(
            "target_scores.csv",
            _csv_bytes(
                (
                    "target_kind",
                    "target_display",
                    "criterion_id",
                    "criterion_label",
                    "scoring_scale_id",
                    "scale_label",
                    "scale_revision",
                    "disposition",
                    "value",
                    "value_label",
                    "scored_at",
                ),
                rows,
            ),
        ),
    )


def render_score_analysis_report_csv(
    prepared: PreparedScoreAnalysisReport,
) -> RenderedScoreAnalysisReport:
    """Render one prepared report as deterministic teacher-analysis CSV."""
    if prepared.report_format != "csv":
        raise ScoreAnalysisReportOutputError(
            "CSV rendering requires a prepared CSV report."
        )
    payload = prepared.payload
    if isinstance(payload, ActivityAnalysisReport):
        artifacts = _activity_csv(payload)
    elif isinstance(payload, TargetDetailReport):
        artifacts = _target_csv(payload)
    else:
        raise ScoreAnalysisReportOutputError(
            "Prepared report payload is unsupported."
        )
    return RenderedScoreAnalysisReport(
        report_scope=prepared.report_scope,
        report_format="csv",
        artifacts=artifacts,
    )


def render_prepared_score_analysis_report(
    prepared: PreparedScoreAnalysisReport,
) -> RenderedScoreAnalysisReport:
    """Render one supported local report format from the prepared projection."""
    if prepared.report_format == "json":
        return render_score_analysis_report_json(prepared)
    if prepared.report_format == "csv":
        return render_score_analysis_report_csv(prepared)
    if prepared.report_format == "pdf":
        from concord.workflows.activity_score_report_pdf import (
            render_score_analysis_report_pdf,
        )

        return render_score_analysis_report_pdf(prepared)
    raise ScoreAnalysisReportOutputError(
        f"Unsupported prepared report format: {prepared.report_format}"
    )


def _allowed_leaves(scope: str) -> frozenset[str]:
    if scope == REPORT_SCOPE_ACTIVITY_ANALYSIS:
        return _ACTIVITY_ALLOWED_LEAVES
    if scope == REPORT_SCOPE_TARGET_DETAIL:
        return _TARGET_ALLOWED_LEAVES
    raise ScoreAnalysisReportOutputError(f"Unsupported report scope: {scope}")


def _validate_rendered(
    prepared: PreparedScoreAnalysisReport,
    rendered: RenderedScoreAnalysisReport,
) -> None:
    if rendered.report_scope != prepared.report_scope:
        raise ScoreAnalysisReportOutputError(
            "Rendered report scope does not match prepared scope."
        )
    if rendered.report_format != prepared.report_format:
        raise ScoreAnalysisReportOutputError(
            "Rendered report format does not match prepared format."
        )
    validate_generated_output_token(prepared.package_token)
    if prepared.package_path.name != prepared.package_token:
        raise ScoreAnalysisReportOutputError(
            "Prepared package path disagrees with its bounded token."
        )
    if (
        prepared.package_path.parent.name != "score_analysis"
        or prepared.package_path.parent.parent.name != "exports"
    ):
        raise ScoreAnalysisReportOutputError(
            "Prepared package path does not match the managed report geometry."
        )

    expected_names = tuple(path.name for path in prepared.output_paths)
    rendered_names = tuple(item.filename for item in rendered.artifacts)
    if rendered_names != expected_names:
        raise ScoreAnalysisReportOutputError(
            "Rendered artifact set does not match prepared output paths."
        )
    if len(set(rendered_names)) != len(rendered_names):
        raise ScoreAnalysisReportOutputError(
            "Rendered report contains duplicate artifact names."
        )

    allowed = _allowed_leaves(prepared.report_scope)
    for path in prepared.output_paths:
        if path.parent != prepared.package_path or path.name not in allowed:
            raise ScoreAnalysisReportOutputError(
                "Prepared report output escaped the fixed report package."
            )


def _managed_work_root(package_path: Path) -> Path:
    return package_path.parent.parent.parent


def _validate_directory(path: Path, label: str) -> None:
    if path.is_symlink() or not path.is_dir():
        raise ScoreAnalysisReportOutputError(
            f"{label} is not a regular non-symlink directory: {path}"
        )


def _prepare_parent_directories(
    package_path: Path,
) -> tuple[Path, ...]:
    managed_root = _managed_work_root(package_path)
    _validate_directory(managed_root, "Managed Concord work root")

    target_parent = package_path.parent
    try:
        relative = target_parent.relative_to(managed_root)
    except ValueError as error:
        raise ScoreAnalysisReportOutputError(
            "Report package escaped the managed Concord work root."
        ) from error

    created: list[Path] = []
    current = managed_root
    for part in relative.parts:
        current = current / part
        if current.exists() or current.is_symlink():
            _validate_directory(current, "Report parent")
            continue
        try:
            current.mkdir()
        except OSError as error:
            raise ScoreAnalysisReportOutputError(
                f"Could not create report parent {current}: {error}"
            ) from error
        created.append(current)
    return tuple(created)


def _cleanup_empty_directories(paths: tuple[Path, ...]) -> None:
    for path in reversed(paths):
        try:
            path.rmdir()
        except OSError:
            pass


def _existing_entries(
    prepared: PreparedScoreAnalysisReport,
) -> dict[str, Path]:
    package = prepared.package_path
    _validate_directory(package, "Existing report package")
    allowed = _allowed_leaves(prepared.report_scope)
    entries: dict[str, Path] = {}
    try:
        children = tuple(package.iterdir())
    except OSError as error:
        raise ScoreAnalysisReportOutputError(
            f"Could not inspect existing report package: {error}"
        ) from error
    for child in children:
        if child.name not in allowed:
            raise ScoreAnalysisReportOutputError(
                "Existing report package contains an unexpected entry: "
                f"{child.name}"
            )
        if child.is_symlink() or not child.is_file():
            raise ScoreAnalysisReportOutputError(
                "Existing report artifact is not a regular non-symlink file: "
                f"{child.name}"
            )
        entries[child.name] = child
    return entries


def _normalized_json_for_reuse(data: bytes) -> dict[str, Any] | None:
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict):
        return None
    metadata = value.get("metadata")
    if not isinstance(metadata, dict):
        return None
    generated_at = metadata.get("generated_at")
    if not isinstance(generated_at, str) or not generated_at:
        return None
    normalized = dict(value)
    normalized_metadata = dict(metadata)
    normalized_metadata.pop("generated_at")
    normalized["metadata"] = normalized_metadata
    return normalized


def _artifact_matches_existing(
    artifact: RenderedScoreAnalysisArtifact,
    existing: bytes,
) -> bool:
    if existing == artifact.content:
        return True
    if artifact.filename != "report.json":
        return False
    existing_value = _normalized_json_for_reuse(existing)
    rendered_value = _normalized_json_for_reuse(artifact.content)
    return (
        existing_value is not None
        and rendered_value is not None
        and existing_value == rendered_value
    )


def install_rendered_score_analysis_report(
    prepared: PreparedScoreAnalysisReport,
    rendered: RenderedScoreAnalysisReport,
) -> InstalledScoreAnalysisReport:
    """Create missing fixed leaves or reuse verified exact report artifacts."""
    _validate_rendered(prepared, rendered)

    package = prepared.package_path
    created_parents: tuple[Path, ...] = ()
    created_package = False
    created_files: list[Path] = []
    reused_files: list[Path] = []

    try:
        if package.exists() or package.is_symlink():
            existing = _existing_entries(prepared)
        else:
            created_parents = _prepare_parent_directories(package)
            try:
                package.mkdir()
            except FileExistsError as error:
                raise ScoreAnalysisReportOutputError(
                    "Report package appeared concurrently; generation stopped "
                    "without overwriting it."
                ) from error
            except OSError as error:
                raise ScoreAnalysisReportOutputError(
                    f"Could not create report package: {error}"
                ) from error
            created_package = True
            existing = {}

        missing: list[RenderedScoreAnalysisArtifact] = []
        for artifact in rendered.artifacts:
            path = existing.get(artifact.filename)
            if path is None:
                missing.append(artifact)
                continue
            try:
                current = path.read_bytes()
            except OSError as error:
                raise ScoreAnalysisReportOutputError(
                    f"Could not read existing report artifact "
                    f"{artifact.filename}: {error}"
                ) from error
            if not _artifact_matches_existing(artifact, current):
                raise ScoreAnalysisReportOutputError(
                    "Existing report artifact conflicts with the prepared "
                    f"immutable report: {artifact.filename}"
                )
            reused_files.append(path)

        for artifact in missing:
            target = package / artifact.filename
            try:
                with target.open("xb") as output:
                    created_files.append(target)
                    output.write(artifact.content)
                    output.flush()
                    os.fsync(output.fileno())
            except FileExistsError as error:
                raise ScoreAnalysisReportOutputError(
                    "Report artifact appeared concurrently and was not "
                    f"overwritten: {artifact.filename}"
                ) from error
            except OSError as error:
                raise ScoreAnalysisReportOutputError(
                    f"Could not write report artifact {artifact.filename}: "
                    f"{error}"
                ) from error

        outputs = tuple(package / item.filename for item in rendered.artifacts)
        return InstalledScoreAnalysisReport(
            package_path=package,
            output_paths=outputs,
            created_output_paths=tuple(created_files),
            reused_output_paths=tuple(reused_files),
        )
    except Exception:
        for path in reversed(created_files):
            try:
                path.unlink()
            except OSError:
                pass
        if created_package:
            try:
                package.rmdir()
            except OSError:
                pass
        _cleanup_empty_directories(created_parents)
        raise


def execute_prepared_score_analysis_report(
    prepared: PreparedScoreAnalysisReport,
) -> InstalledScoreAnalysisReport:
    """Render and install one already-confirmed prepared local report."""
    rendered = render_prepared_score_analysis_report(prepared)
    return install_rendered_score_analysis_report(prepared, rendered)


__all__ = [
    "CSV_MEDIA_TYPE",
    "JSON_MEDIA_TYPE",
    "LOCAL_REPORT_SCHEMA_VERSION",
    "InstalledScoreAnalysisReport",
    "RenderedScoreAnalysisArtifact",
    "RenderedScoreAnalysisReport",
    "ScoreAnalysisReportOutputError",
    "execute_prepared_score_analysis_report",
    "install_rendered_score_analysis_report",
    "render_prepared_score_analysis_report",
    "render_score_analysis_report_csv",
    "render_score_analysis_report_json",
]

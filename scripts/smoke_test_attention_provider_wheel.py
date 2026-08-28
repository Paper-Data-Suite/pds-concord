"Install Concord/Core wheels in isolation and smoke-test module operations."

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
import textwrap
import venv
from pathlib import Path


def _python(venv_root: Path) -> Path:
    return (
        venv_root / "Scripts" / "python.exe"
        if os.name == "nt"
        else venv_root / "bin" / "python"
    )


def _concord(venv_root: Path) -> Path:
    return (
        venv_root / "Scripts" / "concord.exe"
        if os.name == "nt"
        else venv_root / "bin" / "concord"
    )


def _clean_env() -> dict[str, str]:
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONNOUSERSITE"] = "1"
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    return env


def _run(command: list[str], cwd: Path) -> None:
    subprocess.run(
        command,
        cwd=cwd,
        check=True,
        env=_clean_env(),
    )


def _run_with_input(command: list[str], cwd: Path, text: str) -> None:
    subprocess.run(
        command,
        cwd=cwd,
        check=True,
        env=_clean_env(),
        input=text,
        text=True,
    )


def _smoke_code() -> str:
    return textwrap.dedent(
        """
        from __future__ import annotations

        import hashlib
        import sys
        import tempfile
        from datetime import datetime, timezone
        from importlib import metadata
        from pathlib import Path

        import concord
        import pds_core
        from pds_core.class_metadata import (
            create_class_metadata,
            write_class_metadata_for_class,
        )
        from pds_core.classes import write_class_roster
        from pds_core.module_operations import (
            MODULE_OPERATIONS_ENTRY_POINT_GROUP,
            ModuleAttentionReport,
            ModuleOperationsProfile,
            ModuleOperationsRequest,
            ModuleReadinessReport,
            invoke_module_attention,
            invoke_module_readiness,
        )
        from pds_core.provider_diagnostics import diagnose_core_providers
        from pds_core.rosters import create_roster
        from pds_core.workspace import ensure_workspace_root

        from concord.models import PlannedGroup
        from concord.workflows import (
            CreateActivityContextRequest,
            WorkflowActor,
            create_activity_context,
        )
        from concord.workflows.group_plan import (
            CreateGroupPlanRequest,
            create_group_plan,
        )

        assert metadata.version("pds-core") == "0.6.3"
        assert metadata.version("pds-concord") == "0.3.0.dev0"

        env_root = Path(sys.prefix).resolve()
        for package in (concord, pds_core):
            module_path = Path(package.__file__).resolve()
            module_path.relative_to(env_root)
            assert "site-packages" in module_path.as_posix().lower(), module_path

        for distribution in (
            "paper-data-suite",
            "scoreform",
            "quillan",
            "pds-meridian",
            "pds-portia",
            "pds-vitrine",
        ):
            try:
                metadata.version(distribution)
            except metadata.PackageNotFoundError:
                pass
            else:
                raise AssertionError(
                    f"unexpected sibling distribution installed: {distribution}"
                )

        console_entries = tuple(metadata.entry_points(group="console_scripts"))
        concord_console_entries = tuple(
            entry for entry in console_entries if entry.name == "concord"
        )
        assert len(concord_console_entries) == 1
        assert concord_console_entries[0].value == "concord.cli:main"

        operation_entries = tuple(
            metadata.entry_points(group=MODULE_OPERATIONS_ENTRY_POINT_GROUP)
        )
        concord_operation_entries = tuple(
            entry for entry in operation_entries if entry.name == "concord"
        )
        assert len(concord_operation_entries) == 1
        assert (
            concord_operation_entries[0].value
            == "concord.pds_operations:get_module_operations_profile"
        )

        diagnostics = diagnose_core_providers()
        concord_diagnostics = tuple(
            result
            for result in diagnostics
            if result.metadata.entry_point_name == "concord"
        )
        by_kind = {
            result.metadata.provider_kind: result
            for result in concord_diagnostics
        }
        assert set(by_kind) == {
            "routing_module",
            "publication_producer",
            "module_operations",
        }
        for result in by_kind.values():
            assert result.code == "provider.valid", result
            assert result.declared_identity == "concord"
            assert result.registry_conflict is False

        operations_diagnostic = by_kind["module_operations"]
        profile = operations_diagnostic.validated_profile
        assert isinstance(profile, ModuleOperationsProfile)
        assert profile.module_id == "concord"
        assert profile.attention_provider is not None
        assert profile.readiness_provider is not None

        def fingerprint(root: Path) -> tuple[tuple[str, str], ...]:
            rows = []
            for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
                if path.is_file():
                    rows.append(
                        (
                            path.relative_to(root).as_posix(),
                            hashlib.sha256(path.read_bytes()).hexdigest(),
                        )
                    )
            return tuple(rows)

        with tempfile.TemporaryDirectory(prefix="concord-operations-installed-") as raw:
            root = ensure_workspace_root(Path(raw) / "workspace")
            write_class_metadata_for_class(
                root,
                create_class_metadata(
                    "class-1",
                    "2026-2027",
                    created_at=datetime(2026, 8, 28, tzinfo=timezone.utc),
                ),
            )
            write_class_roster(
                root,
                create_roster(
                    "class-1",
                    (
                        {
                            "student_id": "student-1",
                            "last_name": "PrivateLast",
                            "first_name": "PrivateFirst",
                            "period": "1",
                        },
                    ),
                ),
            )
            actor = WorkflowActor(
                actor_id="teacher-private-id",
                display_label="Private Teacher Label",
                role_label="teacher",
            )
            created = create_activity_context(
                CreateActivityContextRequest(
                    class_id="class-1",
                    activity_id="activity-1",
                    title="Operations Acceptance Activity",
                    activity_type="project",
                    scoring_orientation="evidence_only",
                    session_id="session-1",
                    session_label="Day 1",
                    actor=actor,
                ),
                workspace_root=root,
            )
            create_group_plan(
                CreateGroupPlanRequest(
                    class_id="class-1",
                    activity_id="activity-1",
                    group_plan_id="private-plan-1",
                    strategy="manual",
                    expected_snapshot_revision=created.commit.snapshot_revision,
                    actor=actor,
                    proposed_groups=(
                        PlannedGroup(
                            planned_group_key="private-planned-group",
                            label="Private Group Label",
                            student_ids=("student-1",),
                        ),
                    ),
                ),
                workspace_root=root,
            )

            before = fingerprint(root)
            request = ModuleOperationsRequest(
                workspace_root=root,
                active_school_year="2026-2027",
                class_id="class-1",
            )

            readiness = invoke_module_readiness(profile, request)
            assert readiness.code == "module_operations.evaluated"
            assert readiness.result_validation == "passed"
            readiness_report = readiness.report
            assert isinstance(readiness_report, ModuleReadinessReport)
            assert readiness_report.evaluation == "evaluated"
            assert readiness_report.ready is True
            assert readiness_report.notices == ()
            assert fingerprint(root) == before

            invocation = invoke_module_attention(profile, request)
            assert fingerprint(root) == before

            assert invocation.code == "module_operations.evaluated"
            assert invocation.result_validation == "passed"
            report = invocation.report
            assert isinstance(report, ModuleAttentionReport)
            assert report.evaluation == "evaluated"
            assert report.notices == ()
            assert len(report.summaries) == 1

            summary = report.summaries[0]
            assert summary.code == "concord_plan_prepare"
            assert summary.label == "Group plans still need preparation"
            assert summary.count == 1
            assert summary.class_id == "class-1"
            assert summary.work_ref is not None
            assert summary.work_ref.module_id == "concord"
            assert summary.work_ref.class_id == "class-1"
            assert summary.work_ref.work_id == "activity-1"
            assert summary.action is not None
            assert summary.action.module_id == "concord"
            assert summary.action.action_id == "open_activity_plan"

            rendered = repr((readiness_report, report))
            for private_value in (
                "student-1",
                "PrivateLast",
                "PrivateFirst",
                "teacher-private-id",
                "Private Teacher Label",
                "private-plan-1",
                "private-planned-group",
                "Private Group Label",
            ):
                assert private_value not in rendered

            missing_class = invoke_module_readiness(
                profile,
                ModuleOperationsRequest(
                    workspace_root=root,
                    class_id="missing-class",
                ),
            )
            assert missing_class.code == "module_operations.evaluated"
            missing_report = missing_class.report
            assert isinstance(missing_report, ModuleReadinessReport)
            assert missing_report.evaluation == "evaluated"
            assert missing_report.ready is False
            assert tuple(notice.code for notice in missing_report.notices) == (
                "concord_class_not_ready",
            )
            assert fingerprint(root) == before

        unavailable_attention = invoke_module_attention(
            profile,
            ModuleOperationsRequest(active_school_year="2026-2027"),
        )
        assert (
            unavailable_attention.code
            == "module_operations.evaluation_unavailable"
        )
        unavailable_attention_report = unavailable_attention.report
        assert isinstance(unavailable_attention_report, ModuleAttentionReport)
        assert unavailable_attention_report.evaluation == "unavailable"
        assert unavailable_attention_report.summaries == ()
        assert tuple(
            notice.code for notice in unavailable_attention_report.notices
        ) == ("concord_attention_unavailable",)

        unavailable_readiness = invoke_module_readiness(
            profile,
            ModuleOperationsRequest(active_school_year="2026-2027"),
        )
        assert (
            unavailable_readiness.code
            == "module_operations.evaluation_unavailable"
        )
        unavailable_readiness_report = unavailable_readiness.report
        assert isinstance(unavailable_readiness_report, ModuleReadinessReport)
        assert unavailable_readiness_report.evaluation == "unavailable"
        assert unavailable_readiness_report.ready is None
        assert tuple(
            notice.code for notice in unavailable_readiness_report.notices
        ) == ("concord_readiness_unavailable",)
        """
    )


def smoke(concord_wheel: Path, core_wheel: Path) -> None:
    if not concord_wheel.is_file():
        raise FileNotFoundError(concord_wheel)
    if not core_wheel.is_file():
        raise FileNotFoundError(core_wheel)

    with tempfile.TemporaryDirectory(prefix="concord-operations-wheel-") as raw:
        work = Path(raw)
        env_root = work / "venv"
        venv.EnvBuilder(with_pip=True).create(env_root)
        python = _python(env_root)
        _run(
            [str(python), "-m", "pip", "install", str(core_wheel.resolve())],
            work,
        )
        _run(
            [str(python), "-m", "pip", "install", str(concord_wheel.resolve())],
            work,
        )
        _run([str(python), "-m", "pip", "check"], work)

        smoke_path = work / "module_operations_smoke.py"
        smoke_path.write_text(_smoke_code(), encoding="utf-8")
        _run([str(python), "-I", str(smoke_path)], work)

        concord = _concord(env_root)
        if not concord.is_file():
            raise AssertionError(f"installed concord executable is missing: {concord}")
        _run([str(concord), "--help"], work)
        _run_with_input([str(concord)], work, "Q\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("concord_wheel", type=Path)
    parser.add_argument("core_wheel", type=Path)
    args = parser.parse_args()
    smoke(args.concord_wheel, args.core_wheel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

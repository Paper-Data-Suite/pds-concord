"""Installed-wheel qualification for Concord Issue #109 Routing Review."""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import tempfile
import textwrap
import venv
from pathlib import Path

EXPECTED_CORE_SHA256 = (
    "9ace75f17b23b7f0ed6a709d531af5120db43d0325b4148d26f2d6ba1d4b3c18"
)


def _python(venv_root: Path) -> Path:
    return (
        venv_root / "Scripts" / "python.exe"
        if os.name == "nt"
        else venv_root / "bin" / "python"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(command: list[str], cwd: Path) -> None:
    subprocess.run(
        command,
        cwd=cwd,
        check=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def _smoke_code() -> str:
    return textwrap.dedent(
        r"""
        from __future__ import annotations

        import hashlib
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
        from pds_core.route_registrations import load_route_registration
        from pds_core.routes import route_registration_path
        from pds_core.scan_failure_metadata import (
            ROUTING_FAILURE_SCHEMA_VERSION,
            RoutingFailureMetadata,
            write_routing_failure_metadata,
        )
        from pds_core.scan_resolution_metadata import (
            create_scan_resolution_metadata,
            write_scan_resolution_metadata,
        )
        from pds_core.scan_retention import retain_source_scan
        from pds_core.scan_routes import routing_review_dir
        from pds_core.workspace import ensure_workspace_root

        from concord.models import PrivacyPolicy
        from concord.routing.destinations import (
            list_routing_destination_activities,
            list_routing_destination_classes,
            project_routing_destination_candidates,
            routing_destination_activity_label,
            routing_destination_candidate_label,
            routing_destination_class_label,
        )
        from concord.routing.review import (
            RoutingFailureAlreadyResolvedError,
            list_routing_failures,
            resolve_routing_failure_with_route,
            review_routing_failure,
            routing_failure_summary_label,
        )
        from concord.storage import load_current_record_graph
        from concord.workflows import (
            CreateActivityContextRequest,
            WorkflowActor,
            create_activity_context,
        )
        from concord.workflows.artifact_page import (
            ArtifactPagePlan,
            PrepareArtifactPagesRequest,
            prepare_artifact_pages,
        )


        def stage(name: str) -> None:
            print(f"issue109 installed wheel: {name}: PASS", flush=True)


        def require_installed(module: object, distribution: str) -> None:
            raw = getattr(module, "__file__", None)
            if not isinstance(raw, str):
                raise AssertionError(f"{distribution} package file is unavailable")
            origin = Path(raw).resolve()
            if "site-packages" not in str(origin).casefold():
                raise AssertionError(
                    f"{distribution} did not import from isolated "
                    f"site-packages: {origin}"
                )


        def fingerprint(root: Path) -> tuple[tuple[str, str], ...]:
            values = []
            for path in sorted(
                (item for item in root.rglob("*") if item.is_file()),
                key=lambda item: item.relative_to(root).as_posix(),
            ):
                values.append(
                    (
                        path.relative_to(root).as_posix(),
                        hashlib.sha256(path.read_bytes()).hexdigest(),
                    )
                )
            return tuple(values)


        def route_inventory(
            root: Path,
            locator: object,
        ) -> tuple[tuple[str, bytes], ...]:
            directory = route_registration_path(root, locator).parent
            return tuple(
                (path.name, path.read_bytes())
                for path in sorted(directory.glob("*.json"))
                if path.is_file()
            )


        def resolution_count(root: Path) -> int:
            directory = routing_review_dir(root) / "resolutions"
            if not directory.exists():
                return 0
            return sum(1 for path in directory.glob("*.json") if path.is_file())


        require_installed(pds_core, "pds-core")
        require_installed(concord, "pds-concord")
        assert metadata.version("pds-core") == "0.6.5"
        assert metadata.version("pds-concord") == "0.3.1"
        stage("isolated installed provenance")

        with tempfile.TemporaryDirectory(
            prefix="concord-issue109-installed-"
        ) as raw:
            root = ensure_workspace_root(Path(raw) / "workspace")
            fixed = datetime(2026, 10, 4, 22, 30, tzinfo=timezone.utc)
            actor = WorkflowActor(actor_id="teacher-issue109")
            write_class_metadata_for_class(
                root,
                create_class_metadata(
                    "class-1",
                    "2026-2027",
                    created_at=fixed,
                ),
            )
            create_activity_context(
                CreateActivityContextRequest(
                    class_id="class-1",
                    activity_id="activity-1",
                    title="Installed Routing Review",
                    activity_type="project",
                    scoring_orientation="evidence_only",
                    session_id="session-1",
                    actor=actor,
                ),
                workspace_root=root,
                clock=lambda: fixed,
            )
            prepared = prepare_artifact_pages(
                PrepareArtifactPagesRequest(
                    class_id="class-1",
                    activity_id="activity-1",
                    artifact_instance_id="artifact-1",
                    template_version_id="template-1",
                    artifact_category="student_work",
                    expected_snapshot_revision=1,
                    actor=actor,
                    pages=(
                        ArtifactPagePlan(
                            page_number=1,
                            artifact_page_id="page-1",
                        ),
                    ),
                    privacy_policy=PrivacyPolicy(
                        classification="teacher_restricted"
                    ),
                ),
                workspace_root=root,
                clock=lambda: fixed,
            )
            payload = prepared.pages[0].pds2_payload
            assert payload is not None
            from pds_core.pds2 import parse_pds2_payload

            locator = parse_pds2_payload(payload)
            registration = load_route_registration(root, locator)
            routes_before = route_inventory(root, locator)

            source = Path(raw) / "returned-page.png"
            source.write_bytes(b"issue109 installed retained page")
            retained = retain_source_scan(
                root,
                source,
                intake_timestamp=fixed,
            )

            def failure(
                failure_id: str,
                *,
                bound: bool,
            ) -> RoutingFailureMetadata:
                value = RoutingFailureMetadata(
                    schema_version=ROUTING_FAILURE_SCHEMA_VERSION,
                    failure_id=failure_id,
                    scope="page",
                    stage="route_resolution",
                    created_at=fixed.isoformat(),
                    failure_category="payload_missing",
                    failure_message="Synthetic installed Routing Review failure.",
                    source_filename=retained.source_filename,
                    source_scan_id=retained.source_scan_id,
                    source_sha256=retained.source_sha256,
                    retained_source_path=retained.retained_source_relative_path,
                    review_copy_path=None,
                    source_page_number=1,
                    detected_payload=None,
                    route_locator=locator if bound else None,
                    target=registration.target if bound else None,
                    module_details={},
                )
                write_routing_failure_metadata(root, value)
                return value

            unbound = failure("failure-unbound-1", bound=False)
            before_browse = fingerprint(root)
            summaries = list_routing_failures(workspace_root=root)
            summary = next(
                item for item in summaries if item.failure_id == unbound.failure_id
            )
            row = routing_failure_summary_label(summary)
            assert "returned-page.png" in row
            assert "page 1" in row
            assert unbound.failure_id not in row

            review = review_routing_failure(
                unbound.failure_id,
                workspace_root=root,
            )
            assert review.bound_work is None
            assert review.route_action_available
            classes = list_routing_destination_classes(
                review,
                workspace_root=root,
            )
            assert len(classes) == 1
            assert classes[0].class_id == "class-1"
            assert "2026-2027" in routing_destination_class_label(classes[0])
            activities = list_routing_destination_activities(
                review,
                "class-1",
                workspace_root=root,
            )
            assert len(activities) == 1
            assert activities[0].activity_id == "activity-1"
            assert "Installed Routing Review" in (
                routing_destination_activity_label(activities[0])
            )
            projection = project_routing_destination_candidates(
                review,
                locator.work,
                workspace_root=root,
            )
            assert len(projection.candidates) == 1
            candidate = projection.candidates[0]
            assert candidate.locator == locator
            candidate_label = routing_destination_candidate_label(candidate)
            assert "student work" in candidate_label
            assert "page 1" in candidate_label
            assert "Physical: Concord activity-1 page 1" in candidate_label
            assert locator.route_id not in candidate_label
            assert candidate.artifact_instance_id not in candidate_label
            assert fingerprint(root) == before_browse
            stage("unbound Class Activity page browse is read-only")

            first_resolution = resolve_routing_failure_with_route(
                unbound.failure_id,
                candidate.locator,
                message="Teacher selected the exact installed destination.",
                workspace_root=root,
                reviewer=actor,
            )
            assert first_resolution.resolution_status == "resolved"
            assert first_resolution.resolution_action == "route_selected"
            after_first = load_current_record_graph(root, locator.work)
            assert len(after_first.graph.scan_references) == 1
            assert route_inventory(root, locator) == routes_before
            stage("final exact-route resolution through installed Core dispatch")

            bound = failure("failure-bound-1", bound=True)
            bound_review = review_routing_failure(
                bound.failure_id,
                workspace_root=root,
            )
            assert bound_review.bound_work == locator.work
            assert list_routing_destination_classes(
                bound_review,
                workspace_root=root,
            ) == ()
            bound_projection = project_routing_destination_candidates(
                bound_review,
                locator.work,
                workspace_root=root,
            )
            assert len(bound_projection.candidates) == 1
            replay_candidate = bound_projection.candidates[0]
            assert replay_candidate.replayed_occurrence
            replay_label = routing_destination_candidate_label(replay_candidate)
            assert "already filed from this scan page" in replay_label
            revision_before_replay = after_first.snapshot_revision
            replay_resolution = resolve_routing_failure_with_route(
                bound.failure_id,
                replay_candidate.locator,
                message="Teacher confirmed the existing bound Activity page.",
                workspace_root=root,
                reviewer=actor,
            )
            assert replay_resolution.resolution_action == "route_corrected"
            after_replay = load_current_record_graph(root, locator.work)
            assert after_replay.snapshot_revision == revision_before_replay
            assert len(after_replay.graph.scan_references) == 1
            assert route_inventory(root, locator) == routes_before
            stage("bound Activity skips browse and exact replay is idempotent")

            stale = failure("failure-stale-1", bound=True)
            terminal = create_scan_resolution_metadata(
                stale,
                resolution_id="resolution-stale-terminal",
                resolution_status="resolved",
                resolution_action="route_corrected",
                resolved_at=fixed.isoformat(),
                resolution_message="Another reviewer already resolved this failure.",
                route_locator=locator,
                target=registration.target,
                module_details={"review_module": "concord"},
            )
            write_scan_resolution_metadata(root, terminal)
            before_stale = load_current_record_graph(root, locator.work)
            resolutions_before = resolution_count(root)
            try:
                resolve_routing_failure_with_route(
                    stale.failure_id,
                    locator,
                    message="Stale installed review must not dispatch.",
                    workspace_root=root,
                    reviewer=actor,
                )
            except RoutingFailureAlreadyResolvedError:
                pass
            else:
                raise AssertionError("stale resolved failure was dispatched")
            after_stale = load_current_record_graph(root, locator.work)
            assert after_stale.snapshot_revision == before_stale.snapshot_revision
            assert after_stale.snapshot_sha256 == before_stale.snapshot_sha256
            assert resolution_count(root) == resolutions_before
            assert route_inventory(root, locator) == routes_before
            stage("stale terminal state fails closed before redispatch")

            from concord import menu_scan

            assert callable(menu_scan.launch_scan_routing_menu)
            stage("teacher Routing Review menu remains installed and reachable")

        print(
            "Issue #109 isolated installed-wheel acceptance: PASS",
            flush=True,
        )
        """
    )


def smoke(concord_wheel: Path, core_wheel: Path) -> None:
    """Exercise Issue #109 using only isolated installed wheel imports."""
    if not concord_wheel.is_file():
        raise FileNotFoundError(concord_wheel)
    if not core_wheel.is_file():
        raise FileNotFoundError(core_wheel)
    core_sha = _sha256(core_wheel)
    if core_sha != EXPECTED_CORE_SHA256:
        raise RuntimeError(
            "Issue #109 requires the exact released Core 0.6.5 "
            "qualification wheel."
        )

    print(
        f"Issue #109 candidate wheel SHA-256: {_sha256(concord_wheel)}",
        flush=True,
    )
    print(f"Issue #109 Core wheel SHA-256: {core_sha}", flush=True)

    with tempfile.TemporaryDirectory(prefix="concord-issue109-wheel-") as raw:
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

        smoke_path = work / "issue109_installed_acceptance.py"
        smoke_path.write_text(_smoke_code(), encoding="utf-8")
        _run([str(python), "-I", str(smoke_path)], work)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("concord_wheel", type=Path)
    parser.add_argument("core_wheel", type=Path)
    args = parser.parse_args()
    smoke(args.concord_wheel, args.core_wheel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

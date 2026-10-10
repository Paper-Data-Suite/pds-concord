"""Build and qualify the Concord v0.3.1 Issue #129 wheel under Core 0.6.5."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import textwrap
import venv
import zipfile
from email.parser import BytesParser
from email.policy import default
from pathlib import Path

EXPECTED_CONCORD_VERSION = "0.3.1"
EXPECTED_CONCORD_WHEEL = "pds_concord-0.3.1-py3-none-any.whl"
EXPECTED_CORE_VERSION = "0.6.5"
EXPECTED_CORE_WHEEL = "pds_core-0.6.5-py3-none-any.whl"
EXPECTED_CORE_SHA256 = (
    "9ace75f17b23b7f0ed6a709d531af5120db43d0325b4148d26f2d6ba1d4b3c18"
)


class Issue129InstalledAcceptanceError(RuntimeError):
    """Raised when Issue #129 installed-wheel qualification cannot complete."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(command: list[str], *, cwd: Path) -> None:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        check=True,
    )


def _environment_python(environment: Path) -> Path:
    if os.name == "nt":
        return environment / "Scripts" / "python.exe"
    return environment / "bin" / "python"


def _wheel_metadata(wheel: Path) -> tuple[str, str]:
    try:
        with zipfile.ZipFile(wheel) as archive:
            names = [
                name
                for name in archive.namelist()
                if name.count("/") == 1 and name.endswith(".dist-info/METADATA")
            ]
            if len(names) != 1:
                raise Issue129InstalledAcceptanceError(
                    "candidate wheel must contain exactly one top-level METADATA"
                )
            message = BytesParser(policy=default).parsebytes(
                archive.read(names[0])
            )
    except zipfile.BadZipFile as error:
        raise Issue129InstalledAcceptanceError(
            "candidate wheel is not a readable ZIP archive"
        ) from error

    name = message.get("Name")
    version = message.get("Version")
    if not isinstance(name, str) or not isinstance(version, str):
        raise Issue129InstalledAcceptanceError(
            "candidate wheel metadata name/version is missing"
        )
    return name, version


def _verify_core_wheel(core_wheel: Path) -> str:
    if core_wheel.name != EXPECTED_CORE_WHEEL:
        raise Issue129InstalledAcceptanceError(
            f"Core wheel must be named {EXPECTED_CORE_WHEEL}"
        )
    if not core_wheel.is_file():
        raise Issue129InstalledAcceptanceError(
            f"Core wheel is unavailable: {core_wheel}"
        )
    digest = _sha256(core_wheel)
    if digest != EXPECTED_CORE_SHA256:
        raise Issue129InstalledAcceptanceError(
            "Core 0.6.5 wheel SHA-256 does not match the qualified release"
        )
    name, version = _wheel_metadata(core_wheel)
    if name != "pds-core" or version != EXPECTED_CORE_VERSION:
        raise Issue129InstalledAcceptanceError(
            "Core wheel metadata is not exactly pds-core 0.6.5"
        )
    return digest


def _remove_generated_build_roots(repository: Path) -> None:
    for relative in (
        Path("build"),
        Path("pds_concord.egg-info"),
        Path("concord.egg-info"),
    ):
        target = repository / relative
        if not target.exists():
            continue
        if target.is_symlink():
            raise Issue129InstalledAcceptanceError(
                f"refusing to clean linked generated path: {target}"
            )
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()


def _smoke_code(repository: Path) -> str:
    return textwrap.dedent(
        f"""
        from __future__ import annotations

        import sys
        from datetime import datetime, timezone
        from importlib import metadata
        from pathlib import Path
        import tempfile

        import concord
        import pds_core
        from pds_core.class_metadata import (
            create_class_metadata,
            write_class_metadata_for_class,
        )
        from pds_core.classes import write_class_roster
        from pds_core.publication_compatibility import (
            discover_publication_producer_profiles,
            lookup_publication_reader_support,
        )
        from pds_core.rosters import create_roster
        from pds_core.routing_models import ModuleWorkRef
        from pds_core.standards import (
            StandardDefinition,
            StandardsLibrary,
            StandardsProfile,
            write_workspace_standards_library,
        )
        from pds_core.workspace import ensure_workspace_root

        from concord.academic_result_manifest_generation import (
            GenerateAcademicResultManifestRequest,
        )
        from concord.academic_result_publication import (
            publish_concord_academic_results,
        )
        from concord.academic_result_reader import read_academic_result_manifest
        from concord.academic_work_registration import (
            register_concord_academic_work,
        )
        from concord.models import (
            PrivacyPolicy,
            ScoreTargetReference,
            ScoringScaleLevel,
        )
        from concord.pds_contract import (
            ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
            CONCORD_ACADEMIC_RESULT_READER_CONTRACT_VERSION,
        )
        from concord.pds_publication import get_publication_producer_profile
        from concord.workflows import (
            AddScoreRequest,
            CreateActivityContextRequest,
            CreateCriterionSetRequest,
            CreateScoringScaleRequest,
            CriterionSpec,
            SelectActivityCriterionSetsRequest,
            WorkflowActor,
            add_score,
            create_activity_context,
            create_criterion_set,
            create_scoring_scale,
            select_activity_criterion_sets,
        )
        from concord.workflows.activity_read import load_activity_read_context

        EXPECTED_CONCORD_VERSION = {EXPECTED_CONCORD_VERSION!r}
        EXPECTED_CORE_VERSION = {EXPECTED_CORE_VERSION!r}
        REPOSITORY = Path({str(repository)!r}).resolve()

        PROFILE_ID = "njsls-ela:profile.2023:11-12"
        STANDARD_ID = "njsls-ela:2023:rl-ts-11-12-4"
        STANDARD_CODE = "RL.TS.11-12.4"
        STANDARD_SHORT_NAME = "Analyze Text Structure"


        def stage(name: str) -> None:
            print(f"Issue #129 installed acceptance: {{name}}: PASS", flush=True)


        def require_installed(module: object, distribution: str) -> None:
            raw = getattr(module, "__file__", None)
            if not isinstance(raw, str) or not raw:
                raise AssertionError(f"{{distribution}} package file is unavailable")
            origin = Path(raw).resolve()
            parts = {{part.casefold() for part in origin.parts}}
            assert "site-packages" in parts, (
                f"{{distribution}} did not import from site-packages: {{origin}}"
            )
            assert not origin.is_relative_to(REPOSITORY), (
                f"{{distribution}} imported from source checkout: {{origin}}"
            )


        def actor() -> WorkflowActor:
            return WorkflowActor(
                actor_id="teacher-issue129",
                display_label="Synthetic Qualification Teacher",
                role_label="teacher",
            )


        def clock(hour: int) -> datetime:
            return datetime(2026, 10, 9, hour, 0, tzinfo=timezone.utc)


        def standards() -> StandardsLibrary:
            return StandardsLibrary(
                standards=(
                    StandardDefinition(
                        standard_id=STANDARD_ID,
                        code=STANDARD_CODE,
                        source="NJSLS ELA",
                        short_name=STANDARD_SHORT_NAME,
                        description=(
                            "Analyze structural choices and their effects."
                        ),
                        subject="English Language Arts",
                        grade_band="11-12",
                        available_modules=("concord",),
                    ),
                ),
                profiles=(
                    StandardsProfile(
                        profile_id=PROFILE_ID,
                        standards=(STANDARD_ID,),
                        subject="English Language Arts",
                        source="NJSLS ELA",
                        title="NJSLS ELA Grades 11–12",
                    ),
                ),
            )


        assert metadata.version("pds-concord") == EXPECTED_CONCORD_VERSION
        assert concord.__version__ == EXPECTED_CONCORD_VERSION
        assert metadata.version("pds-core") == EXPECTED_CORE_VERSION
        assert pds_core.__version__ == EXPECTED_CORE_VERSION
        require_installed(concord, "pds-concord")
        require_installed(pds_core, "pds-core")

        for raw in sys.path:
            if not raw:
                continue
            try:
                candidate = Path(raw).resolve()
            except OSError:
                continue
            assert candidate != REPOSITORY
            assert not candidate.is_relative_to(REPOSITORY)

        forbidden = {{"scoreform", "quillan", "portia", "meridian", "vitrine"}}
        loaded = {{name.split(".", 1)[0].casefold() for name in sys.modules}}
        assert forbidden.isdisjoint(loaded)
        stage("isolated wheel provenance")

        profiles = tuple(
            item
            for item in discover_publication_producer_profiles()
            if item.module_id == "concord"
        )
        assert profiles == (get_publication_producer_profile(),)
        support = lookup_publication_reader_support(
            profiles[0],
            "academic_result_set",
            ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
        )
        assert support is not None
        assert support.distribution_name == "pds-concord"
        assert support.reader_contract_version == (
            CONCORD_ACADEMIC_RESULT_READER_CONTRACT_VERSION
        )
        assert support.reader_contract_version == (
            "concord_academic_result_reader_v1"
        )
        stage("installed producer reader metadata")

        with tempfile.TemporaryDirectory(
            prefix="concord-issue129-installed-"
        ) as raw:
            root = ensure_workspace_root(Path(raw) / "workspace")
            write_class_metadata_for_class(
                root,
                create_class_metadata(
                    "class-1",
                    "2026-2027",
                    created_at=clock(8),
                ),
            )
            write_class_roster(
                root,
                create_roster(
                    "class-1",
                    (
                        {{
                            "student_id": "student-1",
                            "last_name": "One",
                            "first_name": "Alex",
                            "period": "1",
                        }},
                    ),
                ),
            )

            library = standards()
            write_workspace_standards_library(root, library)

            activity = create_activity_context(
                CreateActivityContextRequest(
                    class_id="class-1",
                    activity_id="activity-1",
                    title="Installed Standards Qualification",
                    activity_type="project",
                    scoring_orientation="standards_based",
                    session_id="session-1",
                    actor=actor(),
                    activity_status="active",
                    session_status="active",
                    standards_profile_id=PROFILE_ID,
                    focus_standard_ids=(STANDARD_ID,),
                    privacy_policy=PrivacyPolicy(
                        classification="teacher_restricted"
                    ),
                ),
                workspace_root=root,
                standards_library=library,
                clock=lambda: clock(9),
            )

            scale = create_scoring_scale(
                CreateScoringScaleRequest(
                    class_id="class-1",
                    activity_id="activity-1",
                    scoring_scale_id="scale-1",
                    lineage_id="scale-lineage-1",
                    name="Standards Scale",
                    revision=1,
                    scale_type="ordinal",
                    levels=(
                        ScoringScaleLevel(
                            value="developing",
                            label="Developing",
                            meaning="Evidence is developing.",
                            position=1,
                        ),
                        ScoringScaleLevel(
                            value="meeting",
                            label="Meeting",
                            meaning="Evidence meets the criterion.",
                            position=2,
                        ),
                    ),
                    status="active",
                    expected_snapshot_revision=(
                        activity.commit.snapshot_revision
                    ),
                    actor=actor(),
                ),
                workspace_root=root,
                standards_library=library,
                clock=lambda: clock(10),
            )

            criterion_set = create_criterion_set(
                CreateCriterionSetRequest(
                    class_id="class-1",
                    activity_id="activity-1",
                    criterion_set_id="set-1",
                    lineage_id="set-lineage-1",
                    name="Text Structure",
                    purpose="Installed reader compatibility qualification.",
                    revision=1,
                    scope="activity_specific",
                    criterion_set_kind="standard_backed",
                    criteria=(
                        CriterionSpec(
                            criterion_id="criterion-1",
                            key="text_structure",
                            label="Text Structure Analysis",
                            definition=(
                                "Analyzes structural choices and effects."
                            ),
                            criterion_kind="standard_backed",
                            supported_target_kinds=("core_student",),
                            standard_id=STANDARD_ID,
                            default_scoring_scale_id="scale-1",
                        ),
                    ),
                    status="active",
                    expected_snapshot_revision=(
                        scale.commit.snapshot_revision
                    ),
                    actor=actor(),
                    standards_profile_id=PROFILE_ID,
                ),
                workspace_root=root,
                standards_library=library,
                clock=lambda: clock(11),
            )

            selected = select_activity_criterion_sets(
                SelectActivityCriterionSetsRequest(
                    class_id="class-1",
                    activity_id="activity-1",
                    criterion_set_ids=("set-1",),
                    expected_snapshot_revision=(
                        criterion_set.commit.snapshot_revision
                    ),
                    actor=actor(),
                ),
                workspace_root=root,
                standards_library=library,
                clock=lambda: clock(12),
            )

            scored = add_score(
                AddScoreRequest(
                    class_id="class-1",
                    activity_id="activity-1",
                    score_record_id="score-1",
                    target_reference=ScoreTargetReference(
                        target_kind="core_student",
                        target_id="student-1",
                        owning_system="core",
                    ),
                    criterion_id="criterion-1",
                    scoring_scale_id="scale-1",
                    disposition="scored",
                    value="meeting",
                    basis="professional_judgment",
                    rationale=(
                        "Synthetic installed professional judgment."
                    ),
                    privacy_policy=PrivacyPolicy(
                        classification="teacher_restricted"
                    ),
                    expected_snapshot_revision=(
                        selected.commit.snapshot_revision
                    ),
                    actor=actor(),
                    session_id="session-1",
                ),
                workspace_root=root,
                standards_library=library,
                clock=lambda: clock(13),
            )

            context = load_activity_read_context(
                root,
                ModuleWorkRef("concord", "class-1", "activity-1"),
            )
            assert context.activity.standards_profile_id == PROFILE_ID
            assert context.activity.focus_standard_ids == (STANDARD_ID,)
            assert context.graph.criterion_sets[0].standards_profile_id == (
                PROFILE_ID
            )
            assert context.graph.criteria[0].standard_id == STANDARD_ID
            assert context.graph.score_records[0].standard_id == STANDARD_ID
            stage("persisted punctuation-bearing Standards identity")

            register_concord_academic_work(
                root,
                "class-1",
                "activity-1",
                academic_intent="summative",
                lifecycle="active",
            )

            publication = publish_concord_academic_results(
                GenerateAcademicResultManifestRequest(
                    class_id="class-1",
                    activity_id="activity-1",
                    expected_snapshot_revision=(
                        scored.commit.snapshot_revision
                    ),
                    actor=actor(),
                    revision_reason="initial",
                ),
                workspace_root=root,
                standards_library=library,
                clock=lambda: clock(14),
            )
            assert publication.compatibility.compatible
            assert publication.compatibility.codes == ()
            assert publication.publication.manifest_contract_version == (
                "concord_academic_result_manifest_v1"
            )
            assert set(publication.publication.capabilities) == {{
                "criterion_scores",
                "standards_ratings",
            }}

            content = publication.manifest_generation.content
            assert STANDARD_ID.encode("utf-8") in content
            assert PROFILE_ID.encode("utf-8") in content
            assert STANDARD_CODE.encode("utf-8") not in content

            manifest = read_academic_result_manifest(content)
            assert manifest.activity_context.standards_profile_id == PROFILE_ID
            assert manifest.activity_context.focus_standard_ids == (STANDARD_ID,)
            assert manifest.criterion_sets[0].standards_profile_id == PROFILE_ID
            assert manifest.criteria[0].standard_id == STANDARD_ID
            assert manifest.scores[0].standard_id == STANDARD_ID
            assert (
                manifest.standards_result_projection[0].standard_id
                == STANDARD_ID
            )

            exact_support = lookup_publication_reader_support(
                get_publication_producer_profile(),
                publication.publication.publication_kind,
                publication.publication.manifest_contract_version,
            )
            assert exact_support == support
            stage("manifest generation Core publication and public reader")

        loaded = {{name.split(".", 1)[0].casefold() for name in sys.modules}}
        assert forbidden.isdisjoint(loaded)
        print(
            "Issue #129 isolated installed Core 0.6.5 acceptance: PASS",
            flush=True,
        )
        """
    )


def run_acceptance(
    *,
    repository: Path,
    work: Path,
    core_wheel: Path,
) -> dict[str, str]:
    repository = repository.resolve(strict=True)
    core_wheel = core_wheel.resolve(strict=True)
    work = work.resolve()

    if work.exists():
        if not work.is_dir() or any(work.iterdir()):
            raise Issue129InstalledAcceptanceError(
                "--work must be absent or an empty directory"
            )
    else:
        work.mkdir(parents=True)

    generated_roots = (
        repository / "build",
        repository / "pds_concord.egg-info",
        repository / "concord.egg-info",
    )
    if any(path.exists() for path in generated_roots):
        raise Issue129InstalledAcceptanceError(
            "refusing to overwrite pre-existing generated build roots"
        )

    core_digest = _verify_core_wheel(core_wheel)
    artifacts = work / "artifacts"
    environment = work / "venv"
    outside = work / "outside-source"
    artifacts.mkdir()
    outside.mkdir()

    try:
        _run(
            [
                sys.executable,
                "-m",
                "build",
                "--wheel",
                "--outdir",
                str(artifacts),
            ],
            cwd=repository,
        )
        wheels = tuple(artifacts.glob("*.whl"))
        if len(wheels) != 1:
            raise Issue129InstalledAcceptanceError(
                "build must produce exactly one Concord wheel"
            )
        wheel = wheels[0]
        if wheel.name != EXPECTED_CONCORD_WHEEL:
            raise Issue129InstalledAcceptanceError(
                f"candidate wheel must be named {EXPECTED_CONCORD_WHEEL}"
            )
        name, version = _wheel_metadata(wheel)
        if name != "pds-concord" or version != EXPECTED_CONCORD_VERSION:
            raise Issue129InstalledAcceptanceError(
                "candidate wheel metadata is not exactly pds-concord 0.3.1"
            )
        concord_digest = _sha256(wheel)

        print(
            f"Issue #129 candidate wheel SHA-256: {concord_digest}",
            flush=True,
        )
        print(
            f"Issue #129 Core wheel SHA-256: {core_digest}",
            flush=True,
        )

        venv.EnvBuilder(with_pip=True).create(environment)
        python = _environment_python(environment)
        if not python.is_file():
            raise Issue129InstalledAcceptanceError(
                "isolated environment Python was not created"
            )

        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                str(core_wheel),
            ],
            cwd=outside,
        )
        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                str(wheel),
            ],
            cwd=outside,
        )
        _run([str(python), "-m", "pip", "check"], cwd=outside)

        smoke_path = work / "issue129_installed_acceptance.py"
        smoke_path.write_text(
            _smoke_code(repository),
            encoding="utf-8",
        )
        _run(
            [str(python), "-I", str(smoke_path)],
            cwd=outside,
        )

        return {
            "concord_version": EXPECTED_CONCORD_VERSION,
            "concord_wheel": str(wheel),
            "concord_sha256": concord_digest,
            "core_version": EXPECTED_CORE_VERSION,
            "core_wheel": str(core_wheel),
            "core_sha256": core_digest,
            "installed_acceptance": "passed",
        }
    finally:
        _remove_generated_build_roots(repository)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--core-wheel", required=True, type=Path)
    args = parser.parse_args()

    try:
        result = run_acceptance(
            repository=args.repository,
            work=args.work,
            core_wheel=args.core_wheel,
        )
    except (
        Issue129InstalledAcceptanceError,
        OSError,
        subprocess.CalledProcessError,
    ) as error:
        parser.exit(
            1,
            f"Issue #129 installed acceptance failed: {error}\n",
        )

    import json

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

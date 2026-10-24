"""Disposable, fabricated two-class Core/Concord fixture for #140 Slice 2.

No teacher workspace, OneDrive folder, network, publication, or real student data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.rosters import create_roster
from pds_core.standards import StandardDefinition, StandardsLibrary, StandardsProfile
from pds_core.workspace import ensure_workspace_root

from concord.workflows import (
    CreateActivityContextRequest,
    WorkflowActor,
    create_activity_context,
    show_activity,
)

STANDARD_ID = "SL.PE.11-12.1"
PROFILE_ID = "synthetic-profile-ela-11-12"
SOURCE_CLASS = "issue140-synthetic-period2"
TARGET_CLASS = "issue140-synthetic-period4"
ACTIVITY_ID = "issue140-synthetic-discussion"
ACTOR = WorkflowActor(actor_id="issue140-synthetic-teacher")
SOURCE_GROUP_COUNTS = (5, 5, 5, 5, 4, 5)
TARGET_GROUP_COUNTS = (6, 5, 5, 3, 6, 5)


@dataclass(frozen=True)
class SyntheticClass:
    class_id: str
    students: tuple[str, ...]
    cluster_members: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class WitnessWorkspace:
    root: Path
    standards: StandardsLibrary
    source: SyntheticClass
    target: SyntheticClass


def _clock() -> datetime:
    return datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)


def _class(class_id: str, counts: tuple[int, ...]) -> SyntheticClass:
    assert len(counts) == 6
    students = tuple(f"{class_id}-student-{i:02d}" for i in range(1, sum(counts) + 1))
    groups = []
    pos = 0
    for count in counts:
        groups.append(students[pos : pos + count])
        pos += count
    assert sum(map(len, groups)) == len(students)
    return SyntheticClass(class_id, students, tuple(groups))


def build_workspace(tmp_path: Path, *, orientation: str = "mixed") -> WitnessWorkspace:
    """Make two disjoint Core classes and one genuine source Activity."""
    root = ensure_workspace_root(tmp_path / "issue140_disposable_workspace")
    source = _class(SOURCE_CLASS, SOURCE_GROUP_COUNTS)
    target = _class(TARGET_CLASS, TARGET_GROUP_COUNTS)
    assert not (set(source.students) & set(target.students))
    for section in (source, target):
        write_class_metadata_for_class(
            root,
            create_class_metadata(section.class_id, "2026-2027", created_at=_clock()),
        )
        write_class_roster(
            root,
            create_roster(
                section.class_id,
                tuple(
                    {
                        "student_id": sid,
                        "first_name": "Fabricated",
                        "last_name": f"Learner{i:02d}",
                        "period": "2" if section.class_id == SOURCE_CLASS else "4",
                    }
                    for i, sid in enumerate(section.students, start=1)
                ),
            ),
        )
    library = StandardsLibrary(
        standards=(
            StandardDefinition(
                standard_id=STANDARD_ID,
                code=STANDARD_ID,
                source="synthetic",
                short_name="Synthetic Collaborative Discussion",
                description="Invented standard metadata for regression testing.",
                available_modules=("concord",),
            ),
        ),
        profiles=(
            StandardsProfile(
                profile_id=PROFILE_ID,
                standards=(STANDARD_ID,),
                title="Synthetic English 12 Standards Profile",
            ),
        ),
    )
    use_standards = orientation in {"mixed", "standards_based"}
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id=SOURCE_CLASS,
            activity_id=ACTIVITY_ID,
            title="Synthetic Jibara Discussion",
            activity_type="socratic_seminar",
            scoring_orientation=orientation,
            standards_profile_id=PROFILE_ID if use_standards else None,
            focus_standard_ids=(STANDARD_ID,) if use_standards else (),
            session_id="issue140-synthetic-session",
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=library if use_standards else None,
        clock=_clock,
    )
    assert created.commit.snapshot_revision >= 1
    assert (
        show_activity(
            SOURCE_CLASS, ACTIVITY_ID, workspace_root=root
        ).summary.scoring_orientation
        == orientation
    )
    return WitnessWorkspace(root, library, source, target)

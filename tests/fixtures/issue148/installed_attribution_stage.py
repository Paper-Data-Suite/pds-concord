"""Isolated installed-wheel subprocess stages for Concord issue #148.

This file is copied to a disposable directory by the smoke runner. Its imports
must resolve only against installed distributions; no source tree is involved.
"""

from __future__ import annotations

import os
import sys
from importlib import metadata
from pathlib import Path

import pds_core
from pds_core.workspace import get_workspace_config_path

import concord
from concord.menu_context import new_menu_session
from concord.teacher_attribution import ConcordTeacherAttributionStore

ACTOR_ID = "teacher-issue148-synthetic"
ACTOR_NAME = "Dr. Ñ. Example"


def _installed_only() -> None:
    """Refuse source-checkout, user-site, or sibling distribution imports."""
    environment = Path(sys.prefix).resolve()
    assert metadata.version("pds-core") == "0.6.6"
    assert metadata.version("pds-concord") == "0.3.4"
    for package in (pds_core, concord):
        location = Path(package.__file__).resolve()
        assert location.is_relative_to(environment), location
        assert "site-packages" in location.as_posix().lower(), location
    for distribution in (
        "pds-meridian",
        "meridian",
        "paper-data-suite",
        "scoreform",
        "quillan",
    ):
        try:
            metadata.version(distribution)
        except metadata.PackageNotFoundError:
            continue
        raise AssertionError(f"Unintended sibling installed: {distribution}")
    config = get_workspace_config_path()
    controlled = Path(os.environ["PDS_148_TEST_CONFIG_HOME"]).resolve()
    assert config.is_relative_to(controlled), (config, controlled)
    workspace = Path(os.environ["PDS_WORKSPACE_ROOT"]).resolve()
    assert workspace.is_relative_to(controlled.parent), workspace
    assert config != workspace


def _profile() -> ConcordTeacherAttributionStore:
    session = new_menu_session()
    provider = session.attribution_provider
    assert provider is not None
    store = provider.store
    assert store.profile_path.is_relative_to(
        Path(os.environ["PDS_148_TEST_CONFIG_HOME"]).resolve()
    )
    return store


def _never_prompt(_message: str = "") -> str:
    raise AssertionError("A saved actor was requested again after restart")


def _setup() -> None:
    """Use the real installed Settings save function with reviewed synthetic input."""
    import concord.menu_teacher_settings as settings

    session = new_menu_session()
    provider = session.attribution_provider
    assert provider is not None
    store = provider.store
    assert store.load() is None
    assert not store.directory.exists()

    reviews: list[str] = []

    def approve(title: str, expected: str, lines: tuple[str, ...]) -> bool:
        assert title == "Save Concord Attribution"
        assert expected == "SAVE PROFILE"
        joined = " ".join(lines)
        assert ACTOR_ID in joined and ACTOR_NAME in joined
        assert "Concord" in joined
        reviews.append(expected)
        return True

    settings._ask_name = lambda **_kw: ACTOR_NAME
    settings._choose_actor_id = lambda _name: ACTOR_ID
    settings.confirm_write = approve
    settings.show_result = lambda *_args: None
    settings._setup(session, provider)
    assert reviews == ["SAVE PROFILE"]
    saved = store.load()
    assert saved is not None
    assert saved.profile.actor_id == ACTOR_ID
    assert saved.profile.display_name == ACTOR_NAME
    assert saved.profile.revision == 1
    assert not get_workspace_config_path().exists()
    assert not Path(os.environ["PDS_WORKSPACE_ROOT"]).exists()
    print("#148 INSTALLED SETUP: reviewed local profile; zero academic writes")


def _actor():
    """Use the production session factory in each entirely new interpreter."""
    import builtins

    builtins.input = _never_prompt
    session = new_menu_session()
    actor = session.require_actor()
    assert actor.actor_id == ACTOR_ID
    assert actor.display_label == ACTOR_NAME
    assert actor.actor_kind == "authorized_adult"
    assert actor.owning_system == "concord"
    assert session.require_actor() == actor
    return actor


def _verify_provenance(root: Path, activity_id: str, group_id: str | None) -> None:
    """Read immutable records and inspect exact persisted actor snapshots."""
    from pds_core.routing_models import ModuleWorkRef

    from concord.storage import load_current_record

    work = ModuleWorkRef(
        module_id="concord", class_id="class-synthetic", work_id=activity_id
    )
    activity, _revision = load_current_record(root, work, "activity", activity_id)
    created_by = activity.created_provenance.actor
    assert created_by.actor_id == ACTOR_ID
    assert created_by.display_label_snapshot == ACTOR_NAME
    assert created_by.owning_system == "concord"
    if group_id is not None:
        group, _revision = load_current_record(root, work, "group", group_id)
        created_by = group.created_provenance.actor
        assert created_by.actor_id == ACTOR_ID
        assert created_by.display_label_snapshot == ACTOR_NAME


def _author() -> None:
    """Fresh-process authoring of two distinct canonical record kinds."""
    from datetime import UTC, datetime

    from pds_core.class_metadata import (
        create_class_metadata,
        write_class_metadata_for_class,
    )
    from pds_core.classes import write_class_roster
    from pds_core.rosters import create_roster
    from pds_core.workspace import ensure_workspace_root

    from concord.workflows import (
        CreateActivityContextRequest,
        CreateGroupRequest,
        create_activity_context,
        create_group,
    )

    actor = _actor()
    root = ensure_workspace_root(Path(os.environ["PDS_WORKSPACE_ROOT"]))
    write_class_metadata_for_class(
        root,
        create_class_metadata(
            "class-synthetic",
            "2026-2027",
            created_at=datetime(2026, 11, 14, tzinfo=UTC),
        ),
    )
    write_class_roster(
        root,
        create_roster(
            "class-synthetic",
            (
                {
                    "student_id": "student-synthetic",
                    "last_name": "One",
                    "first_name": "Synthetic",
                    "period": "1",
                },
            ),
        ),
    )
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-synthetic",
            activity_id="activity-148-first",
            title="Isolated Attribution Activity",
            activity_type="project",
            scoring_orientation="local_criteria_only",
            session_id="session-148-first",
            actor=actor,
            activity_status="active",
            session_status="active",
        ),
        workspace_root=root,
    )
    created_group = create_group(
        CreateGroupRequest(
            class_id="class-synthetic",
            activity_id="activity-148-first",
            group_id="group-148-first",
            label="Synthetic Group",
            status="active",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=actor,
        ),
        workspace_root=root,
    )
    assert created_group.commit.snapshot_revision > created.commit.snapshot_revision
    _verify_provenance(root, "activity-148-first", "group-148-first")
    print("#148 INSTALLED AUTHOR: Activity and Group actor snapshots verified")


def _relaunch() -> None:
    """A third independent process must silently reuse actor to author again."""
    from concord.workflows import CreateActivityContextRequest, create_activity_context

    actor = _actor()
    root = Path(os.environ["PDS_WORKSPACE_ROOT"])
    _verify_provenance(root, "activity-148-first", "group-148-first")
    result = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-synthetic",
            activity_id="activity-148-relaunch",
            title="After Restart",
            activity_type="project",
            scoring_orientation="local_criteria_only",
            session_id="session-148-relaunch",
            actor=actor,
            activity_status="active",
            session_status="active",
        ),
        workspace_root=root,
    )
    assert result.commit.snapshot_revision >= 1
    _verify_provenance(root, "activity-148-relaunch", None)
    _verify_provenance(root, "activity-148-first", "group-148-first")
    saved = _profile().load()
    assert saved is not None and saved.profile.revision == 1
    assert not get_workspace_config_path().exists()
    print("#148 INSTALLED RELAUNCH: third process silently authored; history intact")


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"setup", "author", "relaunch"}:
        raise SystemExit("usage: isolated_stage.py setup|author|relaunch")
    _installed_only()
    {"setup": _setup, "author": _author, "relaunch": _relaunch}[sys.argv[1]]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

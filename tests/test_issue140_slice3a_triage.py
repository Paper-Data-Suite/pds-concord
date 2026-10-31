"""#140 Slice 3A: bounded, synthetic context and safe-source triage tests.

Do not treat source-level omitted arguments as verified behavioral failures.
"""

from __future__ import annotations

import csv
import hashlib
import io
from pathlib import Path
from typing import Any

import pytest
from issue140_slice2_fixtures import (
    ACTIVITY_ID,
    ACTOR,
    SOURCE_CLASS,
    build_workspace,
)
from pds_core.routing_models import ModuleWorkRef
from test_issue140_slice2_failing_before import _create_native_mixed_criterion_set

import concord.menu_score_teacher_labels as teacher_labels
import concord.workflows.artifact_page as artifact_pages
from concord.models import PrivacyPolicy
from concord.storage import list_work_snapshots
from concord.workflows import list_criterion_sets, list_scoring_scales, show_activity
from concord.workflows.artifact_page import (
    ArtifactPagePlan,
    PrepareArtifactPagesRequest,
)

ROOT = Path(__file__).resolve().parents[1]


def _work() -> ModuleWorkRef:
    return ModuleWorkRef("concord", SOURCE_CLASS, ACTIVITY_ID)


def test_source_boundary_inventory_preserves_named_p02_sites() -> None:
    import importlib.util
    import sys

    script = ROOT / "scripts/issue140_slice3a_triage.py"
    spec = importlib.util.spec_from_file_location("issue140_slice3a_triage", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    payload = module.build(ROOT)
    rows = tuple(csv.DictReader(io.StringIO(payload.decode("utf-8"))))
    assert len(rows) == 18
    assert {row["service_name"] for row in rows} == set(
        module.ARTIFACT + module.SCORE + module.LABELS
    )
    assert all(row["evidence_status"] == "BLOCKED_OR_UNTESTED" for row in rows)
    assert all(row["calls"].isdecimal() and int(row["calls"]) >= 1 for row in rows)
    assert all(row["qualification_owner"].startswith("#") for row in rows)
    # #140 is a frozen source census from the original qualification baseline.
    # Its contents must not be silently rewritten as #142 changes call lines.
    frozen = (ROOT / module.OUTPUT).read_bytes()
    frozen_header = f"blob {len(frozen)}\0".encode("ascii")
    assert hashlib.sha1(frozen_header + frozen).hexdigest() == (
        "4ba8a15db722d2ded9fca09c103028c23ab2cd98"
    )
    frozen_rows = tuple(csv.DictReader(io.StringIO(frozen.decode("utf-8"))))
    assert len(frozen_rows) == 18
    assert {row["service_name"] for row in frozen_rows} == {
        row["service_name"] for row in rows
    }
    assert all(
        row["evidence_status"] == "BLOCKED_OR_UNTESTED" for row in frozen_rows
    )
    # A separate #142 successor inventory must track the CURRENT source exactly.
    # Do not label source-only candidate status as runtime verification.
    successor = ROOT / (
        "docs/audits/issue142/slice6c4_current_boundary_inventory.csv"
    )
    assert successor.read_bytes() == payload
    assert successor.read_bytes() != frozen


def test_mixed_activity_score_label_reader_silently_loses_native_definitions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    _create_native_mixed_criterion_set(fixture.root, fixture.standards)
    activity = show_activity(
        SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root
    ).summary
    # Establish that the authoritative graph data exists and reads correctly
    # with canonical context before exercising the genuine teacher label builder.
    native_scales = list_scoring_scales(
        SOURCE_CLASS,
        ACTIVITY_ID,
        workspace_root=fixture.root,
        standards_library=fixture.standards,
        current_only=False,
    )
    native_sets = list_criterion_sets(
        SOURCE_CLASS,
        ACTIVITY_ID,
        workspace_root=fixture.root,
        standards_library=fixture.standards,
        current_only=False,
    )
    assert native_scales and native_sets
    # The menu label projection has no Standards parameter. We inject only
    # the exact disposable workspace root; leave its missing library untouched.
    monkeypatch.setattr(
        teacher_labels,
        "list_scoring_scales",
        lambda *a, **kw: list_scoring_scales(*a, **kw, workspace_root=fixture.root),
    )
    monkeypatch.setattr(
        teacher_labels,
        "list_criterion_sets",
        lambda *a, **kw: list_criterion_sets(*a, **kw, workspace_root=fixture.root),
    )
    monkeypatch.setattr(teacher_labels, "list_groups", lambda *a, **kw: ())
    monkeypatch.setattr(teacher_labels, "list_sessions", lambda *a, **kw: ())
    monkeypatch.setattr(
        teacher_labels, "list_teacher_artifact_choices", lambda *a, **kw: ()
    )
    monkeypatch.setattr(
        teacher_labels, "resolve_read_workspace_root", lambda: fixture.root
    )
    # Confirm the failure is *specifically* the guarded Standards read, not a
    # fixture setup problem or a missing Criterion/Scale definition.
    with pytest.raises(
        Exception, match="standards_library is required for this Activity"
    ):
        teacher_labels.list_scoring_scales(
            SOURCE_CLASS, ACTIVITY_ID, current_only=False
        )
    with pytest.raises(
        Exception, match="standards_library is required for this Activity"
    ):
        teacher_labels.list_criterion_sets(
            SOURCE_CLASS, ACTIVITY_ID, current_only=False
        )
    labels = teacher_labels.build_score_teacher_labels(
        activity, include_score_definitions=True
    )
    assert labels.scales == {}
    assert labels.criteria == {}
    assert labels.scale("issue140-scale") == "Scoring Scale label unavailable"
    assert (
        labels.criterion("issue140-criterion-individual")
        == "Criterion label unavailable"
    )
    assert list_work_snapshots(fixture.root, _work())


@pytest.mark.parametrize("explicit", (False, True))
def test_page_preparation_uses_explicit_or_internal_canonical_context_without_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, explicit: bool
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    before = list_work_snapshots(fixture.root, _work())
    seen: list[tuple[str, object]] = []
    token = object()

    class StopAtRead(Exception):
        pass

    def self_resolve(root: Path) -> Any:
        assert root == fixture.root
        seen.append(("resolve", token))
        return token

    def guarded_read(root: Path, work: ModuleWorkRef, **kw: Any) -> Any:
        assert root == fixture.root
        assert work == _work()
        assert kw.get("standards_library") is token
        seen.append(("read", token))
        raise StopAtRead("safe pre-write evidence probe")

    monkeypatch.setattr(artifact_pages, "_standards", self_resolve)
    monkeypatch.setattr(artifact_pages, "load_current_record_graph", guarded_read)
    monkeypatch.setattr(
        artifact_pages,
        "commit_record_batch",
        lambda *a, **kw: pytest.fail("no source-qualification write allowed"),
    )
    request = PrepareArtifactPagesRequest(
        class_id=SOURCE_CLASS,
        activity_id=ACTIVITY_ID,
        artifact_instance_id="issue140-unreturned-page-test",
        template_version_id="issue140-synthetic-template",
        artifact_category="worksheet",
        expected_snapshot_revision=1,
        actor=ACTOR,
        privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        pages=(ArtifactPagePlan(page_number=1, route_required=False),),
    )
    with pytest.raises(StopAtRead, match="safe pre-write evidence probe"):
        artifact_pages.prepare_artifact_pages(
            request,
            workspace_root=fixture.root,
            standards_library=token if explicit else None,
        )
    expected = (
        [("read", token)]
        if explicit
        else [
            ("resolve", token),
            ("read", token),
        ]
    )
    assert seen == expected
    assert list_work_snapshots(fixture.root, _work()) == before

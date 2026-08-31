from __future__ import annotations

from scripts import smoke_test_feature_wheels as feature_smokes
from scripts import smoke_test_starter_workflows_wheel as starter_smoke


def test_issue70_slice1_registers_one_shared_starter_workflow_scenario() -> None:
    matches = tuple(
        item
        for item in feature_smokes.SCENARIOS
        if item[2] == "scripts/smoke_test_starter_workflows_wheel.py"
    )
    assert matches == (
        (
            "starter workflows",
            "starter_workflows_smoke.py",
            "scripts/smoke_test_starter_workflows_wheel.py",
        ),
    )


def test_issue70_slice1_seminar_smoke_covers_required_installed_boundaries() -> None:
    source = starter_smoke._smoke_code()
    compile(source, "starter_workflows_smoke.py", "exec")

    required_fragments = (
        'metadata.version("pds-core") == "0.6.3"',
        'metadata.version("pds-concord") == "0.3.0"',
        "launch_guided_activity_menu(state)",
        'get_starter_template("socratic_seminar")',
        "create_manual_group_plan(",
        "preview_group_plan(",
        "approve_group_plan(",
        "prepare_group_plan_application(",
        "apply_group_plan(",
        "prepare_packet_instantiation(",
        "commit_packet_instantiation(",
        "render_packet_generation(",
        "parse_pds2_payload(payload)",
        "route_scan_sources(pdf_paths",
        "assemble_returned_artifact(",
        "add_artifact_review(",
        "add_score(",
        "register_concord_academic_work(",
        "generate_academic_result_manifest(",
        "publish_concord_academic_results(",
        "read_academic_result_manifest(",
    )
    for fragment in required_fragments:
        assert fragment in source

    assert 'previewed.plan.status == "previewed"' in source
    assert "expected_snapshot_revision=previewed.summary.snapshot_revision" in source
    assert 'previewed.status == "previewed"' not in source
    assert "previewed.commit.snapshot_revision" not in source


def test_issue70_slice1_preserves_participant_and_no_meridian_boundaries() -> None:
    source = starter_smoke._smoke_code()
    assert 'audience_kind="participant"' in source
    assert 'target.audience_kind == "participant"' in source
    assert 'target.group_id in group_ids' in source
    assert "artifact_by_student" in source
    assert "student-1" in source
    assert "student-4" in source
    assert 'forbidden = ("meridian", "paper-data-suite")' in source
    assert 'module_name.startswith("meridian")' in source


def test_issue70_slice1_automated_path_starts_from_rendered_pdfs() -> None:
    source = starter_smoke._smoke_code()
    render_index = source.index("render_packet_generation(")
    intake_index = source.index("route_scan_sources(pdf_paths")
    review_index = source.index("add_artifact_review(")
    score_index = source.index("add_score(")
    publish_index = source.index("publish_concord_academic_results(")

    assert render_index < intake_index < review_index < score_index < publish_index
    assert "decoder=" not in source
    assert "raw_decoder=" not in source
    assert "fabricated" not in source.casefold()


def test_issue70_slice2_project_smoke_covers_signal_backed_group_path() -> None:
    source = starter_smoke._smoke_code()
    required_fragments = (
        'GroupingSignalSet(',
        'write_grouping_signal(root, signal)',
        'calculate_grouping_signal_digest(signal)',
        'CreateSignalGroupPlanRequest(',
        'strategy="similar_signal"',
        'fallback_effective_context=project_context',
        'get_starter_template("project_plan")',
        'audience_kind="group"',
        'target.audience_kind == "group"',
        'supported_target_kinds=("concord_group",)',
        'target_kind="concord_group"',
        'subject_kind="concord_group"',
        'privacy_judgment="group_and_teacher"',
        'classification="group_and_teacher"',
    )
    for fragment in required_fragments:
        assert fragment in source

    assert "signal_plan.mutation.group_plan_id" in source
    assert "signal_plan.mutation.commit.snapshot_revision" in source
    assert "signal_plan.group_plan_id" not in source
    assert "signal_plan.commit.snapshot_revision" not in source

    project_render = source.index("project_rendered = render_packet_generation(")
    project_intake = source.index("project_returned = route_scan_sources(")
    project_review = source.index("review-project-")
    project_score = source.index("score-project-")
    project_publish = source.index(
        "project_publication = publish_concord_academic_results("
    )
    assert (
        project_render
        < project_intake
        < project_review
        < project_score
        < project_publish
    )


def test_issue70_slice2_enforces_signal_privacy_and_dynamic_page_contracts() -> None:
    source = starter_smoke._smoke_code()
    privacy_fragments = (
        'private_signal_set_id = "issue70-private-signal-set"',
        'private_dimension_id = "issue70-private-proficiency-band"',
        'private_source_module = "issue70_private_producer"',
        'private_snapshot_id = "issue70-private-snapshot"',
        'private_snapshot_digest = "7" * 64',
        'private_canonical_digest = calculate_grouping_signal_digest(signal)',
        'assert_private_absent(project_prepared_generation, private_tokens)',
        'assert_private_absent(packet.output_path.read_bytes(), private_tokens)',
        'assert_private_absent(project_generated.content, private_tokens)',
        'downstream_records = (',
    )
    for fragment in privacy_fragments:
        assert fragment in source

    assert "seminar_page_count = starter.page_count" in source
    assert "project_page_count = project_starter.page_count" in source
    assert 'starter.page_count == 2' not in source
    assert 'project_starter.page_count == 1' not in source


def test_issue70_slice3_peer_review_smoke_covers_random_participant_path() -> None:
    source = starter_smoke._smoke_code()
    required_fragments = (
        'CreateRandomGroupPlanRequest(',
        'seed="issue70-peer-review-seed"',
        'random_plan.mutation.group_plan_id',
        'fallback_effective_context=peer_context',
        'get_starter_template("peer_review_writing")',
        'peer_page_count = peer_starter.page_count',
        'audience_kind="participant"',
        'target.group_id in peer_group_ids',
        'generation_id="generation-peer-review-issue70"',
        'supported_target_kinds=("core_student",)',
        'criterion_id="criterion-peer-review-quality"',
        'peer_registration = register_concord_academic_work(',
        'peer_publication = publish_concord_academic_results(',
        'peer_stage("peer-review workflow complete")',
    )
    for fragment in required_fragments:
        assert fragment in source

    assert 'peer_previewed.plan.strategy == "random"' in source
    assert 'peer_previewed.plan.source_signal_set_id is None' in source
    assert 'peer_previewed.plan.source_signal_set_digest is None' in source
    assert 'peer_previewed.plan.source_signal_dimension_id is None' in source

    peer_plan = source.index("random_plan = create_random_group_plan(")
    peer_preview = source.index("peer_previewed = preview_group_plan(")
    peer_approve = source.index("peer_approved = approve_group_plan(")
    peer_apply_preview = source.index(
        "peer_application = prepare_group_plan_application("
    )
    peer_apply = source.index("peer_applied = apply_group_plan(")
    peer_render = source.index("peer_rendered = render_packet_generation(")
    peer_intake = source.index("peer_returned = route_scan_sources(")
    peer_review = source.index('artifact_review_id=f"review-peer-')
    peer_score = source.index('peer_score_id = f"score-peer-')
    peer_publish = source.index(
        "peer_publication = publish_concord_academic_results("
    )
    assert (
        peer_plan
        < peer_preview
        < peer_approve
        < peer_apply_preview
        < peer_apply
        < peer_render
        < peer_intake
        < peer_review
        < peer_score
        < peer_publish
    )

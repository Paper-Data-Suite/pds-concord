from __future__ import annotations


def test_issue58_template_workflows_are_public_facade_exports() -> None:
    from concord import workflows

    required = (
        "PrepareTemplateActivationRequest",
        "PrepareTemplateCreateRequest",
        "PrepareTemplateRetireRequest",
        "PrepareTemplateRetireVersionRequest",
        "PrepareTemplateRevisionRequest",
        "PrepareTemplateUpdateRequest",
        "PreparedTemplateActivation",
        "PreparedTemplateCreate",
        "PreparedTemplateRetire",
        "PreparedTemplateRetireVersion",
        "PreparedTemplateRevision",
        "PreparedTemplateUpdate",
        "TemplateDetail",
        "TemplateMutationResult",
        "TemplateSummary",
        "commit_template_activation",
        "commit_template_create",
        "commit_template_retire",
        "commit_template_retire_version",
        "commit_template_revision",
        "commit_template_update",
        "get_template",
        "list_templates",
        "prepare_template_activation",
        "prepare_template_create",
        "prepare_template_retire",
        "prepare_template_retire_version",
        "prepare_template_revision",
        "prepare_template_update",
    )
    for name in required:
        assert hasattr(workflows, name), name
        assert name in workflows.__all__

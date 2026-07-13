# Concord Architecture Decision Records

This directory contains the Architecture Decision Records for `pds-concord`.

An Architecture Decision Record documents one significant architectural decision, the problem that required the decision, the selected approach, its consequences, and the principal alternatives considered.

Accepted ADRs constrain later conceptual contracts, schemas, storage decisions, interfaces, and implementation work.

## Naming Convention

ADR files use a four-digit sequence followed by a concise, lowercase, hyphenated title:

```text
NNNN-decision-name.md
```

Examples:

```text
0001-concord-module-boundaries.md
0009-many-to-many-evidence-to-score-relationships.md
```

Numbers are never reused, even when an ADR is later superseded or deprecated.

## Current Decisions

| ADR                                                                        | Decision                                                      | Status   |
| -------------------------------------------------------------------------- | ------------------------------------------------------------- | -------- |
| [0001](0001-concord-module-boundaries.md)                                  | Concord Module Boundaries                                     | Accepted |
| [0002](0002-paper-first-human-reviewed-evidence.md)                        | Paper-First, Human-Reviewed Evidence                          | Accepted |
| [0003](0003-activities-require-explicit-sessions.md)                       | Activities Require Explicit Sessions                          | Accepted |
| [0004](0004-contextual-groups-memberships-and-roles.md)                    | Contextual Groups, Memberships, and Roles                     | Accepted |
| [0005](0005-separate-artifact-authors-and-subjects.md)                     | Separate Artifact Authors and Subjects                        | Accepted |
| [0006](0006-distinguish-roles-responsibilities-tasks-and-contributions.md) | Distinguish Roles, Responsibilities, Tasks, and Contributions | Accepted |
| [0007](0007-preserve-source-evidence-and-history.md)                       | Preserve Source Evidence and History                          | Accepted |
| [0008](0008-separate-review-moderation-scoring-grading-and-reporting.md)   | Separate Review, Moderation, Scoring, Grading, and Reporting  | Accepted |
| [0009](0009-many-to-many-evidence-to-score-relationships.md)               | Many-to-Many Evidence-to-Score Relationships                  | Accepted |
| [0010](0010-exceptional-evidence-states-are-not-low-scores.md)             | Exceptional Evidence States Are Not Low Scores                | Accepted |
| [0011](0011-link-external-artifacts-without-managing-source-systems.md)    | Link External Artifacts Without Managing Source Systems       | Accepted |
| [0012](0012-link-scoreform-and-quillan-without-duplication.md)             | Link ScoreForm and Quillan Without Duplication                | Accepted |
| [0013](0013-keep-activity-specific-structures-optional.md)                 | Keep Activity-Specific Structures Optional                    | Accepted |

## Standard ADR Structure

Each ADR should normally contain:

```text
# ADR NNNN: Decision Title

Status
Date
Decision owners
Applies to

Context
Decision
Consequences
Alternatives Considered
Required Follow-Up
References
Notes
```

The exact number of subsections may vary, but each ADR must clearly include:

* the design pressure or problem;
* the accepted decision;
* important positive and negative consequences;
* credible alternatives considered;
* required follow-up work;
* and references to supporting design material.

An ADR should address one coherent architectural decision.

It should not become a replacement for:

* a domain model;
* a complete conceptual contract;
* an implementation plan;
* a schema specification;
* or a user-interface design.

## ADR Statuses

The normal statuses are:

### Proposed

The decision is under consideration and has not yet been accepted.

### Accepted

The decision governs current design and implementation work.

### Deprecated

The decision is no longer recommended, but no single later ADR fully replaces it.

A deprecated ADR must explain why it was deprecated and point to relevant later guidance.

### Superseded

A later ADR replaces the decision.

A superseded ADR must identify the replacing ADR.

### Rejected

The proposal was considered but not adopted.

Rejected ADRs may be retained when the reasoning is valuable and likely to recur.

## Adding a New ADR

Before adding an ADR:

1. Confirm that the subject is an architectural decision rather than an unresolved question, implementation detail, or ordinary documentation update.
2. Review the existing ADRs for overlap or conflict.
3. Choose the next unused sequence number.
4. Create a file using the naming convention.
5. Begin with `Proposed` unless the decision has already been explicitly accepted.
6. Explain the decision independently enough that a future maintainer can understand it without reconstructing the entire discussion.
7. Identify consequences and credible rejected alternatives.
8. Link the relevant design, domain, contract, issue, or module documentation.
9. Add the ADR to the table in this README.
10. Check the full ADR set for consistency.

A new ADR should be preferred when a change:

* alters module ownership;
* changes foundational cardinality or identity rules;
* changes evidence or scoring semantics;
* changes source-preservation requirements;
* introduces automated interpretation;
* changes dependency direction;
* moves responsibility between Paper Data Suite modules;
* or reverses an accepted architectural constraint.

## Editing an Accepted ADR

Accepted ADRs may be edited for limited non-semantic maintenance, including:

* correcting typographical errors;
* repairing links;
* improving formatting;
* clarifying wording that does not change the decision;
* or adding references to later supporting documents.

An accepted ADR must not be silently edited to reverse, weaken, or materially expand its decision.

When a substantive architectural decision changes, create a new ADR.

The new ADR should explain:

* what changed;
* why the earlier decision is no longer sufficient;
* which earlier ADRs are affected;
* and whether they are superseded or deprecated.

## Superseding an ADR

To supersede an ADR:

1. Create a new ADR with the next unused number.
2. Set the new ADR status to `Accepted`.
3. Explain the relationship to the earlier decision.
4. Change the earlier ADR status to:

```text
Superseded by ADR NNNN
```

5. Add a prominent reference from the earlier ADR to the new ADR.
6. Update this index.
7. Preserve the original decision text and reasoning.

Supersession is historical, not destructive.

The earlier ADR remains part of the project record.

## Deprecating an ADR

Deprecation is appropriate when a decision should no longer guide new work but is not fully replaced by one later ADR.

To deprecate an ADR:

1. Change its status to `Deprecated`.
2. Add a brief explanation.
3. Link any relevant replacement guidance.
4. Update this index.
5. Preserve the original decision and rationale.

## Relationship to Other Documentation

The broader Concord documentation index is located at:

* [`../README.md`](../README.md)

The ADRs are supported by:

* [`../concord-conceptual-design-revised.md`](../concord-conceptual-design-revised.md)
* [`../design/cross-case-requirements.md`](../design/cross-case-requirements.md)
* [`../design/initial-concord-domain-model.md`](../design/initial-concord-domain-model.md)
* [`../packet_models/socratic-seminar-packet-model.md`](../packet_models/socratic-seminar-packet-model.md)
* [`../packet_models/science-laboratory-group-packet-model.md`](../packet_models/science-laboratory-group-packet-model.md)
* [`../packet_models/collaborative-programming_engineering_project_packet_model.md`](../packet_models/collaborative-programming_engineering_project_packet_model.md)

When documents disagree:

1. an accepted ADR governs the architectural decision;
2. an accepted conceptual contract should govern the detailed record structure;
3. implementation documentation should describe the current implementation;
4. exploratory and packet-model documents remain supporting rationale and representative cases.

Implementation convenience must not silently override an accepted ADR.

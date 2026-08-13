# Artifact Review and Moderation

**Status:** Implemented for issue #29 on the v0.2.0 development line.

## Purpose

Concord treats physical evidence, attribution, human Review, Moderation, Score,
Grade, publication, and reporting as distinct record families and decisions.

Issue #29 activates the native `ArtifactReview` and `ModerationRecord` contracts
without changing the evidence chain established through issues #27 and #28.

The intended conceptual sequence is:

```text
Evidence
    -> optional Artifact Review
    -> optional Moderation
    -> optional Score (#30)
    -> optional publication (#31)
    -> optional Meridian policy/reporting
```

This is not an automatic pipeline. A returned Artifact may remain unreviewed. A
Review may stop because evidence is incomplete. Moderation may reject or restrict
evidence without creating a negative Score. An accepted Moderation decision does
not select a Criterion, Score target, Score value, Grade, or publication.

## Artifact Review

An `ArtifactReview` is one explicit human administrative examination of one
`ArtifactInstance`.

The teacher records:

- readability;
- page completeness;
- filing;
- Author attribution confidence;
- Subject attribution confidence;
- privacy judgment;
- relevance;
- Moderation requirement;
- scoring readiness;
- overall Review outcome;
- optional/required explanatory notes; and
- the independent privacy policy protecting the Review record.

Review values are never inferred from Artifact return status, route identity,
Scan References, assembly output, OCR, Authors, Subjects, Group Membership,
Role Assignment, timestamps, or future Score state.

### Return state remains independent

Review does not mutate:

- `ArtifactInstance.artifact_status`;
- `ArtifactPage.page_status`;
- PDS2 routes;
- Scan References;
- Core-retained source bytes;
- assembly lineage;
- Authors;
- Subjects;
- Scores; or
- Core publication state.

A physically incomplete Artifact may therefore receive an `incomplete` or
`awaiting_additional_evidence` Review with `scoring_readiness=not_ready`.

### Review coherence

The native model rejects contradictory combinations.

`ready` requires:

```text
scoring_readiness = ready
moderation_requirement != required
```

and cannot coexist with obvious blockers such as unreadable, incomplete,
misfiled, duplicate, or not-relevant evidence.

`ready_with_qualification` requires:

```text
scoring_readiness = ready_with_qualification
notes = nonempty
```

`moderation_required` requires:

```text
moderation_requirement = required
scoring_readiness = not_ready
```

Clearly blocking overall outcomes require `not_ready`.

These checks prevent contradictory administrative state; they do not automate
the educational judgment.

## Review history

The initial contract supports one Review lineage per Artifact.

The first Review has no predecessor. A later Review:

1. receives a new durable `artifact_review_id`;
2. supersedes the current Review head explicitly;
3. preserves the predecessor;
4. has a decision time not earlier than the predecessor; and
5. atomically creates a `CorrectionRecord` with
   `correction_type=review_correction`.

Current Review state derives only from the explicit supersession graph. Concord
does not choose a Review by ID, filesystem order, storage revision, mtime, or
maximum timestamp. Competing current heads are invalid.

## Moderation

A `ModerationRecord` is an authorized human decision about whether and how one
exact evidence source may be used consequentially.

Moderation can target:

```text
concord artifact_instance
concord artifact_page
scoreform_result
quillan_response
external_record
```

No ScoreForm or Quillan package import is required.

Moderation records:

- an exact `EvidenceReference`;
- zero, one, or many explicit `SubjectReference` values;
- moderator and decision time;
- decision status;
- permitted use;
- mandatory rationale;
- optional/required qualification;
- independent Moderation-record privacy; and
- explicit supersession where revised.

### Exact evidence

Concord-owned Artifact and Page evidence must resolve in the current Activity.

External evidence must carry immutable lineage using an exact immutable source
version and/or a Core Publication reference. Mutable aliases such as `latest`,
`current`, and `mutable` are rejected.

When a `CorePublicationReference` is supplied, Concord resolves the exact
Publication Record through the public
`pds_core.registry_services.get_canonical_publication_record` API. Concord
verifies:

- the Publication Record exists;
- an explicitly supplied publication schema version matches; and
- the publication's producer module matches the Evidence Reference owner.

Concord does not crawl sibling work directories, open undocumented sibling
files, infer a current publication, or copy the external evidence.

### Explicit Subject scope

Zero Subjects means a general evidence decision. Non-empty scope is explicit.

Core-student scope is resolved through the exact Core class roster. Concord
Group, Session, Activity, and Artifact references must resolve in the same
Activity. External Subjects remain typed external references.

Subject scope is canonicalized deterministically and duplicates are rejected.
It is never inferred from:

- Artifact Authors;
- Artifact Subjects;
- Score targets;
- Group Membership; or
- evidence metadata.

### Decision coherence

Supported statuses are:

```text
accepted
accepted_with_qualification
insufficient
disputed
rejected
not_used_for_scoring
```

Supported permitted uses are:

```text
support_group_score
support_named_subject
corroborate_only
formative_only
not_independently_determine_score
not_be_used_for_scoring
```

`accepted_with_qualification` requires a qualification. Rejected or
not-used-for-scoring evidence must use `not_be_used_for_scoring`.
`insufficient` and `disputed` evidence cannot directly support a named Subject
or Group Score. Named-Subject support requires explicit Core-student scope.
Group-score support requires explicit Concord-Group scope.

## Moderation history and applicability

Current Moderation identity is:

```text
exact EvidenceReference + canonical Subject scope
```

Different Subject scopes for the same evidence are independent decisions.

A revision receives a new durable ID, preserves exact evidence and exact Subject
scope, uses a non-backward decision time, retains the predecessor, and atomically
creates:

```text
CorrectionRecord(correction_type="moderation_revision")
```

The reader:

```python
list_applicable_moderation_records(
    class_id,
    activity_id,
    evidence_reference,
    *,
    subject_context=(),
)
```

returns every current decision that applies to the exact evidence and requested
Subject context. It never chooses one candidate based on timestamp or ID.

## Handoff to scoring

Issue #29 does not create Criteria, Scoring Scales, Scores, Score Evidence
Links, Grades, or publications.

The effective Moderation requirement for a later evidence use is required when
either:

```text
EvidenceReference.moderation_requirement == required
```

or the current Artifact Review requires Moderation.

A caller cannot bypass a current Review requirement by constructing an otherwise
equivalent Evidence Reference marked `not_required`.

Existing graph validation also rejects a Score Evidence Link that tries to rely
on:

- a historical Moderation decision;
- a Moderation decision for different evidence;
- a non-applicable Subject scope;
- a permitted use that does not match the Score target;
- `formative_only`;
- `not_be_used_for_scoring`; or
- a non-accepted decision when required Moderation must be satisfied.

This is validation of the boundary only. Score creation remains issue #30.

## Direct CLI

The direct, noninteractive commands are:

```text
concord artifact review add
concord artifact review list
concord artifact review show
concord artifact review replace

concord moderation add
concord moderation list
concord moderation show
concord moderation replace
```

Broad Review listing omits Review notes. Broad Moderation listing omits
Moderation rationale. Exact `show` commands expose the selected record's detail.

Repeated Moderation Subject scope uses:

```text
--target-subject KIND,OWNER,ID[,CONTRACT_VERSION]
```

External evidence accepts exact contract, Core Publication, and immutable-source
lineage fields. No `latest` or `current` selector is provided.

## Teacher menu

The Artifact menu preserves the issue #28 choices and adds:

```text
8. Review
9. Moderation
```

Review offers current state, preserved history, first Review entry, and explicit
successor entry.

Moderation offers decision inspection, new decision entry, same-scope revision,
and applicable-decision inspection.

The menu uses the shared typed services, ten-row selection pagination, standard
H/B/M/Q navigation, stale-snapshot reload behavior, and explicit confirmation
words:

```text
REVIEW
MODERATE
REVISE
```

A Moderation revision reuses the predecessor's exact evidence and canonical
Subject scope instead of asking the teacher to reconstruct them.

## Pure graph integrity

Pure graph validation covers:

- Review parent existence;
- one current Review head per Artifact;
- Review supersession acyclicity, nonbranching, same-Artifact context, and
  non-backward time;
- exact Review correction linkage;
- Moderation evidence existence/ownership;
- Moderation Subject existence and Activity containment;
- deterministic current Moderation heads by exact evidence/scope;
- same-scope Moderation supersession and non-backward time;
- exact Moderation correction linkage;
- correction type/target agreement; and
- the Score handoff restrictions described above.

Validation reports contradictions. It does not repair, select, or reinterpret
human decisions.

## Installed-wheel acceptance

The isolated wheel smoke extends the existing Activity -> Artifact -> PDS2 route
-> retained source -> Scan Reference -> return -> Author -> Subject path with:

```text
Artifact Review requiring Moderation
-> applicable Moderation decision
-> reload
```

The smoke verifies that Review and Moderation survive canonical reload, current
Review is deterministic, Moderation lineage is exact, and pre-existing
Artifact/Page/ScanReference/Author/Subject records plus retained source bytes
remain unchanged. No Score or Score Evidence Link is created, and Concord still
declares no publication-producer entry point.

Representative repository tests additionally cover peer observation,
recorder-for-Group, teacher tracker, attribution dispute/correction, incomplete
evidence followed by a successor Review, and the same evidence moderated
independently for two Subject scopes.

## Ownership boundary

Core remains authoritative for workspace/class/roster identity, PDS2 routing,
retained scans, Academic Work Registration, and Publication Records.

Concord owns Review, Moderation, their history, and evidence-use restrictions.

Issue #30 owns Criterion/Scale/Score workflows. Issue #31 owns Concord academic
publication projection. Meridian owns Grade policy, proficiency, Academic Period
membership, cumulative calculation, overrides, and reporting.

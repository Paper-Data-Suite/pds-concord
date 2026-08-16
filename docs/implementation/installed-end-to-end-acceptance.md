# Installed end-to-end acceptance

Issue #33 adds the distribution-level acceptance for Concord's v0.2.0
teacher-local Activity producer lifecycle. The authoritative run starts from a
newly built, noneditable Concord wheel and the released Core 0.6.0 wheel in a
fresh virtual environment. It does not use Concord or Core from a source
checkout.

## Qualified artifacts and isolation

The Core qualification artifact is exactly:

```text
pds_core-0.6.0-py3-none-any.whl
SHA-256 be28c061b38463ef59ebc328ed1aa443767fe7f2c626babb769c2d8e5932f308
```

`scripts/verify_core_wheel.py` authenticates that artifact before repository
validation. `scripts/smoke_test_wheel.py` creates a fresh wheel environment and
an outside working directory, installs both wheels noneditably, and runs the
existing side-effect-free profile, reader, help, version, and quit-only checks
before any mutation-heavy acceptance. The producer acceptance receives a
separate empty workspace.

The dedicated
`scripts/verify_installed_producer_acceptance.py` program verifies distribution
versions, the declared Core requirement, module origins under the isolated
environment's `site-packages`, and the exact routing and publication-producer
entry points. It rejects checkout import leakage and checks that no ScoreForm,
Quillan, Portia, Meridian, or Vitrine runtime import was needed.

## Lifecycle

The harness prints one bounded status for each of these stages:

```text
installed provenance
synthetic native workflow
academic-work registration
manifest revision 1
public reader revision 1
initial publication
publication replay
catalog revision 1
Core verification revision 1
authorized artifact revision 1
native correction
manifest revision 2
supersession
catalog revision 2
Core verification revision 2
historical artifact
withdrawal
final catalog
registry audit
immutability
```

The single synthetic workflow creates a Core class and two-student roster, a
mixed-orientation Activity, Session, Group and Memberships, a synthetic Focus
Standard, and one return-expected PDS2 Artifact Page. Concord renders and routes
the page through installed production behavior, verifies retained-source
lineage, assembles the returned Artifact, and explicitly assigns different
Artifact Author and Artifact Subject identities.

At both producer revisions the harness requires the complete native and public
Score populations to equal the deliberately created history, including every
exact target. This proves that Group Membership, Artifact attribution, routing,
and other context did not synthesize an additional individual Score.

A real Review requires Moderation. The accepted-with-qualification Moderation
record then permits one standard-backed student Score to cite the exact Concord
Artifact through a Score Evidence Link. The workflow also records a local Group
Score and a valueless `absent` non-score state. Private Review, Moderation,
Score, status, and provenance text is required to remain outside public
manifest bytes.

Only an explicit Concord registration call creates Core Academic Work
Registration revision 1. Concord generates immutable manifest revision 1,
reads the durable bytes through its consumer-neutral reader, and publishes the
same bytes through Core. Exact publication replay must retain the original
publication identity. Core then rebuilds and queries its catalog, canonically
reloads the Publication Record and referenced registration, evaluates the
installed producer profile, and verifies manifest containment and SHA-256
before Concord reads the verified bytes.

A material replacement of the Group Score preserves the predecessor and creates
manifest revision 2. Core supersession must name the exact revision-1
publication. After catalog and verification checks, an unrelated Session note
advances current native state; the revision-1 manifest still drives an
authorization-gated Artifact read from its exact historical
`source_snapshot_revision`. Withdrawing the revision-2 structural head leaves no
current selectable publication and does not reactivate revision 1.

The final bounded Core `audit_academic_registry` call requests registrations,
publications, manifests, contracts, catalog, and locks for the exact synthetic
Concord work. It requires
one registration work/revision, two Publication Records, one series, one
withdrawal, two verified manifests, no errors, and no locks. A separate final
check compares captured registration, manifest, Publication Record, withdrawal,
retained-source, native-history, and installed-package bytes.

## Semantic and ownership boundaries

The acceptance preserves these distinctions rather than deriving one identity
or policy from another:

```text
Artifact Author != Artifact Subject
Artifact Subject != Score target
route target != Score target
Group Membership != authorship
Group Membership != individual Score
Group Score != individual Score
non-score disposition != zero
native Score history != consumer selection policy
manifest authorization != Artifact authorization
privacy classification != authorization
```

Concord production APIs own collaboration, Artifact, Review, Moderation, native
Score, manifest generation, publication orchestration, public interpretation,
and bounded Artifact representation. Core production APIs own registration and
publication persistence, withdrawal, catalog derivation, compatibility,
manifest verification, and registry audit. The harness never writes canonical
Core registry JSON or SQLite directly.

The deterministic Artifact authorization gate is deliberately narrow: it only
allows the complete request derived from the validated manifest and represented
evidence link: exact work, record-set revision, source snapshot, Score, link,
Evidence Reference, and purpose. Any changed field is denied. It defines no
teacher, administrator, student, recipient, privacy, or disclosure policy.
Catalog presence and manifest access are not treated as Artifact authorization.

Successful Artifact reads also assert one explicit Author, one explicit Subject,
one logical Artifact Page, exact Group/Session context, a one-page derived PDF
that differs from retained-source bytes, and the absence of retained paths,
digests, Scan/route metadata, filenames, and fallback text from every public
Artifact projection. Registration and both Publication Records are independently
reloaded and checked field-for-field against their exact versioned Activity,
manifest, registration, capability, and supersession envelopes.

## Invocation

Normal validation runs the acceptance automatically for the built wheel:

```text
python scripts/validate_repository.py --core-wheel <authenticated-core-wheel>
```

The dedicated program is invoked by the wheel smoke after installation. Its
expected Concord version is supplied from wheel metadata, so release closeout
can rerun the same lifecycle after version promotion without changing the
harness.

## Deliberate limits

Issue #33 does not define a new manifest contract, add sibling runtime
dependencies, calculate grades or proficiency, choose a preferred Score,
convert Group Scores to student Scores, infer authorship or subject identity,
or implement Meridian/Vitrine policy. Exhaustive malformed-manifest,
authorization-denial, and filesystem-race cases remain in the source suites.
Release promotion, tagging, publication, and final release authorization remain
work for issue #34.

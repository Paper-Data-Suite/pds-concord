# Security Policy

## Project Status

Concord is the Paper Data Suite module for paper-first collaborative classroom
evidence, including Activities, Sessions, Groups, Group Planning, Roles,
Responsibilities, reusable Templates and Packets, physical-paper routing,
Artifact assembly, Review, Moderation, Scoring, and academic-result publication.

The latest published Concord release is `0.2.0`. The current source tree is
developing `0.3.0` and reports package version `0.3.0.dev0`.

Concord is pre-1.0, local-first, teacher-controlled educational software. It is
not:

- a hosted service;
- an institutional identity provider;
- a gradebook;
- an autonomous grading system;
- an authorization provider;
- a legal-compliance certification; or
- a substitute for school or district security controls.

`main` and development versions such as `0.3.0.dev0` are development-only and
are not supported release artifacts.

Local-first operation reduces unnecessary remote data handling, but it does not
remove the need for appropriate:

- operating-system account security;
- filesystem access controls;
- device security;
- encryption where required;
- protected backups;
- authorization;
- retention and deletion practices;
- secure handling of printed and scanned materials;
- secure handling of exports and removable media; and
- compliance with applicable school, district, state, and federal requirements.

## Supported Versions

Concord is pre-1.0 and does not provide a long-term-support commitment.

For the current published release family:

| Version | Status |
| --- | --- |
| `main` / `0.3.0.dev0` | Development only; not a supported release artifact |
| latest released `0.2.x` | Supported |
| older superseded `0.2.x` releases | Upgrade recommended; fixes may require the latest `0.2.x` |
| `<=0.1.x` | Unsupported unless explicitly documented otherwise |

A future published `0.3.x` release supersedes this table when the repository's
release policy is updated for that line.

There is no guaranteed vulnerability-response SLA, maintenance window, or
backport period. Pre-1.0 fixes may require upgrading to the latest supported
Concord release.

## Student Data and Privacy

Concord workspaces may contain highly sensitive educational records.

Do not commit, upload, publish, attach, or otherwise expose real classroom data
in this repository, public issues, pull requests, discussions, screenshots, CI
logs, examples, generated artifacts, or other public development material.

Do not publicly post:

- real student names;
- real student IDs or other identifiers;
- real class rosters;
- real Group or Membership assignments;
- real GroupPlans or planning rationale;
- grouping signals derived from real students;
- Role or Responsibility assignments tied to real students;
- student work, scans, photographs, or transcriptions;
- generated Packets or classroom materials containing real identifiers;
- Artifact images or assembled student submissions;
- review or moderation records tied to real students;
- Scores, standards ratings, criterion judgments, or grade-like information;
- Academic Work Registrations tied to real classroom work;
- Concord Academic Result Manifests containing real classroom information;
- Core Publication Records tied to real classroom work;
- exported reports or generated files containing identifiable records;
- production Paper Data Suite workspaces;
- workspace backups;
- private school or district documents;
- parent, guardian, or student contact information;
- credentials, access tokens, secrets, private keys, or private configuration;
- diagnostic output containing identifiable classroom information; or
- screenshots or logs exposing sensitive filesystem, account, or deployment
  information.

Repository examples, fixtures, screenshots, demonstrations, and tests must use
synthetic data.

Synthetic data should use clearly fictional names, identifiers, classes,
Activities, assignments, grouping signals, Groups, Scores, scans, and
publication records.

Do not lightly alter or pseudonymize real classroom records and then treat them
as synthetic fixtures.

Before committing generated files, logs, screenshots, fixtures, scans, PDFs,
manifests, reports, or diagnostic output, verify that they contain no copied
classroom information or identifying metadata.

## Local-First Data Handling

Concord is designed around teacher-controlled storage inside the Paper Data
Suite workspace.

Local-first does not mean that files are automatically safe merely because they
remain on a local filesystem.

Users should protect production workspaces with deployment-appropriate controls,
including:

- secure operating-system accounts;
- appropriate filesystem permissions;
- full-disk or removable-media encryption where required;
- protected backup destinations;
- secure handling of externally synchronized folders;
- controlled access to shared or network storage;
- deliberate review before exporting or sharing records;
- appropriate retention and disposal procedures; and
- physical protection of printed classroom materials.

Anyone able to read a production workspace may be able to read sensitive
student or classroom records stored there.

Users remain responsible for following applicable school, district, state, and
federal requirements when handling educational records.

## Repository and Workspace Separation

A production Concord or Paper Data Suite workspace must not be stored inside
this source repository.

Repository ignore rules are a development safeguard, not a privacy boundary.

Do not rely on `.gitignore` to protect real classroom data.

Before every commit or pull request:

1. inspect `git status`;
2. inspect the staged file list;
3. review generated files, scans, PDFs, images, logs, and diagnostics;
4. confirm that no production workspace material is staged;
5. confirm that no credentials, tokens, private configuration, or sensitive
   filesystem information is staged; and
6. confirm that all fixtures and examples are synthetic.

Do not copy a production classroom workspace into the repository merely to
reproduce a bug. Build a synthetic reproduction instead.

## Concord Security and Integrity Boundaries

Concord owns collaborative classroom domain state. PDS Core owns shared
infrastructure and contracts according to the documented Paper Data Suite
architecture.

Security-sensitive code must preserve distinctions such as:

```text
filesystem access != authorization

record discoverability != permission to read record contents

student identity != permission to disclose student work

GroupPlan != Group

Group != GroupMembership

grouping signal != permanent learner label

grouping signal != Score

grouping signal != Grade

planned grouping != approved grouping

approved GroupPlan != applied Membership state

Role definition != Role Assignment

Responsibility definition != Responsibility Assignment

Template != Activity-specific printed Artifact

Packet definition != prepared classroom copies

QR / PDS2 identity != authorization

scan presence != valid Artifact assembly

Artifact assembly != Review completion

Review completion != Moderation decision

criterion evidence != Score

Score != Grade

standard-linked evidence != proficiency

publication != downstream ingestion

publication discovery != authorization to consume referenced evidence

successful parsing != trusted provenance

hash agreement != confidentiality

package installation != deployment authorization
```

Concord must not silently collapse these distinctions.

## Ownership Boundaries

Concord owns its canonical domain records and workflows, including, as
applicable:

- Activities;
- Sessions;
- GroupPlans;
- Groups;
- GroupMemberships;
- Role Assignments;
- Responsibility Assignments;
- Concord-owned reusable presets;
- Template and Packet definitions and versions;
- Activity-specific Packet Instances;
- Artifacts and Artifact Pages;
- Authors and Subjects;
- Reviews and Moderation;
- Criterion Sets and Criteria;
- native Scoring Scales;
- Scores and Score evidence;
- Concord producer manifests; and
- Concord-specific workflow history.

Core owns shared infrastructure such as workspace authority, class and roster
authority, shared routing and retained-source services, shared identifiers,
standards contracts, Academic Work Registration, Publication Records,
authorization interfaces, compatibility contracts, and other explicitly
documented cross-module services.

Concord must not:

- mutate another module's canonical records;
- use Core as an alternate store for Concord-owned records;
- bypass Core-owned publication or routing authority;
- treat another module's private storage as a Concord API;
- create a sibling-module runtime dependency as a shortcut around Core
  contracts; or
- infer semantic authority from incidental filesystem access.

## Group Planning and Grouping-Signal Privacy

Grouping workflows are especially privacy-sensitive because temporary planning
signals can be mistaken for permanent student characteristics.

Concord must preserve:

```text
temporary grouping signal != permanent learner profile

signal value != student ability label

signal availability != teacher obligation to use it

suggested GroupPlan != approved GroupPlan

approved GroupPlan != canonical Membership state
```

Grouping signals should remain purpose-limited, temporary, and bounded by the
Core grouping-signal contract.

Do not expose raw or unnecessary grouping-signal payloads in ordinary
teacher-facing screens, logs, diagnostics, exports, or publications.

Do not persist signal-derived labels such as "high," "low," "strong," "weak,"
"advanced," or "struggling" as permanent learner classifications merely because
a grouping algorithm used a temporary signal.

Applying a GroupPlan to canonical Groups or Memberships must remain an explicit
teacher-approved operation.

## Roles, Responsibilities, and Reusable Presets

Reusable Role, Responsibility, Criterion Set, and Scoring Scale presets are
definitions or starting points, not reusable student state.

Reuse must not copy or preserve earlier Activity-specific:

- student assignments;
- Membership state;
- evidence;
- reviews;
- moderation decisions;
- Scores;
- publications; or
- operational history.

Materialization into a new Activity must create fresh canonical operational
records where the relevant contract requires fresh identity.

A reusable preset must not become live inheritance that silently changes
already-created Activity state when the preset is later edited or retired.

## Templates, Packets, and Physical Materials

Concord may create reusable Templates and Packets and may prepare Activity-
specific printed materials.

Preserve the boundary:

```text
Template
-> Packet definition/version
-> Activity-specific Packet Instance
-> Artifact / Artifact Page
-> Core PDS2 routing
-> physical paper
```

Do not bypass Packet or Artifact authority merely because a Template can be
rendered directly.

Generated classroom materials may contain student or class identifiers and
operational PDS2 locators. Protect printed materials before, during, and after
classroom use.

A QR code, route ID, page ID, Artifact ID, Activity ID, student ID, or similar
identifier is not an authentication or authorization mechanism.

Printers, print queues, scanners, scanner software, OS preview caches, temporary
directories, and cloud-connected device software may create copies outside the
Paper Data Suite workspace. Users are responsible for configuring those systems
appropriately for student data.

Dispose of unwanted printed material according to applicable school or district
policy.

## Scan, Artifact, and Routing Security

Concord may process PDFs, images, retained scans, routed pages, Artifacts, and
other physical-work evidence.

Security-sensitive scan and Artifact processing should:

- reject path traversal outside intended roots;
- preserve exact retained-source provenance;
- avoid silently overwriting canonical source evidence;
- distinguish retained source material from derived files;
- avoid assuming machine-readable identity proves educational authorship;
- fail safely when routing or identity cannot be established;
- preserve ambiguity and review states;
- avoid silently selecting among conflicting or duplicate physical evidence;
- avoid exposing page images or private paths unnecessarily in logs; and
- use documented Core routing and retained-source services rather than creating
  a second routing authority.

A readable retained scan does not itself establish permission to disclose its
contents.

## Review, Moderation, and Scoring Boundaries

Concord may record teacher review, moderation, criteria, evidence, Scoring
Scales, and Scores.

These records must not be overstated.

Preserve distinctions such as:

```text
evidence present != evidence accepted

evidence accepted != Score

Score != Grade

criterion Score != course Grade

standards alignment != proficiency

unrated != low proficiency

review complete != publication authorized

moderation decision != automatic replacement of teacher judgment
```

Concord does not calculate a course Grade or downstream proficiency merely
because it stores criterion evidence or Scores.

Where downstream interpretation is supported, the authorized downstream
consumer remains responsible for its own evidence-selection, aggregation,
proficiency, mastery, Grade, reassessment, and reporting policies.

## Academic Result Publication and Downstream Consumers

Concord may publish immutable producer-owned academic-result manifests through
Core.

The intended boundary is:

```text
Concord producer-native state
-> immutable Concord Academic Result Manifest
-> Core Academic Work / Publication state
-> authorized compatible consumer discovery
```

Publication does not prove that a downstream consumer has:

- discovered the publication;
- received authorization;
- opened the manifest;
- inspected referenced evidence;
- imported any result;
- selected a Score;
- calculated proficiency;
- calculated a Grade; or
- generated a report.

Concord must not write directly into Meridian or another consumer's canonical
records.

A consumer's permission to inspect a manifest does not automatically grant
permission to open every referenced Artifact or evidence file. Artifact access
must continue to honor the relevant authorization boundary.

## Authorization

The following must not be treated as authorization by themselves:

- possession of a path;
- possession of an Activity ID;
- possession of a student ID;
- possession of a Group or Membership ID;
- possession of a Packet, Artifact, or page ID;
- possession of a publication ID;
- knowledge of a manifest path;
- knowledge of a digest;
- filesystem readability;
- publication discovery;
- package installation;
- producer-profile compatibility;
- matching student identity;
- manifest validity; or
- a caller-provided purpose string.

Where authorization is required, missing authorization must fail closed.

## Paths and Filesystem Safety

Concord reads and writes potentially sensitive records and artifacts inside the
Paper Data Suite workspace.

Filesystem-sensitive implementation should:

- reject traversal outside intended roots;
- use documented Core workspace and path services where appropriate;
- avoid treating string-prefix comparison as filesystem containment;
- avoid unsafe following of links or filesystem redirection;
- fail safely when canonical paths cannot be established;
- avoid destructive overwrite unless explicitly permitted;
- preserve immutable or revisioned records where required;
- protect staged and temporary writes;
- avoid exposing unnecessary absolute paths in user-facing output;
- treat filesystem state as potentially changing between validation and
  mutation; and
- preserve ownership boundaries when resolving shared and module-owned paths.

A valid or readable path does not itself establish permission to access the
referenced content.

## Integrity, Hashes, and Provenance

Concord and PDS Core may use SHA-256 or other exact identity mechanisms for
records, Artifacts, manifests, release artifacts, and source provenance.

A matching digest demonstrates that bytes agree with the expected digest.

It does not provide:

- encryption;
- confidentiality;
- access control;
- proof of legal authorization;
- proof of educational correctness;
- proof of authorship;
- proof that the source was trustworthy; or
- a digital signature unless an explicitly documented signed-verification
  mechanism is used.

Do not describe ordinary hash verification as stronger assurance than it
provides.

## Backups and External Storage

Whole-workspace backup and restore are suite-level responsibilities, but Concord
data stored in the canonical workspace may be included in those backups.

Production workspaces and backups may contain the same sensitive information as
the live Concord workspace.

When production data or backups are placed in:

- OneDrive;
- Google Drive;
- Dropbox;
- a network share;
- removable media;
- institutionally managed cloud storage; or
- another externally synchronized location,

synchronization, encryption, sharing, remote access, retention, account
compromise, and recovery behavior belong to that external storage system.

Concord does not make an external destination appropriate merely because it is
technically writable.

Use only teacher-controlled or institutionally approved storage appropriate for
the data involved.

## Dependencies and Release Artifacts

Concord's dependencies should remain minimal and deliberate.

Security-relevant dependency changes should be reviewed, tested, and documented
when they materially affect supported behavior.

Development currently targets Python 3.11 or newer and the repository's
documented compatible Core range. Release qualification must use the exact
supported dependency and artifact procedures documented for the release being
prepared.

Supported release artifacts should be produced and distributed through the
documented Concord release process.

Where exact wheel identity, checksums, compatibility verification, or
installed-wheel acceptance are part of release qualification:

- verify the expected artifact;
- fail closed on mismatch;
- do not silently substitute a source checkout;
- do not silently substitute a different Core wheel;
- do not treat a broad dependency range as proof that every matching version
  was release-qualified; and
- distinguish development source from supported release artifacts.

A package that imports successfully is not necessarily the package that was
qualified.

## Reporting a Vulnerability

Do not disclose sensitive vulnerability details in a public GitHub issue.

For suspected security vulnerabilities, use GitHub Private Vulnerability
Reporting for this repository when that workflow is available.

A private report should include only the minimum information needed to reproduce
and assess the issue:

- affected Concord version, branch, or commit;
- affected component or workflow;
- concise description;
- reproduction steps;
- expected behavior;
- observed behavior;
- potential impact;
- prerequisites or required permissions;
- suggested mitigation, if known; and
- current disclosure status.

Do not include real student data, production workspace contents, real scans,
credentials, private school or district material, or unrelated sensitive
information in a vulnerability report.

If GitHub Private Vulnerability Reporting is unexpectedly unavailable, do not
place exploit details or sensitive information in a public issue. Open only a
non-sensitive issue stating that a private security-reporting channel is needed.

## Reporting Non-Sensitive Security or Privacy Concerns

Public GitHub Issues may be used for non-sensitive:

- security-hardening suggestions;
- privacy-design questions;
- synthetic-data concerns;
- documentation gaps;
- dependency-maintenance concerns;
- workflow-integrity questions; and
- data-safety issues that can be described without exploit-sensitive or private
  information.

Do not include real student records, credentials, scans, production workspace
contents, or sensitive deployment information in a public issue.

## Security-Sensitive Areas

Reports are particularly appropriate for demonstrated problems involving:

- unauthorized access to student or classroom records;
- path traversal or workspace escape;
- unintended overwrite or deletion;
- unsafe symlink or filesystem-redirection handling;
- authorization bypass or fail-open behavior;
- unsafe scan, PDF, image, or temporary-file handling;
- incorrect PDS2 or physical-page routing;
- identity confusion that exposes another student's work;
- inappropriate cross-student data association;
- GroupPlan application without explicit approval;
- grouping-signal leakage or permanent labeling;
- grouping signals being treated as Scores or Grades;
- reusable presets copying Activity-specific student state;
- unauthorized access to Artifacts, reviews, Scores, or publications;
- publication state being treated as authorization;
- manifest or Artifact integrity failures;
- digest-verification bypass;
- package or release-artifact substitution;
- source-checkout shadowing that defeats installed-package verification;
- command injection;
- CI credential disclosure;
- sensitive student data appearing in logs, diagnostics, screenshots, or
  exceptions;
- unintended mutation during read-only or diagnostic operations;
- incorrect cross-module writes;
- Scores being silently promoted to Grades or proficiency; or
- any workflow that collapses a documented privacy, provenance, ownership,
  approval, or authorization boundary.

## Suspected Exposure or Incident

If real student data, credentials, or private school information is accidentally
committed or posted publicly:

1. stop further sharing of the material;
2. remove public access when possible;
3. rotate exposed credentials or tokens immediately;
4. notify the appropriate school or district contact according to local policy;
5. preserve only the minimum non-sensitive information needed to understand and
   remediate the software issue; and
6. do not rely on a normal Git revert alone as proof that sensitive historical
   content is no longer retrievable.

Repository history, forks, caches, CI artifacts, backups, and synchronized
copies may retain previously exposed content. Follow the applicable incident
response and records-management process rather than assuming deletion from the
current working tree resolves the exposure.

## Good-Faith Security Research

Good-faith testing should:

- use synthetic data;
- use systems, accounts, workspaces, and files you are authorized to access;
- minimize access to unrelated information;
- stop if real sensitive data is encountered;
- avoid retaining sensitive information;
- avoid modifying or destroying data unnecessarily;
- avoid disrupting classroom or institutional systems;
- report vulnerabilities privately;
- allow maintainers a reasonable opportunity to investigate and correct the
  problem before public disclosure; and
- comply with applicable law and organizational policy.

Do not test against systems, accounts, workspaces, devices, or data you do not
have permission to access.

This policy does not authorize activity against third-party systems.

## Scope

This policy applies to the `pds-concord` repository, its released package
artifacts, and Concord-owned domain records and workflows.

It does not make Concord responsible for the security implementation of PDS
Core, the suite shell, Meridian, or another installed module.

Cross-module behavior must preserve documented Core ownership, validation,
authorization, provenance, routing, publication, and compatibility boundaries.

## Compliance

Paper Data Suite and Concord are software infrastructure, not a legal
determination that a particular deployment satisfies FERPA, state
student-privacy law, district policy, records-retention requirements,
accessibility requirements, or other institutional obligations.

Teachers, administrators, developers, and deploying organizations remain
responsible for determining and following the requirements applicable to their
use.

This policy describes repository security intent and supported project
practices. It is not legal advice.

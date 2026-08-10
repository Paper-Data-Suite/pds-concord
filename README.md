# pds-concord

Concord is the Paper Data Suite module for paper-first, human-reviewed evidence
created during collaborative classroom Activities. The repository is in v0.2.0
development against the released `pds-core` v0.6.0 integration baseline.

The package now includes the collaboration-context workflow required to create
and manage Activities, Sessions, Groups, contextual Group Memberships, Roles,
and Responsibilities. The same typed service layer supports a fully
noninteractive direct CLI and a teacher-facing low-information-density menu.
Canonical state remains protected by immutable history, exact expected-snapshot
concurrency, and guarded batch commits.

Concord does **not** yet generate or route Artifact Pages, process scans,
assemble returned Artifacts, record Artifact Author or Subject associations,
perform Review or Moderation, record Scores, publish results, or calculate
Grades. Routing remains assigned to issue #27 and publication to issue #31.

## Requirements and installation

Concord requires Python 3.11 or newer and `pds-core>=0.6,<0.7`. Core v0.6 is
distributed as an authenticated GitHub Release wheel rather than through PyPI.
Download `pds_core-0.6.0-py3-none-any.whl` and `SHA256SUMS.txt` from the
[pds-core v0.6.0 release](https://github.com/Paper-Data-Suite/pds-core/releases/tag/v0.6.0),
verify the wheel, and install it before installing Concord from source:

```powershell
python scripts/verify_core_wheel.py path\to\pds_core-0.6.0-py3-none-any.whl
python -m pip install path\to\pds_core-0.6.0-py3-none-any.whl
python -m pip install -e ".[dev]"
```

## Teacher menu

Bare Concord launches the teacher-facing workflow:

```text
concord
concord menu
```

The main menu provides Activity Management, Activity opening, Workspace
Settings, contextual Help, and Quit. Controlled teacher screens use:

```text
H. Help
B. Back
M. Main Menu
Q. Quit
```

Every menu write shows a focused review screen and requires the operation word
`CREATE`, `UPDATE`, `ADD`, `END`, or `REASSIGN`. The menu clears between stages,
paginates long selections after ten items, and does not display raw record
bodies or complete graphs.

## Direct CLI

Direct commands are deterministic and fully noninteractive. They never clear
the screen, pause, or call `input()`.

```text
concord workspace show|set|validate|reset
concord activity create|list|show|update|set-status
concord session add|list|show|update|set-status
concord group create|list|show|update|set-status
concord group member add|list|end|reassign
concord role assign|list|end|reassign
concord responsibility assign|list|end|reassign
```

Mutating direct commands require explicit actor context. Every write after the
initial Activity-plus-first-Session creation also requires the exact current
snapshot revision. `group member add` accepts repeated `--student-id` values and
commits the selected Memberships atomically.

See the [CLI contract](docs/cli-contract.md) for command behavior, exit codes,
workspace rules, and concurrency semantics.

## Workspace and identity

Core owns workspace resolution, saved workspace configuration, class metadata,
rosters, student identity, standards libraries, and shared B/M/Q navigation.
Concord uses those public APIs rather than copying their storage or parsing
rules.

Mutating Concord workflows initialize an absent resolved workspace through Core.
Read-only operations and help do not. Core resolution priority remains:

1. explicit runtime root;
2. `PDS_WORKSPACE_ROOT`;
3. saved Core configuration;
4. Core default.

Activity creation requires an existing Core class with valid class metadata.
Membership creation uses the Core class roster; a Concord Group is never a
student identity.

## Collaboration workflow semantics

Activity creation commits exactly one Activity and its required first Session
in one guarded batch. Later Activity, Session, Group, Membership, Role, and
Responsibility changes use the exact current snapshot revision. Exact no-ops do
not create new snapshots.

Membership, Role, and Responsibility reassignment preserves the predecessor and
creates an explicit successor. Storage revision and domain supersession remain
separate concepts. Membership does not establish authorship or contribution;
Role does not prove fulfillment; Responsibility does not prove performance.

Standards-based and mixed Activities require a Core standards profile and one or
more ordered Focus Standards validated through the Core standards contract.
Evidence-only and local-criteria-only Activities do not require standards
configuration.

Detailed behavior is documented in the
[workflow implementation guide](docs/implementation/activity-session-group-workflows.md).
Canonical persistence and recovery rules remain documented in the
[canonical storage guide](docs/implementation/canonical-storage.md).

## Validation

Run focused checks with `python -m pytest`, `python -m ruff check .`, and
`python -m mypy`. Run the complete repository validation on Windows with:

```powershell
.\run_tests.ps1 -CoreWheel path\to\pds_core-0.6.0-py3-none-any.whl
```

The cross-platform equivalent is:

```text
python scripts/validate_repository.py --core-wheel <wheel>
```

The validator authenticates the exact Core v0.6.0 wheel, runs pytest, Ruff,
strict Mypy, documentation checks, package builds, Twine validation, package
inspection, isolated installed-wheel workflow/menu smoke tests, and
`git diff --check`.

Core exposes routing through `paper_data_suite.modules` and publication through
`paper_data_suite.publication_producers`. These remain independent integration
surfaces, and Concord currently declares neither entry point.

The implementation sequence is tracked by
[umbrella issue #22](https://github.com/Paper-Data-Suite/pds-concord/issues/22).
See the [documentation index](docs/README.md), the
[accepted ADR index](docs/decisions/README.md), and the
[foundation review](docs/design/foundation-review.md) for governing design.

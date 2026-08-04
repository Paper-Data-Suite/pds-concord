# pds-concord

Concord is the Paper Data Suite module for paper-first, human-reviewed evidence
created during collaborative classroom Activities. The repository has moved from
architecture into v0.2.0 implementation. The installable Core 0.6 package
baseline and the immutable native record, exact conversion, and pure validation
layer are complete.

The available models do not make the complete Activity workflow operational.
Storage and teacher workflows remain pending. Concord does not yet handle
returned Artifact Pages, calculate Grades, publish result manifests, or expose
either a routing profile or a publication-producer profile.

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

## Commands and validation

The initial CLI is deliberately read-only:

```text
concord --help
concord --version
python -m concord --help
```

Run focused checks with `python -m pytest`, `ruff check .`, and
`python -m mypy`. Run the reusable repository validation on Windows with:

```powershell
.\run_tests.ps1 -CoreWheel path\to\pds_core-0.6.0-py3-none-any.whl
```

The cross-platform equivalent is
`python scripts/validate_repository.py --core-wheel <wheel>`.

## Integration boundaries and status

Native model imports are documented in
[the implementation guide](docs/implementation/native-record-models.md).
Record bodies can be converted without filesystem access, and relationship
validation is deterministic and side-effect free.

Core exposes routing through `paper_data_suite.modules` and publication through
`paper_data_suite.publication_producers`. These are independent surfaces: a
routing profile does not make Concord a publication producer, and a publication
profile does not make Concord routable. This baseline intentionally declares
neither entry point. Routing is assigned to issue #27 and publication to #31,
after their required behavior and validators exist.

The implementation sequence is tracked by
[umbrella issue #22](https://github.com/Paper-Data-Suite/pds-concord/issues/22).
See the [documentation index](docs/README.md), the
[accepted ADR index](docs/decisions/README.md), and the
[foundation review](docs/design/foundation-review.md) for the governing design.


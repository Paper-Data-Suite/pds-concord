# Concord v0.3.0 release checklist

The qualification Core artifact is:

```text
pds_core-0.6.3-py3-none-any.whl
SHA-256:
98d7596ce0eed26e4d56a17bbbbd644db3014259b56a45783a173fe8237af5e5
```

No phase publishes to PyPI or another package index.

## Phase A — release-preparation branch and PR

- [x] start from reconciled post-#70 / post-#98 `main` at
      `33bd916978da21f4a317a1509adc77981a25aa26`
- [x] authenticate the exact released Core 0.6.3 wheel
- [x] record the clean pre-edit authoritative baseline validator PASS
- [x] audit all 15 ADRs
- [x] audit architecture, grouping-signal privacy, reusable/instance boundaries,
      teacher usability, and installed/suite interoperability
- [x] inherit issue #70 physical acceptance without a redundant #71 physical run
- [x] harden release validators for module operations and the exact direct runtime
      dependency set
- [x] promote source and active qualification surfaces from `0.3.0.dev0` to
      `0.3.0`
- [x] roll the changelog and add `RELEASE_NOTES_v0.3.0.md`
- [x] focused issue #71 release-preparation tests pass
- [x] authoritative validator passes with `--allow-dirty`
- [x] physical qualification delta audit confirms no behavior-changing change to
      the #70-qualified print/PDS2/scan/Artifact/Review/Score/publication path
- [ ] complete release-preparation diff receives independent review
- [ ] hosted Ubuntu/Windows, Python 3.11–3.14 CI passes
- [ ] release-preparation PR is squash-merged

Tagging, final artifact hashes, GitHub Release publication, and fresh-download
verification cannot be completed on the release-preparation branch.

## Phase B — post-merge exact-main qualification

- [ ] reconcile local `main` and require `main == origin/main`
- [ ] require a clean tree and record the exact merged commit
- [ ] rerun the authoritative validator without `--allow-dirty`
- [ ] build exactly `pds_concord-0.3.0-py3-none-any.whl` and
      `pds_concord-0.3.0.tar.gz` from that commit
- [ ] pass Twine, ordinary wheel validation, release artifact validation, release
      compatibility, installed base smoke, installed shared-feature/starter
      smoke, and installed module-operations smoke
- [ ] confirm the exact wheel resolves Concord/Core from isolated `site-packages`
      with `pip check` clean and no sibling PDS distribution required
- [ ] complete the final physical-delta review against issue #70
- [ ] compute `SHA256SUMS.txt` from these exact final artifacts
- [ ] independently review the commit, filenames, byte lengths, and hashes

Expected final assets:

```text
pds_concord-0.3.0-py3-none-any.whl
pds_concord-0.3.0.tar.gz
SHA256SUMS.txt
```

## Phase C — tag and GitHub Release publication

- [ ] create tag `v0.3.0` at the exact qualified commit
- [ ] push the tag without rewriting an existing tag
- [ ] create the GitHub Release from `v0.3.0` using
      `RELEASE_NOTES_v0.3.0.md`
- [ ] upload the exact wheel, sdist, and `SHA256SUMS.txt`
- [ ] verify uploaded asset byte lengths and SHA-256 values match Phase B
- [ ] do not publish to a package index

## Phase D — post-release fresh-download verification

- [ ] download Core 0.6.3 and Concord 0.3.0 assets into a fresh external directory
- [ ] authenticate both wheels and the published Concord checksum file
- [ ] install noneditably into a fresh virtual environment outside the checkout
- [ ] run `pip check`
- [ ] verify installed metadata, version, and `concord --version`
- [ ] verify Core discovery of Concord routing-module, publication-producer, and
      module-operations providers
- [ ] rerun bounded installed base and representative starter-workflow acceptance
- [ ] rerun installed readiness/attention/module-operations acceptance
- [ ] record issue #70 physical qualification as inherited PASS; do not perform a
      new physical print/mark/scan run for issue #71
- [ ] record final artifact names, byte lengths, hashes, release URL/status, and
      fresh-download PASS in issue #71
- [ ] only then close issue #71, umbrella #47, and the v0.3.0 milestone

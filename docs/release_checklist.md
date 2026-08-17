# Concord v0.2.0 release checklist

The qualification Core artifact is
`pds_core-0.6.0-py3-none-any.whl`, SHA-256
`be28c061b38463ef59ebc328ed1aa443767fe7f2c626babb769c2d8e5932f308`.
No phase publishes to PyPI or another package index.

## Phase A — release-preparation branch and PR

- [x] start from reconciled post-#33 `main`
- [x] authenticate the exact Core 0.6.0 wheel
- [x] record the clean pre-edit authoritative baseline
- [x] audit all 15 ADRs and the #22 exit conditions
- [x] freeze consumer-facing contracts and promote source version to `0.2.0`
- [x] add compatibility and exact wheel+sdist release validators
- [ ] focused issue #34 tests pass
- [ ] authoritative validator passes with `--allow-dirty`
- [ ] release-preparation diff receives independent review
- [ ] hosted Ubuntu/Windows, Python 3.11–3.14 CI passes
- [ ] PR is squash-merged

Tagging, release publication, authoritative hashes, and download verification
cannot be completed on the release-preparation branch.

## Phase B — post-merge exact-main qualification

- [ ] reconcile local `main` and require `main == origin/main`
- [ ] require a clean tree and record the exact merged commit
- [ ] rerun the authoritative validator without `--allow-dirty`
- [ ] build exactly `pds_concord-0.2.0-py3-none-any.whl` and
  `pds_concord-0.2.0.tar.gz` from that commit
- [ ] pass Twine, ordinary wheel validation, release artifact validation,
  installed smoke, and #33 producer acceptance
- [ ] compute `SHA256SUMS.txt` from these exact final artifacts
- [ ] independently review the commit, filenames, and hashes

Expected final assets are:

```text
pds_concord-0.2.0-py3-none-any.whl
pds_concord-0.2.0.tar.gz
SHA256SUMS.txt
```

## Phase C — tag and GitHub Release publication

- [ ] create annotated or accepted project tag `v0.2.0` at the exact qualified commit
- [ ] push the tag without rewriting an existing tag
- [ ] create the GitHub Release from `v0.2.0` using `RELEASE_NOTES_v0.2.0.md`
- [ ] upload the exact wheel, sdist, and `SHA256SUMS.txt`
- [ ] verify uploaded asset hashes match Phase B
- [ ] do not publish to a package index

## Phase D — post-release fresh-download verification

- [ ] download Core 0.6.0 and Concord 0.2.0 assets into a fresh directory
- [ ] authenticate both wheels and the published Concord checksum file
- [ ] install noneditably into a fresh virtual environment outside the checkout
- [ ] run `pip check`, installed metadata/version/CLI checks, routing and
  publication discovery, public reader import, and Artifact-boundary import
- [ ] rerun the bounded installed smoke and #33 lifecycle when practical
- [ ] record Meridian #23 handoff identities
- [ ] only then close issue #34, umbrella #22, and the milestone

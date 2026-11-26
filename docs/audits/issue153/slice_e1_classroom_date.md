# #153 E1 — classroom generation date versus recorded instant

D3b3 qualified at `731470c67d69cf50f97b01e42a25f758b7e36c92` after exact
tree reconciliation; all 18 behavior tests passed before formatting-only
reconciliation and the six-file final Ruff check passed unchanged.

## Source trace and defect classification

- `prepare_packet_instantiation` calls `_generation_date` before building
  the reviewed target plan. Previously its default clock took the date
  directly from UTC, so October 19, 2026 at 21:00 EDT (October 20 01:00 UTC)
  produced October 20 as the planned date. This is a source-verified
  reproduction condition, not proof of the original historical user's
  specific run.
- The date participates in the review digest and the system rendering
  input `current_date`. Commit revalidates against the exact reviewed date
  using a synthetic explicit clock, then persists it in Packet records
  and their rendering values. Rendering consumes those stored values;
  it must not calculate a new date.
- `workflow_timestamp` defaults to an aware UTC instant for provenance.
  History projects the persisted generation date separately from creation
  timestamps, which are displayed in host-local time. Output filenames
  are generated from durable identities, not the calendar date.
- No explicit classroom date option exists in the current generation
  request. No new request field, CLI flag, date parser or persisted schema
  is introduced.

## Repair

Convert the default UTC clock instant to the host's local timezone before
extracting its calendar date. Explicit aware clocks retain their supplied
date, including commit's existing reviewed-date revalidation. The default
date changes for new preparations through both menu and direct CLI/API;
explicit ISO serialization, command grammar and recorded provenance are
unchanged. Host timezone is authoritative for this implicit default;
a misconfigured host timezone is not inferred or corrected by Concord.

15 added cases in the existing native Packet commit regression module:
eight host-local instant cases, three explicit aware clock cases, two
rejected invalid clocks, one historical date-only presentation case,
and one real synthetic workspace preparation/commit across midnight.
The DST cases use the known New York offsets at the exact specified
instants; these test application conversion behavior rather than validating
an OS/IANA timezone rule database. No new timezone data dependency.
The integration witness checks the persisted date, digest, template
current_date values, and independent UTC provenance.

No historical record migration, new Core capability, dependency change,
or release. Local qualification pending. E2 technical-detail disclosure
remains separate; B/F still require the released Core contract.

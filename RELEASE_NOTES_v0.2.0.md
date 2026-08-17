# pds-concord 0.2.0

Concord 0.2.0 delivers the first executable teacher-local collaborative
Activity vertical slice on the released PDS Core 0.6 baseline.

The release includes:

- Activity and explicit Session workflows;
- contextual Group, Membership, Role, and Responsibility history;
- PDS2 non-student and multi-subject page routing;
- returned Artifact assembly from exact retained-source lineage;
- independent Artifact Author and Subject attribution;
- explicit human Review and evidence Moderation;
- teacher-controlled Criterion Sets, native Scoring Scales, criterion Scores,
  non-score dispositions, evidence links, and Score revision history;
- Core Academic Work Registration for collaborative Activities;
- immutable, versioned Academic Result Manifest publication through Core,
  including supersession, withdrawal, catalog reconciliation, and audit;
- a consumer-neutral public manifest reader;
- a separate authorization-gated historical Artifact reader; and
- clean-wheel installed producer acceptance through the complete two-revision
  lifecycle against authenticated `pds-core 0.6.0`.

The frozen consumer handoff is intended for Meridian issue #23. Concord retains
producer-native Group/student targets, local/standard-backed Scores, native
Scale values, non-score states, Score history, and Moderation meaning; it does
not calculate Grade or proficiency and does not choose consumer-preferred
Scores.

Group Planning (manual, random, similar-signal, and mixed-signal), Core
`grouping_signal_set_v1`, Meridian grouping-signal export, Template and Packet
Definitions/composition, a starter handout library, and broader packet-oriented
teacher UI remain explicit v0.3.0 work.

Distribution is through verified GitHub Release wheel/sdist assets rather than
PyPI or another package index. Release-asset SHA-256 values are recorded from
the exact qualified release commit and published alongside those assets.

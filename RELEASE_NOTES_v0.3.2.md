# Concord v0.3.2

The release preserves the existing concord_academic_result_reader_v1 reader contract and concord_academic_result_manifest_v1 manifest contract without changing their semantics.

Concord v0.3.2 is a minimal dependency compatibility patch for Paper Data Suite Issue #132.

## Changes

- Requires `zxing-cpp>=3.1.1,<4`, instead of `zxing-cpp>=2.3,<3`.
- Preserves `pds-core>=0.6.5,<0.7` and all existing Concord academic-result producer/reader contracts, workspace state, and PDS2 routing policies.
- Verifies that Concord's real ZXing-C++ `read_barcodes(image)` decoder still reads QR images and multi-page PDFs, and that Concord can share a Python environment with ScoreForm v0.13.0's optional ZXing-C++ QR recovery.

## Compatibility

Use Core 0.6.5 and ZXing-C++ 3.1.1 (or a separately qualified compatible 3.x version). ScoreForm v0.13.0 is the cross-module comparison target. The installed composition test authenticates the exact candidate/final wheels and exercises both modules' actual decoders, without accessing student data.

No native workspace migration or public-reader-contract version bump is required.

Physical print/scan qualification is **not claimed** by automated tests.

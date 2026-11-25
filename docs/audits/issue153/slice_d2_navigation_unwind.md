# #153 Slice D2 — preserve navigation at action boundaries

D1 qualified on Windows at `c908671cdbe39ce3b32f6266ca1ae11de90bce7c`:
18 passed in 1.32 s; all static and integrity gates passed, including
the outstanding C1/C2 formatting corrections.

Core 0.6.6's ReturnToMainMenu and QuitPDS inherit Exception. Nine local
Activity and Packet handlers catch Exception after CancelMenuAction,
therefore swallow M/Q issued within nested selections or reviews.
D2 explicitly re-raises the two published Core navigation exceptions
before ordinary domain/storage error handling. Back remains a local
cancellation; actual operational errors still use existing receipts.

Scope: create/copy/edit Activity; generate/open/inspect/render/reprint/
resume Packet actions. No new confirmation, removal of approval tokens,
change to actor authorization, read/write services or Core capability.
The new 30 controller cases use real published navigation parsing in
synthetic nested selection/confirmation fixtures and reject any write,
viewer launch or erroneous receipt. They do not claim full end-to-end
storage acceptance. Other controllers remain subject to targeted audit;
no suite-wide unwind claim. A separate prompt consolidation is justified
only by demonstrated redundant teacher decisions, not multiple internal
preparation or currentness checks.

Local qualification pending. Next: audit remaining affected action
boundaries and preserve existing actor/Score review regression witnesses;
then classroom date and technical detail work. B/F remain Core #244
release dependent.

# Independent current-P1 consumer repair plan review v1

Disposition: CHANGES REQUIRED before implementation, limited to the two changes below. The native-consumer design and five-gap allocation are otherwise approved at metadata level. This is an independent review by /root/bac_astra_p2_custody_plan_review, not root adoption, source review, runtime verification or hardware qualification.

Reviewed subject: CUDA-HARDWARE-P2-CURRENT-P1-CONSUMER-REPAIR-PLAN-v1.md, SHA256 f2e6cb835ac86853cef35e63ffda5b8c1104805aa12232972bebcf05c77cc507 (16442 bytes). The plan freeze, gaps capsule dcc5441374e936c996b6859c099398d20f9277677f27acc868e5e7306f559804 and producer capsule b79532047f10410aeb7c5c2fe6a6f60ae473d84239d225cd59061e2561b94c96 were read and their exact bytes hashed. Source-body reads: zero. The runner pin 0d2a163305efb4683b8d90f42364d894a1af962129b9df15137ccd466374cc97 is a reviewed metadata assertion, not independently rehashed source in this review.

## What is already sufficient

All five recorded gaps have finite owners: native discovery and source siblings in Task2; explicit Git authority and retained joins in Task3; capture adoption and terminal reference types in Task1. The plan preserves the native thirteen-key versus NVIDIA nine-key distinction, optional topology failure, exact version LF behavior, native parent identities, ordered three-query P1 source observations, separate P2 unstaged guard, and P3's independently adopted two-query transport. Recursive exact primitive checks, duplicate-key/nonfinite rejection, terminal refusal gates and clock regression refusal are appropriate. No compatibility adapter, default Git path, historical capture acceptance or removal of existing capabilities is needed.

Externally pinning a root manifest is justified. Neither the current spec/admission graph nor terminal result hashes the five source siblings; result.json itself lacks an incoming authenticated edge. A first-read P2 snapshot cannot establish their history. Root's externally supplied exact manifest reference closes the byte graph when coupled with genuine custody. The authority label, matching hashes, directory permissions, lock file or successful JSON validation alone cannot establish that custody.

The source-only/test-only reslice is appropriate, provided root grants genuinely separate contexts and counts whole bodies without resetting a context's accumulated reads. Preserve the current runner during independent P4 work; only root's subsequent release permits the coordinated runner/caller/pin change. No new production helper or P0/P1 wire change is required by this review.

## Change 1 — Freeze the two missing root record contracts and their assurance boundary

The plan correctly identifies this as unresolved, so it is not implementation-ready. Adopt the following finite proposal or an equivalently explicit existing pair. These are proposed schemas, not records of past events. Exact field sets are closed; no implicit defaults, extra keys, duplicate keys, bool-as-int, nonfinite constants or nullable success fields. Ref means current strict P0 {path,sha256,bytes}; identity means current closed P0 process identity; UTC means the producer capsule's YYYY-MM-DDTHH:MM:SS.ffffffZ; absolute paths must be canonical. Each evidence list below is nonempty, ordered, unique exact references to retained actual controller/tool observations. Consumers check the references; root must inspect their actual provenance and substance before independently pinning the manifest. These raw observations are not a third machine-parsed authority schema.

### Proposed publication record

Exact keys for `bac-root-p1-producer-wait-v1`:

- schema: that literal.
- capture_directory: D.
- capture_tool: adopted P1 reference.
- request: exact P1 request reference.
- capture_identity: actual producer identity, matching manifest and discovery wrapper.capture_identity.
- controller_identity: actual process identity of the controller that spawned and waited for this producer; not the assistant's textual name.
- argv: complete actual producer argv, list of strings.
- cwd: actual canonical producer working directory.
- launched_at: UTC observation immediately before the actual launch.
- identity_observed_at: UTC when the actual live producer identity was collected.
- wait_observed_at: UTC when that controller's actual child wait completed.
- wait_method: literal `direct-child-wait`.
- exit_code: exact integer 0 for this success-only authority record.
- terminal: exact D/result.json reference.
- terminal_observed_at: UTC when terminal bytes were read after successful wait under continued custody.
- evidence: nonempty exact references to actual launch/identity/wait/terminal observation records or tool outputs.

Required observations and joins: the controller really owns and waits for this child; producer.ppid equals controller.pid, same host/boot, distinct live identities; live birth token is observed before termination and then retained. `launched_at <= identity_observed_at <= wait_observed_at <= terminal_observed_at <= manifest.sealed_at`; launched_at <= start.at and admission.at <= wait_observed_at. Actual terminal publication must precede successful wait; the terminal read timestamp is only an observation after wait, not an invented publication instant. The exact observed argv/cwd must identify the adopted capture invocation and request, including the actual D selector, using a root-approved invocation description frozen before actual launch. No guessed CLI or later PID reconstruction is permitted. P2 can check the closed record, typed identities, refs and temporal joins; root authenticates that the observations genuinely came from its controller. A shell/session tool's eventual exit status alone is insufficient when it cannot bind the capture child identity. A direct parent controller can collect these facts under future authorized execution without adding a production module or changing P1. If actual orchestration cannot observe them, keep capture UNRUN/refused rather than fill placeholders or accept an alternative wait mode silently.

### Proposed namespace lease record

Exact keys for `bac-root-p1-capture-namespace-lease-v1`:

- schema: that literal.
- authorization: exact reference to root's independently approved pre-creation execution/ownership grant.
- capture_directory: D.
- source_authorization: exact reference to the already required source no-writer grant; capture custody does not replace source custody.
- request: exact request reference, authorizing the only producer.
- owner: literal `root` (or freeze one actual root-owner identifier before implementation; no unchecked free-text identity).
- mechanism: literal `root-orchestration-sole-writer` for the current proposed mode.
- start, end: UTC authorized lease bounds, start < end.
- created_at: UTC actual exclusive creation observation, within the lease.
- directory_identity: closed {device,inode}, both exact nonnegative integers observed from the newly created directory.
- authorized_writers: literal ordered list [`p1-producer-until-wait`]; root/consumer/P4 may read the capture directory, while custody records are written outside D.
- evidence: nonempty exact references to retained creation/ownership/scheduling observations.

Required actual observations: root authorizes this exact unused D and interval before creation; creates it exclusively with no-follow ancestor checks; observes directory identity; controls all participating writer assignments; permits only the request-bound P1 producer to write D before its successful wait; grants no writer after wait through final P4 completion; records unexpected writers or custody loss as refusal. Identity must be rechecked at consumer boundaries and final P4 alongside no-symlink checks. Root retains the directory and does not release/reuse it before final P4 completion and cleanup. `lease.start <= created_at <= publication.launched_at <= ... <= manifest.sealed_at <= lease.end`; creation may precede launch but must occur in the producer's actual supported orchestration (if producer itself exclusively creates D, record that actual creation rather than precreating D incompatibly). All capture times and actual consumer/P4 boundary checks must lie within the lease.

Crucial assurance distinction: this mechanism is human/root orchestration authority over cooperating writers. The existing sole-writer scheduling ownership makes it actionable; it is not kernel-enforced exclusion of arbitrary same-UID or privileged writers, nor machine-proven continuous custody. Do not describe it as such. Root must explicitly accept this assurance model in the external grant and maintain it in actual scheduling. If the requirement instead means protection against arbitrary writers, the present mechanism is insufficient and real capture remains blocked until a real supported isolation mechanism is observed. Do not invent chmod/flock protection or an OS-isolated server that does not exist. There is no silent fallback between these models.

The lease end is a deadline/commitment, not evidence that future custody has already occurred. A manifest sealed before consumption must not assert that the entire future interval has been observed. Final P4 reports the actual completed interval and root closes the lease afterward. No circular references are needed: pre-creation external grant -> lease; publication -> observed producer/terminal; manifest -> lease/publication/inputs. The external input independently pins the manifest after the actual wait and hash observations.

## Change 2 — Make retention and boundary enforcement explicit for the new graph

Add publication and namespace record references and their finite evidence/authorization closure to the retained immutable custody inventory available to final P4, not just the manifest and five siblings. Read and validate the two closed schemas once through their pinned refs; rehash their exact referenced bytes with the existing source boundary checks. Root's grant and raw observations retain their stated authority limits; do not claim their semantics are fully machine-validated. P4 receives the same external manifest pin and verifies the same graph, including terminal and five siblings, rather than an independently authored P2 receipt claim.

Recheck the current UTC deadline and directory identity at every existing source/launch/final boundary and final P4, not solely at initial admission. Root must schedule a window covering the authorized bounded execution and cleanup. Expiry or custody loss prevents further launch/acceptance; use the existing cleanup path and retain failure if it occurs during execution. A future interval cannot prove continuing ownership. No extra continuous supervisor feature is requested; the guarantee is existing boundary validation plus root's explicitly accepted orchestration assurance.

Finite extra cases: missing/misbound publication or lease; wrong child/controller identity or wait/terminal chronology; fabricated-success fixture labeled synthetic; changed publication/lease/evidence reference after admission; wrong D inode; lease expired at a later source/P4 boundary; unauthorized assurance mode. These fit the planned custody matrices; no broad new testing campaign is requested.

## Decision and limits

After these two contract clarifications, root can accept the design without another native parsing design cycle, allocate bounded author/test contexts and release the shared runner after current P4 verification. This review does not itself grant implementation, test collection, runtime, source mutation or Git actions. It requires no capability removal, compatibility behavior or extra production module.

Actual local capture remains blocked by namespace/full cgroup ancestry. The anticipated 16-worker CUDA server is not available. Pure fixtures prove parser/refusal behavior only. No actual publication/wait/lease record is produced by this review; no successful wait, continuous namespace custody, hardware observation, P4 rerun or full-chain qualification is claimed. Existing failed/unrun records and Task4 gates remain intact.

# V2 root handoff

Current review-ready proposal SHA256:
`45801f6d05a751b4fa7458278f2c781290c094eafa267a65479efb34d9c427c6`.
The former24e002 seal below is historical and preserved as PRE-FORWARDING-SNAPSHOT.

2026-11-14. Read `T18e-R0-PARENT-INTEGRATION-PROPOSAL-V2.md` as current
implementation proposal; V1/source suppliers remain preserved. No APP or
runtime baton exercised. Four retained bodies3924, all current seals unchanged.

New concrete facts:

- Ordinary CLI is UnifiedServer -> TrainingThread -> DemoRunner, concurrent
  with daemon inference sharing checkpoint directory. Shutdown-request flag is
  not completed cleanup; worker-set flag can cause stop() to skip joins.
- Token assembler's three buffers/type are registered but nonpersistent:
  Module.to includes them, state_dict does not. Forward context copies and
  lane-index sources must be inventoried; no conversion cache exists.
- seed_all directly mutates Python/NumPy/Torch globals without custody; no
  rollback or protected gap to later construction exists.
- Hosted nine POP diagnostics describe seven unique invocations on five lines;
  two additional source omissions in restore make nine source-level omissions.
- Current BANK no incoming lineage; runtime-lock -> BANK domain order is
  incompatible with naive domain-first parent integration. This is a prospective
  integration gap, not a demonstrated current standalone BANK healthy window.

First APP-C1 proposal is concrete runtime/BANK retained custody plus explicit
bind_operation(actual RNGOperation), ordinary domain-before-runtime entry, own
BANK completion receipt under held lock, and unchanged method reentry guards.
No core redesign or replay retention API needed. Existing cohort/restore modes
remain supported standalone; active-parent cohort capability is a later explicit
idle-registration packet. No generic recovery, feature removal or fallback.

Writer and independent reviewer budget: runtime<=1600 + BANK<=1750 + new
concrete scope helper<=300 + new focused test<=900 =4550/four. Do not add the
1468-line existing BANK suite body; use supplier fixture APIs and root execution.
V2 specifies nine causal producer acceptance groups, real component-controller
fixture flow and later ENV/constructor/POP/restore/recurrent/runner packets.

Immediate next action: independently review V2's proposed API/lifetime/order and
bounded split, incorporate pending exact BANK inventory/native supplier facts,
then root grants one APP writer. No repeat review of settled outcome attribution.

Historical pre-forwarding source-fact addendum: V2 was sealed at SHA256
`24e0027c778edf6dc88a429fd3129e94cbf38bdc04631071525a9778db99dc75`
and has been sent to `bac_astra_parent_c1_contract_review`. Its previous bytes
are preserved in the PRE-NATIVE-SNAPSHOT file at SHA256
`3139424328b4b5ab2c21d20df96c77e54665f88df326903588eccb76e6153cbf`.
Native final capsule `7cb54762da2ecffae75091d06725afac71d83097f615cd364fc79ed1f54f0ba9`
and BANK addendum `4e118f6b65bbfd4bdc9b877624d9ad5abbbeb607e97374a9776b9e33f11165e4`
resolve the pending C1 metadata questions. BANK can use its own preserved
`self._devices` tuple for equivalent declared-inventory invocation; no native
getter or hidden tuple access is required. Native own completion remains actual
and nondeferred; copied reward/stamp-property output does not justify blanket
native quarantine. Foreign-source/rejected-prefix CUDA completeness remains a
distinct producer obligation. No extra implementation body was read.

Local independent-review correction now incorporated: runtime-delegated BANK
entry requires a private single-use exact-method forwarding permit, consumed
before public BANK body/admission/callbacks. Guard remains across standalone
prepare's private admission phases/idle cohort gap; direct standalone install
uses the same forwarding seam. Direct BANK controllers remain supported outside
runtime delegation. Real report/commit callback attempts are tested standalone
and parent-bound; cadence uses genuine standalone restore, while bound restore
refuses before cadence. Ephemeral scope/permit identity stays outside restored
state, with weak-key lifetime discipline and no resurrection or latch healing.
Fixture API is pinned as T18e-R0-POP-FIXTURE-CURRENT-API.md SHA256
`41c31db60be7c2d0f7f65d581bbb3587ca5809a593d58ab967639e46c51cb5b8`.

# P4 current-owner budget boundary v1

Current independently useful delta is implemented and tested: current P0 pin,
raw-v2-only observations, exact Python assertions/optimization separate from
Torch anomaly, current raw source/mode/module/reference/observation types, and
truthful measured nonfork Python debug even when Torch is absent. Existing88
regressions remain;11 new cases yield99PASS on the exact current source. Ruff and
Black pass. This is UNQUALIFIED partial integration, not owner/P5 completion.

After normal Black140 formatting: P4source1205/tests1399/P0526/P5source1518 =4648.
Remaining current individual headroom is145 source lines and151 test lines.
No P5 literal import or dispatch has been added; child-role branch remains a
fail-closed unsupported boundary. Neither adopted readonly dependency changed.

Concrete remaining implementation bodies identified in authorized reads:
- Existing P4 processes() lines306–507 handles only controller/worker; it rejects
  child roles outright. Current-owner launch/claim, parent full-environment and
  nested owner context cannot be obtained by merely changing its role enum.
- P5's already reviewed pair_process() is142 lines (566–707), and timing() is110
  lines (994–1103). These locate the owner launch/claim/environment/role/resource/
  sampler/emission and complete-call/parent timing requirements which P4 must
  independently implement. P4 may reuse its existing source/process checks, but
  cannot call those P5 methods as a replacement for independent common custody.
- P4 also needs independent explicit completion closure, fixed schema-directed
  document materialization, finite inventory dispatch, canonical-versus-selected
  role handling and existing receipt wrapping. The P5 public pure API exposes no
  document collector. Its standalone uses internal Documents/Check/Reader, which
  are not the approved literal P4 integration API. Using those internals as the
  P4 acceptance gate would remove the required independence.

The remaining145 normal source lines do not accommodate these independently
required checks plus document/receipt integration without omissions, delegation
of common acceptance, or large compressed lines. Per root's writer grant, pause
before adding that code and request a bounded reslice. No checks/tests were
removed, no new helper/interface was invented, and no cap has been exceeded.

A potential narrowly bounded next grant is to reallocate the same four-body cap
(e.g. source1600/tests1300 + readonly526/1518 =4944), if root explicitly permits
moving only bulky inert fixture declarations to hash-bound JSON fixture data
while preserving every test function/assertion and all existing behavior. The
current test Evidence constructor occupies633 lines; such fixture-data extraction
would not import P5 tests, create another executable helper, or move production
capabilities. This is a reslice option for root review, not an action taken or a
claim it already fits. Otherwise root must choose another bounded packet split;
this author will not silently widen the four-body envelope or merge capabilities.

Exact current source/status checkpoint is checkpoint-unqualified-v1.json.
All RED/GREEN attempts, actual command/PID/UTC/exit/resources and inert fixtures are
retained below current-owner-integration. Test runs were capped to one affinity
CPU and4GiB address space; no APP/Torch/CUDA/Git runtime or extra agents ran.

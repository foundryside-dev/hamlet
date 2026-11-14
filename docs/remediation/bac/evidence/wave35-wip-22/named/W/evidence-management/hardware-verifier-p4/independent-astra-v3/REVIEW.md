# Independent P4 frozen-v3 review

Disposition: **no remaining blocker found in the bounded common-verifier candidate; eligible for root adoption review within this scope only**. This is not adoption, full toolchain qualification or hardware evidence.

Exact candidate freeze SHA256 `32b0818346c54a35ce5471caad7fcb34ddd4b8331fe4aa566963e85ee3ee1bc1`; verifier `e72330bcffc2942a2d908a22b5e3471e702d744f54282314c6bccc4afc2c9d81`; tests `d9ee2216087d9906ac9e516d23f060c7d9e20c8213788b12328fc19a0e08f2f2`. Execution verifies freeze, all four source bodies, immutable author snapshots, current interface and every referenced interface metadata dependency. P0/historical wrapper remain unchanged. Review compared the complete source/test delta against the prior exact reviewed candidate and reassessed the retained bounded contracts.

## Evidence

The entire owned suite ran once on the actual frozen-v3 candidate: **88 passed**, exit0, PID197228, one process on CPU affinity `[3]`. The same process ran **24 independent synthetic probes**, with all expected dispositions. These overlap author regression purposes and are not summed into a unique test count.

The former external failed-down substitution now refuses with `replacement prior is not exact inventoried predecessor down`, for both fresh and reused gateway identities. A duplicate inventoried down refuses. Valid fresh-gateway and same-gateway replacement controls still satisfy common custody. Static review confirms prior_lifecycle is now equal to the exact unique inventoried down for predecessor_start, the already inventoried record supplies the failure evidence, and single consumption keys predecessor_start. Existing parent/role/worker/configure/absolute-time/monotonic checks remain intact. The last review blocker is resolved on these exact bytes.

Other retained probes confirm: parent and controller monotonic containment; one worker run/mainargv; refusal of duplicate initial gateways, unrelated gateway reuse and overlapping replacement; acceptance of child observations preceding the parent's post-Popen sample; exact ordered completion source-array copying; refusal of empty sources and missing raw provenance; and acceptance of the supplier-permitted minimal producer inventory plus an external reference while independently checking final filesystem inventory. The supplier distinction is preserved without inventing universal producer/final inventory equality or general transitive source closure.

Unknown validator IDs and substituted verifier pins refuse. Missing exact-job inventory stays unsatisfied. Missing process end stays completed-unverified/unsatisfied. Required P5 evidence cannot satisfy the conservative P0 aggregate; hardware remains unrun. Finite p4-common-v1 direct dispatch, accepted schema parsing, report/phase membership, source/provenance checks and conservative obligation gating remain in place.

## Retention and boundaries

`execution.json` records exact source hashes/snapshot references, probe hash, argv/PID/PPID, UTC start/end, affinity and exit0. `suite.json` and `suite.log` retain pytest invocation and result. `probes.json` retains every disposition and refusal traceback. `probe.py.txt` is the exact executed 117-line independent body. All suite/probe fixture directories remain present, including coherent mutated reference DAGs and rejected ancestry inputs. Earlier failed reviews and executed probe snapshots remain unchanged. The same logical probe body was updated in its existing location, not expanded into a sixth helper: **five bodies / 3,175 lines** conservatively counted. No APP/Torch/CUDA, actual producer toolchain, P0/P2/P3 changes, source-checkout/index/branch/worktree operations, inventory authoring or publication occurred.

Authority remains root's exact authorized spec invocation under source/namespace custody, not a hash or authority string. Root must adopt reviewed exact bytes before authoring a concrete inventory, then pin that inventory in the exact job prerequisites. Synthetic inventory fixtures supply no adoption.

P3's new raw/owner amendments remain separately under design/review and are not accepted by this review. P5 strict-child/producer/RNG/fork/phase semantics, six CUDA groups, APP validators, full producer integration, source-qualified owners and actual hardware remain pending/unrun. General producer inventory/source closure remains an explicit supplier-policy limit. No required missing obligation can be called satisfied. Any integration or source change needs its own bounded qualification.

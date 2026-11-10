# Current RP compatibility name inventory

At clean source checkpoint c1de41509ae108848fd5bf295487510254daab6b, root ran `rg -n 'is_legacy_policy_payload|legacy_shared_payload|LEGACY_POLICY_FIELDS' src tests --glob '*.py'`.

Only src/townlet/config/exploration_policy.py matches: constant definition35, predicate definition55/use57, from_dict predicate325 and fieldset331, projection definition336. There are no direct textual references to those named compatibility helpers outside RP in current src/tests. This is a search-derived name inventory, not proof of absence of dynamic use or of the semantics of external artifact consumers. It authorizes no compatibility adapter. Actual RP source and current policy schema decide the coherent direct replacement under the owner no-BC ruling. Historical artifact preservation/admission and the explicit shared alternative remain separate contracts.

No external implementation source is reproduced or implied reviewed here. Actual historical parent provider-subtree admission still needs its owning source/capsule; HC's payload transport must not be advertised as such a selector without evidence.

# Operational note for future finite checkpoints

The reviewed selector compares descendant lists in its actual recursive traversal order, not merely as sets. When preparing a future receipt, use the exact reviewed helper `descendants(qualification_root, top_entry)` result, or compare ordered output before freezing the subject. Do not invent a different global path ordering. In WIP15 the initial final selection stopped before output on this representation difference; all 68 normalized sets matched, 31 lists needed only order canonicalization. Exact history remains in `wip15-ordering-reconciliation.json`. No test/source/custody fact changed and no guard was weakened.

This is an operational invocation note for the reviewed tool, not a new application contract, source edit or acceptance exception.

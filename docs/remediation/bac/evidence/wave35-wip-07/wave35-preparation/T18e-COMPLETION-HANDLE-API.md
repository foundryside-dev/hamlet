# T18e completion preparation receipt accessor

Exact fact from already reviewed scoped_curiosity.py only; no additional source read, runtime check or source/index mutation.

`CuriosityBank.prepare_completion(*, accepted, boundary_key, completion_content, outcomes, participated_world_ids) -> PreparedBankCompletion` returns the actual preparation handle. Its public dataclass field is:

`prepared.prepared_receipt: WorldOwnerReceipt`

Thus the genuine receipt argument for the parent outline is `dispositions=prepared.prepared_receipt`. This is attribute access, not a getter/property method or a new API.

Ownership evidence: prepare_completion issues `self._issuer.issue(kind='prepared_dispositions', payload=payload)` and stores that same receipt in the returned PreparedBankCompletion.prepared_receipt field. The BANK issuer is constructed for the actual BANK and checks issuer.owner is self. The returned dataclass is mutable: use the untouched actual handle/receipt, not a fabricated, cloned or field-replaced token. ENV's actual owner/receipt validation remains authoritative; these BANK bodies alone do not prove every ENV acceptance rule.

`commit_completion(*, prepared: PreparedBankCompletion) -> WorldOwnerReceipt` is a later distinct operation returning the committed `dispositions` receipt. It is not the accessor for the earlier `prepared_dispositions` receipt required by ENV.prepare_episode_close. The genuine facade wrapper is outside the four inspected bodies; the fact applies when, as the parent reports, it returns the actual PreparedBankCompletion unchanged.

# MCP-safe scans

**Warning:** `strict_defaults` is **false by default**. It does not mean
"strictest gate." Setting it to `true` ignores the repository's entire
`weft.toml` Wardline configuration and uses built-in defaults. That discards
declared `source_roots`, exclusions, severity policy, and trust-grammar packs;
on a large checkout it can turn a bounded `src/` scan into a repository-wide
scan that also discovers duplicate code under nested `.worktrees/`. For a
trusted checkout, omit it (or pass `false`) so the declared project scope and
packs apply. Use `true` only when the operator deliberately rejects
repository-controlled policy, has verified that the resulting built-in scope
is acceptably bounded, and accepts that custom markers will not load.

For a large or unfamiliar project, use the asynchronous job surface instead of
holding a synchronous MCP call open:

```text
scan_job_start({
  "path": ".",
  "config": "weft.toml",
  "format": "agent-summary",
  "fail_on": "ERROR",
  "fail_on_unanalyzed": true,
  "local_only": true,
  "timeout_seconds": 1800
})
scan_job_status({"path": ".", "job_id": "<returned job_id>"})
```

Poll `scan_job_status` until it reports a terminal state; use
`scan_job_cancel` when the work is no longer wanted. `local_only: true`
disables sibling emission for a gate-only run. Omit it only when Filigree
emission is intentional. The job still writes its status and artifacts under
`.weft/wardline/jobs/`.

On synchronous `scan`, `summary_only` and `max_findings` bound the response;
they do **not** reduce discovery, analysis, cache work, or configured
Loomweave/Filigree writes. A client-side timeout does not prove the server-side
scan stopped, so do not immediately retry an ambiguous synchronous timeout.
Use the job surface to obtain progress, a terminal result, and cancellation.

Custom packs must be declared in `weft.toml`; `trust_packs` and
`trust_local_packs` authorize declared imports but do not declare or load a
pack by themselves. A Python pack exports its `TrustGrammar` as lowercase
`grammar`. Because `strict_defaults: true` ignores `weft.toml`, it also ignores
all declared packs.

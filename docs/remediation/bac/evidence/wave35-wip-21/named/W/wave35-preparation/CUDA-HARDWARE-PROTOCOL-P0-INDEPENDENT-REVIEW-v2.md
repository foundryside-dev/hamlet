# Independent Astra review — hardware protocol P0 v2

**PASS for the agreed finite P0 common transport scope**, 2026-11-14T05:48:16.553325+00:00. No remaining P1/P2 findings in this bounded review. This supersedes the blocking disposition of `CUDA-HARDWARE-PROTOCOL-P0-INDEPENDENT-REVIEW-v1.md`; its findings, failing test runs and setup failures remain preserved.

Reviewed frozen protocol SHA-256 `81b7e420987d1b8b0452c798445d7eb14f6157fd16e72961bf03f0479f1f9ea7` (467 lines), author tests `ee821e2347a6091acc658ca73b4ac01b652368cf227a8df33930290eab7a195b` (417 lines), and unchanged independent test file (124 lines). All three bodies total 1,008 lines; author pair 884/1,400. Freeze-v2 source, schema inventory and interface metadata lengths/hashes were independently verified against actual files.

All three original findings are resolved:

- Reference hashing rewalks the no-follow directory chain from root and checks directory device/inode identities before checking the leaf. The deterministic parent-replacement probe now rejects. This detects observed substitution; it does not defeat arbitrary subsequent or restored transient writes. The source-freeze/no-writer requirement remains explicit.
- Refused/unrun records now require null exit, zero signal, unavailable execution end/duration and no collected IDs, outcomes, process records or obligation records. Orchestration start and refusal diagnostics remain representable. Both relabel mutations reject; author's valid failure/interruption/nonexecution fixtures pass.
- Source-freeze records now reject measured end preceding start.

Independent execution against the frozen revised module: author's complete suite **89 passed**, exit 0 (`author-suite-v3`); unchanged independent adversarial suite **22 passed**, exit 0 (`independent-suite-v4`). Exact argv, cwd, explicit environment, UTC start/end and matching source-before/source-after hashes are in the corresponding JSON records below. The sets overlap in behavior; counts are not summed into an application coverage claim. All logs and fixture directories were exclusively created and retained. No application imports, hardware discovery or server action occurred.

This PASS covers exact bytes, closed transport schema, typed/local invariants, reference rejection behavior and explicit interface limitations. It does not qualify CUDA work, child/fork/phase contracts, resources, causal process observations, actual source freeze, or authenticated validator receipts. Downstream P1–P5 must enforce the sealed interface requirements, including owner-supplied exact case contracts and missing-validator unsatisfied/unrun behavior. No consumer may treat `validate_record` success as behavioral acceptance. Root owns adoption and any separately bounded consumer work; server/CUDA availability remains unverified.

Evidence resides in `evidence-management/hardware-protocol-p0/independent-review` unless noted as freeze/interface metadata:

- `author-suite-v3.json`: SHA-256 `5cf3e09838d6ff5bc547ae25fc1289e7694fbada2e4bd76c98896e91eb886cd6`.
- `author-suite-v3.log`: SHA-256 `365e69adc5dd53fdcff0d0e7ad51b592246546508f1593de62a21a43d2fdd8db`.
- `independent-suite-v4.json`: SHA-256 `99e56c4799e2581f7f81fde71aec366162f66a50b24490eac1be12893220c79d`.
- `independent-suite-v4.log`: SHA-256 `ec3622cd28ed58d936296959047810aafa476cb0738b1aa83ec2cccffc39214a`.
- `test_independent_p0.py`: SHA-256 `dc17ff2ac3ef7f21716eb78cc561c9c08fc771fe20c1b34f54d5aa467e718bf2`.
- `freeze-v2.json`: SHA-256 `32c8f8fd80b6b9407c87aac6da4d8e74e7da1ac4aaad557bce79d360e62c5bd7`.
- `interface-contract-v2.json`: SHA-256 `f20950a73809a5044278fca1575aa42764c62ac35797f1899dfc2f29aba56e6a`.

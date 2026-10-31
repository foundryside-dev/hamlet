# Security policy

## Supported versions

Townlet is pre-release. Only the latest commit on `main` receives fixes.

## Reporting a vulnerability

Please do not open a public issue. Email <john@foundryside.dev> with `[SECURITY]` in the
subject.

Include what an attacker could do, the affected files or components, and steps to reproduce.
This is a one-person project, so responses are best-effort; you should hear back within a week.
Once a fix is on `main` the issue will be disclosed in a GitHub security advisory, with credit
if you want it.

## Trust boundaries

Townlet is research software meant to run on your own machine. Keep these limits in mind:

- **Checkpoints.** Training resume and the live inference server load checkpoints with
  `weights_only=False`, because checkpoints carry curriculum and replay state as Python objects.
  Loading a checkpoint can therefore run arbitrary code. Each checkpoint has a `.sha256`
  sidecar, which detects corruption but is not a signature. Only load checkpoints you produced
  or fully trust.
- **Config packs.** YAML is parsed with PyYAML's safe loader and validated against strict schemas.
  A config pack can still make training consume a lot of memory or compute, so review packs from
  others before running them.
- **Network servers.** The training WebSocket server and the inference server listen on all
  interfaces (`0.0.0.0`) with no authentication or encryption. Run them on a trusted network or
  behind a firewall, and do not expose them to the internet.
- **Variable access policies.** `readable_by`, `writable_by` and `exposed_to` control what an
  agent can read and observe. They are not a confidentiality mechanism: rewards and other
  values derived from hidden state can still reveal it.

## Out of scope

- Resource exhaustion from training itself.
- Reward hacking and other "interesting failures" in learned behaviour. Those are research
  findings, not vulnerabilities; please open an ordinary issue.
- Vulnerabilities in dependencies. Report those upstream.

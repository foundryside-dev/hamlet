# Security Surface Map — Townlet (HAMLET)

**Date:** 2026-05-16
**Scope:** `src/townlet/`, `scripts/`, `deploy/`, `pyproject.toml`
**Method:** Source-derived; file:line citations throughout.
**Version under review:** `townlet` 0.1.0 (alpha, pre-release).

Companion to `01-discovery-findings.md` / `02-subsystem-catalog.md` §11.6
and the SG8 deep-dive (`temp/sg8-demo-recording-frontend.md`). Scoped to
**what attackers could realistically do today**, not a hypothetical
production deployment. Most headline issues are "would-be-critical if
exposed publicly, low-risk on localhost" — stated explicitly where so.

---

## 1. Threat Model — Scope and Posture

### 1.1 What this project actually is

Townlet is a single-tenant pedagogical Deep RL framework. It has:

- One inbound network surface (a FastAPI/uvicorn WebSocket on `:8766`).
- One systemd unit for long-running demo training
  (`deploy/townlet-demo.service`).
- No authentication anywhere — by design.
- No PII, no payment data, no user accounts, no upstream API consumers.
- One on-host SQLite database (`demo_state.db` / `metrics.db`),
  accessed only by the process that wrote it.

Version: 0.1.0 alpha, with classifier
`Development Status :: 3 - Alpha` (`pyproject.toml:30`).

### 1.2 In scope

- Demo FastAPI/uvicorn listener (`src/townlet/demo/live_inference.py:73`,
  `src/townlet/demo/unified_server.py:414`).
- Systemd unit + install script (`deploy/`).
- Universe Compiler YAML pipeline (`src/townlet/universe/{compiler.py,
  loaders/preflight.py, source_map.py, raw_configs_v21.py}`).
- World expression DSL (`src/townlet/world/expression/`).
- Checkpoint loading (`src/townlet/training/checkpoint_utils.py:199`).
- Recording (msgpack/LZ4) load path (`src/townlet/recording/`).
- `pyproject.toml` supply-chain shape.

### 1.3 Out of scope

- Multi-tenant operation, RBAC, identity, federation — none exist.
- Secret handling — no secrets handled.
- Network exposure beyond localhost — treated as a deployment
  misconfiguration, not a feature.
- Frontend XSS — the WebSocket is the same entry point an attacker
  already has; XSS is moot.
- Network-layer DDoS — out of scope at this project tier.

### 1.4 Assets

| Asset | Where | Confidentiality | Integrity | Availability |
|---|---|---|---|---|
| Training checkpoints (`checkpoint_ep*.pt`) | `<run_root>/checkpoints/` | Low | **High** (RCE risk if tampered) | Medium |
| Recorded episodes (`episode_*.msgpack.lz4`) | `<output_dir>/` | Low | Medium | Low |
| Config packs (YAML) | `configs/<level>/`, snapshot under run dir | Low | **High** (drives behaviour, hashed for provenance) | Low |
| SQLite metrics DB (`metrics.db`) | run dir | Low | Medium | Low |
| Q-value debug log (`qvalues_inference.log`) | **process CWD** (`live_inference.py:157`) | Low | Low | Low |
| TensorBoard logs / training.log | `<run_root>/` | Low | Low | Low |

### 1.5 Adversary model

Three realistic adversaries, descending plausibility:

1. **Benign operator mistake.** Pointing uvicorn at a non-localhost
   interface, running the unit on a multi-user box, log files in
   someone else's directory. Most likely failure mode.
2. **Tampered artifact (supply-chain or local).** A checkpoint or
   config pack from an untrusted source — GitHub fork, shared training
   cluster, a teacher distributing an "interesting failure" to
   students. Natural distribution mode for a pedagogical project.
3. **Hostile browser on the LAN.** Relevant only if the demo is
   exposed beyond localhost (`allow_origins=["*"]` +
   `host="0.0.0.0"`).

Out of scope: APT, host-level malware (if attacker has shell, the
threat model is moot), insider with DB credentials (none exist).

---

## 2. Inbound Surface Inventory

The **complete** set of listening sockets in `src/townlet/`:

| Surface | Bind | Auth | AuthZ | Input validation | Rate limit |
|---|---|---|---|---|---|
| FastAPI/uvicorn on `:8766` | `0.0.0.0` (`live_inference.py:1231`, `unified_server.py:416`) | None | None | Minimal (see §3.2) | None |

That is the entire inbound surface. There are no HTTP routes — only two
WebSocket routes, both mapped to the same handler:

| Method | Path | Handler | Source |
|---|---|---|---|
| WebSocket | `/ws` | `LiveInferenceServer.websocket_endpoint` | `live_inference.py:173` |
| WebSocket | `/ws/training` | `LiveInferenceServer.websocket_endpoint` (alias) | `live_inference.py:174` |

No `@app.get` / `@app.post` / `@app.put` decorators exist anywhere in
`live_inference.py`. The frontend's `checkServerAvailability` probes
`/ws` and `/ws/training` by opening short-lived sockets
(`frontend/src/stores/simulation.js:112-146`).

The TCP port for the **frontend dev server** (Vite, `:5173`,
`vite.config.js:5-11`) is a separate process, started by hand. It is not
part of the Python attack surface and is not addressed further here except
in §5.

CORS configuration (`live_inference.py:164-170`):

```python
self.app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

For a WebSocket-only app the CORS middleware's practical effect is
limited (the upgrade handshake doesn't preflight like HTTP fetch). But
the config covers any future HTTP route on the same app, and the
intent it signals is wrong for any non-loopback deployment.

### 2.1 Per-route command surface

After handshake (`live_inference.py:516-541`) the loop dispatches on
`command` / `type` (`:551-628`). All commands are unauthenticated and
unauthorised — any WS peer can issue any of them.

| Command | Params | Effect | Source |
|---|---|---|---|
| `play` | — | start inference / replay loop | `:566-575` |
| `pause` | — | stop loop | `:577-583` |
| `step` | — | run one step | `:585-591` |
| `reset` | — | reset episode counter / replay cursor | `:593-603` |
| `refresh_checkpoint` | — | rescan checkpoint dir, hot-load newest | `:605-612` |
| `toggle_auto_checkpoint` | — | flip auto-load mode | `:614-620` |
| `set_speed` | `speed: number` | set `step_delay = 0.2 / speed` | `:622-628` |
| `load_replay` | `episode_id: int` | switch to replay mode, load episode | `:556-557, :969-1015` |
| `list_recordings` | `filters: dict` | DB query, returns list | `:559-560, :1017-1046` |
| `replay_control` | `action, seek_step?` | replay play/pause/step/seek | `:562-563, :1048-1073` |

Validation summary:

- `set_speed`: no validation; `step_delay = 0.2 / speed` at `:627`.
  `speed=0` → `ZeroDivisionError` (caught at `:545-549`, drops the
  connection). `speed=-1` → negative delay (asyncio.sleep treats as 0 →
  CPU spin). `speed=1e-9` → 200000-second delay.
- `load_replay`: only checks `episode_id` non-None (`:976`). Passed as
  SQL bind parameter — SQLi-safe but no int type-check.
- `list_recordings`: `limit` from `filters` goes straight to SQL
  (`:1029`). A client can request `limit: 10_000_000_000`.
- `replay_control.seek_step`: bounds-checked in
  `ReplayManager.seek()` (`replay.py`).

No frame-size limit; uvicorn default (~16MB) applies.

---

## 3. STRIDE per Surface

### 3.1 Spoofing

**Threat:** Anyone connecting to `/ws` claims to be "the operator".

**Assessment.** True, but uninteresting for a pedagogical demo on
localhost. There is no notion of identity; the server treats every
WebSocket peer identically. The risk is only meaningful if the listener
escapes localhost. See §5 and §6.

**Severity (localhost-only deployment):** Low.
**Severity (if exposed):** High. Anyone on the LAN can `play`/`pause`,
swap checkpoints, drive the replay endpoint, and DoS the loop.

### 3.2 Tampering

**Inbound (over the WS):** the server accepts JSON frames; the dispatcher
trusts whatever string is in `command`. There is no schema validation
(no Pydantic model wrapping the WS message — only on the YAML loading
side). The handlers themselves are short and the field accesses are
defensive (`data.get(...)`), so the worst the WS can do directly is the
DoS surface in §3.5.

**Persisted state (the actual concern):** the server cold-loads the
*latest checkpoint* in the checkpoint directory on startup
(`live_inference.py:419-444`):

```python
checkpoints = sorted(self.checkpoint_dir.glob("checkpoint_ep*.pt"))
...
verify_checkpoint_digest(latest_checkpoint, required=True)
checkpoint = safe_torch_load(latest_checkpoint, weights_only=False)
```

Remediation update: the demo callsites now require the digest sidecar
before entering this `weights_only=False` load path. The digest file still
lives next to the checkpoint (`checkpoint_utils.py:150-167`); an attacker
who can write both the `.pt` and `.sha256` can still satisfy the check.
The digest defends against missing/corrupt sidecars and accidental
tampering, not adversarial tampering — there is no signature, no
out-of-band key, no trust anchor.

Combined with `weights_only=False` (see §4.1), an attacker who can write
both files to the checkpoint directory still wins.

**Severity:** Medium for the threat actor "I can drop a file on the
training host"; the project is not protecting against shell-level
attackers, so this collapses to the supply-chain case (untrusted
checkpoint distributed and loaded).

### 3.3 Repudiation

Reproducibility is the closest thing to non-repudiation. Checkpoints
embed `drive_hash` (DAC SHA256), `vfs_hash` (validated on resume —
`checkpoint_utils.py:127-147`), `brain_hash`
(`live_inference.py:364-366`). Config snapshot copied to
`<run_root>/config_snapshot/` on every run
(`unified_server.py:97-113`).

Adequate for *what produced this checkpoint?* (forensic attribution
against drift). Not a tamper-evident audit log: snapshot, hashes, and
checkpoint live in the same directory; an attacker who can write one
can write all three. No signing key, no external anchor. This project
is explicitly not in the `axiom-audit-pipelines` regime.

**Severity:** Low (no production audit obligation).

### 3.4 Information disclosure

Server hands out: substrate metadata, action labels
(`live_inference.py:520-535`); live Q-values per step (`:723-743`);
checkpoint filenames (`:528, :701`); recording metadata
(`:1031-1046`).

Not exposed: filesystem paths beyond `checkpoint_ep{N:05d}` filenames;
env vars; PII (none exists); stack traces (caught at `:545-549`, not
returned).

Two side channels:

1. `qvalues_inference.log` is CWD-relative (`live_inference.py:157`).
   Accumulates wherever the operator's CWD was. Content (RL Q-values)
   is not sensitive.
2. Config snapshot is copied wholesale into `<run_root>` every run
   (`unified_server.py:97-113`). If a future config pack ever contains
   secrets, they will be silently copied. Today no pack contains
   secrets — forward-looking concern.

**Severity:** Low.

### 3.5 Denial of Service

With no auth, no rate limit, a hostile WS peer can:

- Spam `play`/`pause` to thrash loop state.
- `set_speed` with tiny `speed` → multi-hour `asyncio.sleep`
  (`:627, :747`).
- `set_speed` with `0` → `ZeroDivisionError`, connection drops
  (self-limiting per connection).
- `set_speed` with `-1` → CPU pin for the inference-loop lifetime.
- `list_recordings` with `limit: 10_000_000` → large DB query + JSON
  response.
- Open many WebSockets — `self.clients` is unbounded (`:117`);
  broadcast loop (`:955-967`) detects/removes slow consumers but a
  flood at the front can starve normal clients.

Training-side defences exist (recorder queue
`maxsize=1000` with drop-on-overflow, `recorder.py:29,141`) but are
not network-side. The WebSocket itself is unbounded.

**Severity (localhost):** Low. **(If exposed):** Medium — easy to
disrupt, not destructive.

### 3.6 Elevation of privilege

The interesting boundary is systemd → application user, not user →
root.

Unit (`deploy/townlet-demo.service`): `Type=simple`, `User=%USER%`
substituted from installer's `$USER` (`install-service.sh:11`).
**No hardening directives** — no `NoNewPrivileges`, `ProtectSystem`,
`ProtectHome`, `PrivateTmp`, `RestrictAddressFamilies`, `SystemCallFilter`,
`MemoryMax`. `Restart=always` with 10s backoff.

Runs as a normal user; if the WS surface is RCE-able (it is via the
checkpoint path — §4.1), the attacker gets the operator's user
context. Not root, but everything that user reads — workstation:
home directory; shared box: SSH keys and other runs.

**Severity:** Medium for any non-trivial deployment.

---

## 4. Code-Execution Attack Surface

The places where attacker-controlled bytes can become Python code.

### 4.1 Checkpoint loading (`safe_torch_load` with `weights_only=False`)

`safe_torch_load` defaults to `weights_only=True`
(`checkpoint_utils.py:203`) — safe. **But every demo callsite passes
`weights_only=False`:**

| Callsite | File:Line |
|---|---|
| Inference hot-load | `live_inference.py:444` |
| Runner initial | `runner.py:185` |
| Runner latest | `runner.py:342` |

`weights_only=False` → `torch.load(..., weights_only=False)` →
**arbitrary pickle deserialization** — any gadget chain in the
checkpoint executes at load.

The function's own docstring acknowledges this
(`checkpoint_utils.py:215-216`):

> "For external/untrusted checkpoints, always use `weights_only=True`."

Demo callsites pass `weights_only=False` because the checkpoint stores
non-tensor state (curriculum, replay buffer, exploration —
`runner.save_checkpoint` at `runner.py:265`).

Combined with the now-required but same-directory digest check (§3.2):
**any attacker-supplied checkpoint plus matching digest dropped into the
watched directory is still RCE at load** under the systemd user. Missing
or corrupt digest sidecars are blocked before pickle load. This remains
the most consequential residual finding in the project until the
non-tensor state moves out of pickle or checkpoints are signed.

**Severity:** High in the "tampered artifact" model (realistic for a
pedagogical project where students swap checkpoints). Critical if
combined with public exposure.

Note: `cloudpickle` is declared in `pyproject.toml:58` but **not
imported anywhere in `src/townlet/`** (only `import pickle` for the
exception class, `checkpoint_utils.py:7`). `torch.load` uses `pickle`
directly. Removing the `cloudpickle` dep is safe.

### 4.2 YAML loading

All `yaml.load` sites in `src/townlet/` and `scripts/` use
`yaml.safe_load` — verified by `grep -rn 'yaml.load\|yaml\.safe_load'`
across `src/townlet/`, `scripts/`. Sites: `config/*_config.py`,
`config/{base.py:43, cues.py:120, training_v2_config.py:420}`,
`curriculum/adversarial.py:205`, `universe/compiler.py:564`,
`universe/raw_configs_v21.py:{163,176,189,242,250}`,
`universe/loaders/preflight.py:{84,130,140,160}`,
`environment/{action_config.py:121, action_builder.py:188}`,
`vfs/schema.py:547`, `scripts/{migrate_affordances_to_effects.py:88,
validate_compiler_cli.py:51}`.

One exception: `universe/source_map.py:97` uses
`yaml.load(handle, Loader=_LineNumberLoader)`. `_LineNumberLoader`
subclasses `yaml.SafeLoader` (`source_map.py:11`) with a custom mapping
constructor — **safe**, recognised idiom for line-number preservation.

**No unsafe YAML loaders.** Not an RCE vector. **Severity:**
Negligible.

### 4.3 World expression DSL

`world/expression/{parser,evaluator}.py` is a pyparsing grammar
producing an AST (`ast_nodes.py`) evaluated by an `ASTVisitor`. Grep
for `eval(`, `exec(`, `compile(` across `src/townlet/world/` returns
nothing — no Python-eval fallback. The evaluator dispatches over a
closed set of AST node types (Constant, Variable, BinaryOp, UnaryOp,
FunctionCall, IfThenElse, IndexAccess, PathAccess) into `torch` ops.

Closed grammar, no escape. Malicious configs can still craft
large-tensor or deep-recursion expressions → DoS-class, not RCE-class.

**Severity:** Low. Follow-up: bound expression depth and intermediate
tensor size if configs ever become operator-uploadable.

### 4.4 Other dangerous sinks

`grep -rn 'subprocess|shell=True|os.system' src/townlet/` returns:

| Site | What | Risk |
|---|---|---|
| `recording/video_export.py:137,173` | `ffmpeg` for video encoding | List-form argv (no shell). Input paths come from operator CLI or the DB. Low. |
| `demo/unified_server.py:460,469` | `npm` / `npm run dev` for frontend | Dead code (`_start_frontend` is not called from `start()`, per SG8 finding #4). Low. |
| `universe/compiler.py:702` | `git rev-parse HEAD` for provenance | Fixed argv, no input. Negligible. |

No `shell=True` anywhere. No `os.system`. No `eval`/`exec` of user input.

### 4.5 The migration script

`scripts/migrate_affordances_to_effects.py` is a one-shot YAML rewriter.
It uses `yaml.safe_load` (`:88`) and `yaml.dump` (`:97,100`). It can
clobber files in the operator's config directory, but it is invoked
explicitly and the input/output paths are controlled by the operator.

**Severity:** Negligible.

---

## 5. Deployment Posture

### 5.1 The systemd unit

`deploy/townlet-demo.service` is `Type=simple`, `User=%USER%`,
journal-logged, `Restart=always`/10s. **No hardening directives.**

Missing (each is one line):

- `NoNewPrivileges=yes`
- `PrivateTmp=yes`
- `ProtectSystem=strict` + `ReadWritePaths=` for the run dir
- `ProtectHome=read-only` (or tmpfs with explicit ReadWritePaths)
- `PrivateDevices=yes` (or `DeviceAllow=` for GPU)
- `RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6`
- `ProtectKernelTunables`, `ProtectKernelModules`,
  `ProtectControlGroups`
- `SystemCallFilter=@system-service` (test required — torch can be
  fussy)
- `MemoryMax=`, `TasksMax=`

Second issue: the unit invokes `python -m townlet.demo.runner` — the
**training-only** entry point. It does not spawn the WS server.
`scripts/run_demo.py` is what wires up `UnifiedServer` (which binds
`0.0.0.0:8766`). The unit and the documented demo workflow disagree.
If an operator switches the unit's `ExecStart` to `run_demo.py` for
the unified experience, they silently expose `0.0.0.0:8766` —
there is no CLI flag or env var to bind to `127.0.0.1` instead.

**Severity (current):** Low — no network port opened by the unit as
shipped. **(Likely future):** Medium — the moment the unit is
switched to the unified server, `0.0.0.0:8766` is exposed without
hardening.

### 5.2 The install script

`deploy/install-service.sh` substitutes vars via `sed
"s|%PLACEHOLDER%|$VAR|g"` (`:28-34`); writes
`/tmp/townlet-demo.service` (predictable, fixable with `mktemp`); copies
to `/etc/systemd/system/` via sudo. Substitution has no escaping —
breaks if `$VAR` contains `|`. Footgun, not a security finding. No
secrets in the unit file; world-readable tmpfile is fine. **Severity:**
Negligible.

---

## 6. CORS, Listeners, and Defaults

### 6.1 The CORS/listener combination

```python
# live_inference.py:164-170
self.app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

```python
# live_inference.py:1231
uvicorn.run(server.app, host="0.0.0.0", port=port)

# unified_server.py:414-417
config = uvicorn.Config(
    app=self.inference_server.app,
    host="0.0.0.0",
    port=self.inference_port,
    log_level="warning",
)
```

`allow_origins=["*"]` with `allow_credentials=True` is an invalid CORS
combo per Fetch (browsers reject it for cross-origin credentialed
requests). Today this is moot: no HTTP routes; WS upgrade doesn't
preflight, so browsers can connect from any origin regardless. The
CORS misconfig is cosmetic — but signals "no origin policy" and
becomes real the moment an HTTP route is added.

The `host="0.0.0.0"` bind is the operative problem: the WS is
reachable from every interface. Combined with §2.1 (no auth) and
§4.1 (checkpoint RCE), this is the primary deployment-misconfig
failure mode.

Safe-when: single-user box, firewall, NAT, laptop without
public-facing IFs. Unsafe-when: multi-user box, classroom
workstation, cloud instance with public IP. One-line remediations
(§9).

### 6.2 The CWD-relative log

`self._qvalue_log_path = Path("qvalues_inference.log")`
(`live_inference.py:157`). Confidentiality: low (RL Q-values are not
sensitive). Integrity: `open("w")` truncates on each server start —
symlink-attack class on shared hosts; under systemd the CWD is the
project root, so the file lands in a user-owned directory. Practical
only on shared dev hosts. Availability: no rotation; grows unbounded
over a multi-day demo (which is what the unit is named for).
**Severity:** Low.

### 6.3 Frontend Vite dev server

`vite.config.js` binds `0.0.0.0:5173` with no proxy (SG8). Same caveat
as §6.1; not part of the Python listener but documented in the README.

---

## 7. Supply Chain

### 7.1 Pyproject dependency shape

From `pyproject.toml:39-67`:

| Dep | Pin | Notes |
|---|---|---|
| `pettingzoo` | `>=1.24.0` | Open-ended. |
| `gymnasium` | `>=1.0.0` | Open-ended. |
| `numpy` | `>=1.24.0` | Open-ended. |
| `torch` | `>=2.9.0,<2.12` | **Upper-pinned** (comment cites triton 3.7 segfault `filigree hamlet-74197422b3`). |
| `fastapi` | `>=0.100.0` | Open-ended. |
| `uvicorn[standard]` | `>=0.23.0` | Open-ended. |
| `websockets` | `>=11.0` | Open-ended. |
| `flask` | `>=3.0.0` | **Declared but not imported** (SG8 §C concerns #2, confirmed: `grep -rn 'flask\|Flask(' src/` returns nothing). Pure dead weight. |
| `flask-cors` | `>=4.0.0` | Same — unused. |
| `cloudpickle` | `>=3.0.0` | **Declared but not imported in `src/` (grep returns no hits).** Only `import pickle` in `checkpoint_utils.py:7`. |
| `tensorflow[and-cuda]` | `>=2.20.0` | Plus duplicate `tensorflow>=2.20.0` on the next line. Used (if at all) only for tensorboard logging — likely unnecessary CUDA-coupling, per catalog §11.6. |
| `mlflow` | `>=2.9.0` | Heavy dep; check actually-used. |
| `gitpython` | `>=3.1.0` | The compiler uses `subprocess` for `git rev-parse`, not `gitpython` (`compiler.py:702`). Possibly unused. |
| `msgpack` | `>=1.1.2` (top-level) + `>=1.0.0` (recording extra) | Duplicate declaration. |
| `lz4` | `>=4.4.5` + `>=4.0.0` | Duplicate declaration. |

Two security-relevant points:

1. **`torch<2.12` upper pin** is a deliberate triton-segfault
   workaround. Blocks future security patches in the 2.12+ line.
   Revisit every release; track unpin when triton 3.8 lands.
2. **`flask`, `flask-cors`, `cloudpickle`, `gitpython` are
   dead-weight declarations** (no `src/` imports). Each contributes
   nothing at runtime and adds attack surface in a compromised-mirror
   scenario. Fix: `uv remove flask flask-cors cloudpickle gitpython`
   plus dedupe the `msgpack`/`lz4` lines.

### 7.2 CI / pre-commit

Not inspected in this pass. `config-validation.yml` exists per
catalog §11. Narrow follow-up: confirm CI does not load checkpoints
from untrusted PRs (checking out a PR branch and running tests is
fine; loading a `.pt` file the PR adds is the failure mode).

### 7.3 Repo-root debris

Spot-check of `/home/john/hamlet/`:

| File | Findings |
|---|---|
| `.coverage` (405 KB) | Coverage SQLite; leaks dev paths. `.gitignore` it (catalog §12). Not a credential leak. |
| `qvalues_inference.log` (0 B) | CWD-relative inference log (§6.2). |
| `DEPENDENCY_ANALYSIS_REPORT.txt` / `_SUMMARY.md` | Plaintext dependency tables, no secrets. Should live under `docs/`. |
| `.mcp.json` (161 B) | filigree MCP config, not a secret store. |

No `.env`, `secrets.yml`, `*.pem`, `*.key`, `id_rsa`, or
`credentials.*` files at repo root. **Severity:** Negligible.

---

## 8. Findings Table

Sorted by Severity (Critical → Low). All `Likelihood` and `Impact`
ratings are in the localhost-deployment posture *unless* the surface
explicitly leaks beyond localhost.

| ID | Finding | Severity | Likelihood | Impact | Surface | Recommendation |
|---|---|---|---|---|---|---|
| SEC-01 | Checkpoint loading still uses `weights_only=False` (pickle RCE); digest verification is now required but same-directory | **High residual** | Medium (supply-chain / shared cluster) | High (RCE as service user) | `checkpoint_utils.py:220`, `live_inference.py:444`, `runner.py:185,342` | Short-term digest requirement is done. Migrate the non-tensor state out of pickle into msgpack/JSON so `weights_only=True` works. Long-term: sign checkpoints with a key kept outside the run dir. |
| SEC-02 | uvicorn binds `0.0.0.0` with no auth, no rate limit | **High if exposed / Low on localhost** | High (operator mistake on shared host) | High when exposed | `live_inference.py:1231`, `unified_server.py:416` | Default `host="127.0.0.1"`. Add a CLI flag `--bind 0.0.0.0` for explicit opt-in. |
| SEC-03 | systemd unit lacks hardening directives; runs as operator user | Medium | High (default install) | Medium (full operator-user blast radius) | `deploy/townlet-demo.service` | Add `NoNewPrivileges`, `ProtectSystem=strict`, `ProtectHome=read-only` or `tmpfs`, `PrivateTmp`, `RestrictAddressFamilies`, `MemoryMax`, `TasksMax`. |
| SEC-04 | systemd unit invokes `townlet.demo.runner` (no WS) but operators likely want unified server; switching to unified silently exposes `0.0.0.0:8766` | Medium | High (anyone wanting the demo) | Medium | `deploy/townlet-demo.service:9` | Decide what the unit is for; if it's the unified server, change `ExecStart` and add a bind-host argument; if it's training-only, remove `network.target` from `After=` and document. |
| SEC-05 | `set_speed` divides by attacker-controlled value with no validation (DoS) | Medium | High if exposed | Low (single-connection DoS / CPU pin) | `live_inference.py:626-627` | Validate `0 < speed <= max_speed`; reject otherwise. |
| SEC-06 | `list_recordings` accepts unbounded `limit` from the client | Low | Medium | Low | `live_inference.py:1029-1038` | Clamp `limit` server-side (e.g. `min(limit, 1000)`). |
| SEC-07 | CORS `allow_origins=["*"]` + `allow_credentials=True` is an invalid combination; signals "no origin policy" | Low | Low (no HTTP routes today) | Low today; High the moment a route is added | `live_inference.py:164-170` | If kept, set `allow_origins=["http://localhost:5173"]` and `allow_credentials=False`. |
| SEC-08 | `qvalues_inference.log` is CWD-relative, unrotated | Low | High | Low | `live_inference.py:157` | Move under `<run_root>/qvalues_inference.log`; add size-based rotation. |
| SEC-09 | Frontend Vite dev server binds `0.0.0.0:5173` | Low | Medium (default Vite) | Low | `frontend/vite.config.js:5-11` | Default to `host: '127.0.0.1'` in `vite.config.js`. |
| SEC-10 | `cloudpickle`, `flask`, `flask-cors`, `gitpython` declared but unused; supply-chain bloat | Low | Low (mirror compromise) | Low | `pyproject.toml:48-49,58,60` | Remove. Also dedupe `msgpack` and `lz4` lines. |
| SEC-11 | `torch<2.12` upper pin blocks future security patches in 2.12+ | Low | Medium (over time) | Low | `pyproject.toml:45` | Track via filigree; unpin when triton 3.8 lands and the segfault is resolved. |
| SEC-12 | Checkpoint digest is co-located with checkpoint; an attacker who can write one can write the other | Low | Low | Low (mitigation is cosmetic anyway) | `checkpoint_utils.py:150-167` | Out of scope for this project tier; note in SECURITY.md that digests are integrity, not authenticity. |
| SEC-13 | World expression DSL is closed-grammar but has no depth/size bounds | Low | Low | Low (DoS) | `world/expression/parser.py`, `evaluator.py` | Add max-depth + max-tensor-size guards if and when configs become operator-uploadable. |
| SEC-14 | `.coverage` SQLite committed at repo root; leaks dev paths | Negligible | n/a | Negligible | `/.coverage` | `.gitignore` it. |
| SEC-15 | Config snapshot copies the whole config pack into the run dir; will silently include any future secrets | Negligible (today) | Low | Medium (forward-looking) | `unified_server.py:97-113` | Document the policy in `SECURITY.md`: config packs MUST NOT contain secrets. |

---

## 9. Recommendations

Ordered for "if this were ever deployed beyond localhost, what must
change first?" Effort estimates are in engineer-hours.

### Phase 1 — Pre-deployment must-fix (≤ 1 engineer-day total)

1. **Bind to `127.0.0.1` by default** (SEC-02). One-line change in
   `live_inference.py:1231` and `unified_server.py:416`. Add a
   `--bind` CLI flag. **Effort: 30 min.**
   *Confidence: High. Risk of regression: Negligible (the frontend
   dev server hits `localhost`).*
2. **Validate `set_speed` and `list_recordings.limit`** (SEC-05,
   SEC-06). Two short input checks. **Effort: 30 min.**
   *Confidence: High.*
3. **Tighten CORS** (SEC-07). Set `allow_origins=
   ["http://localhost:5173"]` and `allow_credentials=False`. **Effort:
   10 min.** *Confidence: High (frontend is the only legitimate
   origin).*
4. **Harden the systemd unit** (SEC-03). Add the standard hardening
   block. **Effort: 1–2 hours including a smoke test that training and
   the WebSocket still work under the restrictions.** *Confidence:
   Medium — `SystemCallFilter=@system-service` may need tuning for
   torch/CUDA.*
5. **Decide what `townlet-demo.service` is for** (SEC-04). Either point
   it at `run_demo.py` (with `--bind 127.0.0.1`) or strip the
   `network.target` dependency and document it as training-only.
   **Effort: 30 min decision + 15 min change.**

### Phase 2 — Within-the-month hygiene (≤ 1 engineer-day)

6. **Checkpoint digests required** (SEC-01 first step) — done in code.
   `live_inference.py` and the runner load sites now require `.sha256`
   sidecars before `weights_only=False` loading. Regenerate any existing
   checkpoints missing the sidecar. Residual risk remains for malicious
   checkpoints with matching same-directory digests; see SEC-01.
7. **Move `qvalues_inference.log` under the run directory** (SEC-08).
   Already noted by SG8. **Effort: 15 min.**
8. **Remove dead deps** (SEC-10): `flask`, `flask-cors`, `cloudpickle`
   (no `src/` imports), `gitpython` (compiler uses `subprocess`).
   Dedupe `msgpack`/`lz4` declarations. **Effort: 15 min** + a CI run
   to confirm nothing screams.
9. **Bind Vite to `127.0.0.1` by default** (SEC-09). **Effort: 5 min.**
10. **Add `.coverage` to `.gitignore`** (SEC-14). **Effort: 1 min.**

### Phase 3 — Longer-term, if the project ever ships a "demo for strangers"

11. **Replace pickle-in-checkpoint with msgpack-or-JSON for non-tensor
    state** (SEC-01 root cause). The non-tensor things in the
    checkpoint are: curriculum state, exploration internals (epsilon,
    RND optimizer state), replay buffer metadata, brain config dict.
    Most can be `dict[str, Any]` → JSON. The replay buffer requires
    tensor handling (already torch-native). Goal: every callsite of
    `safe_torch_load` can pass `weights_only=True`. **Effort: 2–3 days
    given existing tests.** *Confidence: Medium. Worth a design pass
    first.*
12. **Authenticate the WebSocket** (SEC-02 root cause). A bearer token
    from a local file (`~/.config/townlet/auth-token`) is enough for
    the project's actual threat model — it stops a curious browser on
    the LAN but doesn't pretend to be SSO. **Effort: 1 day including
    a frontend change.** *Confidence: Medium; the frontend would need
    to read the token from a localStorage entry the operator pastes
    in.*
13. **Sign checkpoints** (SEC-01 / SEC-12). HMAC with an out-of-tree
    key. Useful only if the project genuinely distributes checkpoints
    between hosts. **Effort: 2 days.** *Confidence: Low value at
    current project tier.*
14. **Add a `SECURITY.md` clause stating "config packs MUST NOT
    contain secrets"** (SEC-15). **Effort: 10 min.**

### Phase 4 — Out of scope

- TLS termination, mTLS, RBAC, audit logging: this project is not in
  the regime where these add value.
- Sandboxing the DSL evaluator: the DSL is closed-grammar; the cost
  of sandboxing exceeds the benefit.

---

## Confidence Assessment

- **Inbound surface inventory (§2):** **High.** I read the only two
  inbound files end-to-end; FastAPI's decorator surface is fully
  enumerated.
- **STRIDE per surface (§3):** **High** for Spoofing, Tampering, DoS,
  EoP; **Medium** for Information Disclosure (I did not exhaustively
  enumerate every server→client frame, but I checked the dispatch sites
  and confirmed no path data, env vars, or stack traces leak).
- **Code execution surface (§4):** **High.** Grep of `eval`/`exec`/
  `compile`/`yaml.load`/`pickle` across `src/townlet/` and `scripts/`
  is exhaustive; the only RCE-class finding is the
  `weights_only=False` checkpoint path, which is unambiguous.
- **Deployment posture (§5):** **High** on what the unit does and
  doesn't do; **Medium** on the operator's intended use (the unit's
  ExecStart and the project's documented "demo" workflow disagree —
  SEC-04).
- **CORS / listener defaults (§6):** **High.**
- **Supply chain (§7):** **Medium.** I read `pyproject.toml` and
  spot-checked imports for `flask`/`cloudpickle`/`gitpython`; I did not
  run `pip-audit` or `safety` against the lockfile (no `uv.lock`
  inspected). A vulnerability sweep is a separate exercise.
- **Findings table (§8) and recommendations (§9):** **High** on
  identification, **Medium** on severity ratings (the localhost-vs-
  exposed dichotomy is real and I have flagged it; reasonable people
  could move SEC-02 between Low and High depending on how strict they
  are about default postures).

## Risk Assessment

| Recommendation block | Risk of recommending | Risk of not recommending |
|---|---|---|
| Phase 1 (bind/CORS/validate/hardening) | Negligible (all reversible, all small) | Medium — accumulates as "ready to expose" technical debt. |
| Phase 2 (digests required, dead deps, paths) | Low — small breaking changes; pre-release policy supports them. | Low to Medium — slow accumulation of supply-chain risk and dev-host clutter. |
| Phase 3 (msgpack checkpoints, auth, signing) | Medium — non-trivial refactor; signing in particular is overkill if the project doesn't actually distribute checkpoints. | Low today, Medium-High if the project ever ships a public demo. |

## Information Gaps

- I did not inspect `.github/workflows/` or `.pre-commit-config.yaml`
  for CI security posture (PR-checkout-then-load-checkpoint patterns
  are the failure mode). Recommend a separate pass over
  `.github/workflows/*.yml`.
- I did not run an automated dependency vulnerability scan
  (`pip-audit`, `safety check`). The findings about `torch<2.12` and
  the dead deps are static-analysis-based.
- I did not verify whether the project has a `frontend/package.json`
  (per SG8 §C concern #1, it is absent from the tree). If the frontend
  build is broken at the file level the practical exposure of the Vite
  `0.0.0.0` bind is zero.
- I did not enumerate every Server→client frame for accidental
  PII/path leakage; I confirmed the high-traffic paths
  (`connected`, `state_update`, `episode_*`) are clean. A future pass
  could grep `_broadcast_to_clients` callsites exhaustively.
- I did not assess the recording msgpack/LZ4 deserialization for
  malformed-input handling (`replay.py`). msgpack is a binary format
  with a long history of bounded-input deserializers; the risk is low
  but I did not verify.

## Caveats

- This is a **pedagogical RL framework, not a service**. Recommendations
  here are scoped accordingly. I have deliberately not invoked OWASP
  ASVS or NIST controls — those would be security theatre at this
  project tier.
- Everything in this document assumes the operator is benign and the
  attacker is one of: a tampered artifact, a curious browser on the
  LAN, or a future-self who forgets that `0.0.0.0` means "everywhere."
- The `weights_only=False` finding (SEC-01) is the only finding that
  rises to "real CVE-class issue" *in a realistic threat model*
  (distributed checkpoints). It is also the only finding whose
  remediation has non-trivial engineering cost. Everything else is one
  line of code or one line of config.

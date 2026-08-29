# HAMLET/Townlet Architecture Diagrams

> ✅ **Recovered from archive 2026-08-26 — the three diagrams below were re-verified against
> source on that date.** Every module path named as a node in `c2_component_diagram.mmd`
> resolves to a live file in `src/townlet/`, and the external integrations in
> `c1_system_context.mmd` (WebSocket `:8766`, Vue frontend `:5173`, TensorBoard `:6006`,
> SQLite `metrics.db`, `checkpoints/*.pt`) all match the shipped system.
>
> **What is NOT here:** the companion `ARCHITECTURE_REPORT.md` (2025-11-12) was **left in the
> archive** at `docs/zzz. archive/diagrams/ARCHITECTURE_REPORT.md`. It predates VFS, the
> oracle, `items/` and `effects/`, and it is superseded by the six-document HLD set in
> `docs/architecture/`. This README no longer routes you to it.
>
> These are **structural** diagrams — boxes and edges. They are accurate about *what talks to
> what*. They carry no dimension counts, action counts, or status claims, which is why they
> aged well. For behaviour and current status, use `README.md` and `docs/architecture/`.

C4-style diagrams of the HAMLET/Townlet system, at three levels of zoom.

## Files

| Diagram | Level | Shows |
|---|---|---|
| `c1_system_context.mmd` | C1 — System Context | The system as one box: operators, filesystem, SQLite, WebSocket, TensorBoard, the Vue frontend |
| `c2_component_diagram.mmd` | C2 — Components | Inside `src/townlet/`: cold path (config → compilation) vs hot path (training execution), plus persistence and visualization |
| `c3_dependency_graph.mmd` | C3 — Module Dependencies | Module-level import relationships, entry points, compilation pipeline, runtime flow |

The C2 split between **cold path** (configuration parsed and compiled once into a frozen
`CompiledUniverse`) and **hot path** (GPU-native tensor execution) is the single most useful
thing in this directory, and it is still how the system is organised.

## Viewing

**VS Code** — install [Markdown Preview Mermaid Support](https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid):

```bash
code --install-extension bierner.markdown-mermaid
```

**Mermaid CLI** — render to an image:

```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i c1_system_context.mmd -o c1_system_context.svg -b transparent
```

**Mermaid Live Editor** — paste the contents of any `.mmd` file into <https://mermaid.live>.

**GitHub** renders Mermaid inline in markdown, but these are bare `.mmd` files; wrap the
contents in a ```` ```mermaid ```` fence to preview one in a markdown document.

## Provenance

Generated 2025-11-12 by autonomous codebase analysis at commit `f9b5752` (branch
`004a-compiler-implementation`), from a scan of the `src/` tree rather than from documentation.
Node paths re-verified against `src/townlet/` on 2026-08-26.

If the architecture moves, these need regenerating — they are hand-checkable, so the cheap
maintenance step is to re-run the node-path check rather than to redraw.

## Related

- `README.md` (repo root) — current and honest about status; prefer it over anything here for behaviour
- `docs/architecture/` — the six-document HLD set (`HLD`, `STRATA`, `UAC`, `BAC`, `COMPILER`, `VFS`)
- `docs/architecture/COMPILER.md` — the seven-stage compilation pipeline the C3 graph traces
- `docs/config-schemas/` — per-surface configuration schemas
- `CLAUDE.md` — development commands and quick reference

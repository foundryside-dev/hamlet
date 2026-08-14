---
name: live-inference
description: Use when starting the HAMLET live-visualization stack — the townlet inference server plus the Vue frontend — to watch trained agents run from checkpoints in a browser.
---

# Live Inference (Visualization)

Two processes, two terminals.

## Terminal 1 — inference server

Run from a directory containing checkpoints:

```bash
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
python -m townlet.demo.live_inference <checkpoint_dir> 8766 0.2 10000 <config_path>
# Args (positional): checkpoint_dir, port, speed, total_episodes, config_path
```

The server broadcasts state over WebSocket on `localhost:8766`.

## Terminal 2 — frontend

```bash
cd frontend && npm run dev
```

Open http://localhost:5173. The frontend connects to the WebSocket on mount.

## Notes

- Checkpoints must match the config pack's `drive_hash` — a checkpoint trained under a
  different `drive.yaml` will be rejected.
- Rendering mode is substrate-specific (see `frontend/CLAUDE.md`): spatial grids render in
  `Grid.vue`; aspatial universes get the meters-only `AspatialView.vue`.
